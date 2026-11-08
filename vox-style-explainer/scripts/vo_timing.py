#!/usr/bin/env python3
"""Turn a voiceover + beat sheet into src/timing.json for vox-style-explainer.

The narration is the timeline. This script derives every scene boundary and every
in-scene payoff frame from where words actually fall in the audio, so nothing
downstream is typed by hand.

    python vo_timing.py voiceover.mp3 --beat-sheet beat-sheet.csv --words words.json
    python vo_timing.py voiceover.mp3 --beat-sheet beat-sheet.csv --whisper groq
    python vo_timing.py voiceover.mp3 --beat-sheet beat-sheet.csv --estimate

Emits, per scene: `from`, `durationInFrames`, and the ABSOLUTE `beatFrame`.
MasterSequence converts that to scene-local with `s.beatFrame - s.from`, because
<Series.Sequence> resets useCurrentFrame() to 0.

Requires ffprobe on PATH. No third-party packages.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_LEAD_IN = 10  # frames; see references/vo-sync.md
SENTENCE_PAUSE = 0.32  # seconds of breath between beats, used by --estimate only
MATCH_WINDOW = 14  # words to scan ahead when aligning a line to the transcript

# A key that is merely PRESENT is not a key that WORKS. This machine has shipped an
# 8-char `sk-12345` placeholder in the Windows User environment that shadows blank
# config files, so reject obvious placeholders before spending a request.
PLACEHOLDER_KEYS = {"sk-12345", "sk-xxx", "changeme", "your-api-key", "none", "null"}

VOWEL_RUN = re.compile(r"[aeiouy]+")


def syllables(word: str) -> float:
    """Rough syllable count, used only to weight --estimate durations."""
    w = word.lower()
    digits = sum(ch.isdigit() for ch in w)
    letters = re.sub(r"[^a-z]", "", w)
    if not letters:
        # Pure number or symbol: each digit is about one syllable, and long numbers
        # gain a "hundred"/"thousand" word or two.
        return max(1.0, digits * 1.0 + (1.0 if digits >= 3 else 0.0))
    n = len(VOWEL_RUN.findall(letters))
    if letters.endswith("e") and n > 1 and not letters.endswith(("le", "ee", "ye")):
        n -= 1
    return max(1.0, float(n)) + digits


def norm(token: str) -> str:
    """Normalise for matching: keep letters, digits and $ so `$116` survives."""
    return re.sub(r"[^a-z0-9$]", "", token.lower())


def tokens_of(text: str) -> list[str]:
    out = [norm(t) for t in text.split()]
    return [t for t in out if t]


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    sys.exit("vo_timing: " + msg)


def load_beat_sheet(path: Path) -> list[dict]:
    """Read the beat sheet. Format is detected from the extension."""
    if not path.exists():
        die(f"beat sheet not found: {path}")

    if path.suffix.lower() == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else raw.get("scenes") or raw.get("beats") or []
    else:
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))

    beats: list[dict] = []
    for i, r in enumerate(rows):
        rid = str(r.get("id") or "").strip()
        line = str(r.get("vo_line") or "").strip()
        if not rid and not line:
            continue  # tolerate trailing blank CSV rows
        if not rid:
            die(f"row {i + 1} has no id")
        if rid.upper().startswith("EXAMPLE-"):
            die(
                f"row {i + 1} is still the shipped template ({rid!r}). Replace the "
                "EXAMPLE- rows in beat-sheet.template.csv with the real script."
            )
        if not line:
            die(f"{rid}: vo_line is empty - every beat needs its narration sentence")

        mid = r.get("midground_asset") or ""
        if isinstance(mid, str):
            mid = [m.strip() for m in mid.split(";") if m.strip()]

        beat_word = str(r.get("beat_word") or "").strip()
        if beat_word and norm(beat_word) not in tokens_of(line):
            die(
                f"{rid}: beat_word {beat_word!r} does not occur in vo_line. Fix the "
                "spelling to match the narration exactly, including $ and digits."
            )

        beats.append(
            {
                "id": rid,
                "vo_line": line,
                "midground_asset": mid,
                "foreground_asset": (r.get("foreground_asset") or "").strip() or None,
                "transition_out": (r.get("transition_out") or "hard-cut").strip(),
                "beat_word": beat_word,
            }
        )

    if not beats:
        die("beat sheet has no usable rows")
    return beats


def load_words(path: Path) -> list[dict]:
    """Normalise any of four common alignment formats to [{word, start, end}]."""
    raw = json.loads(path.read_text(encoding="utf-8"))

    # 1. already normalised: {"words": [...]} or a bare list
    seq = raw.get("words") if isinstance(raw, dict) else raw
    # 2. Whisper verbose_json: words nested under segments
    if seq is None and isinstance(raw, dict) and isinstance(raw.get("segments"), list):
        seq = [w for s in raw["segments"] for w in (s.get("words") or [])]
    # 3. ElevenLabs character alignment -> collapse runs between spaces into words
    if seq is None and isinstance(raw, dict):
        al = raw.get("alignment") or raw.get("normalized_alignment") or raw
        chars = al.get("characters")
        starts = al.get("character_start_times_seconds")
        ends = al.get("character_end_times_seconds")
        if chars and starts and ends:
            seq, buf, bs = [], "", None
            for ch, cs, ce in zip(chars, starts, ends):
                if ch.isspace():
                    if buf:
                        seq.append({"word": buf, "start": bs, "end": prev_end})
                        buf, bs = "", None
                    continue
                if not buf:
                    bs = cs
                buf += ch
                prev_end = ce
            if buf:
                seq.append({"word": buf, "start": bs, "end": prev_end})

    if not seq:
        die(f"{path}: could not find word timings in this file")

    words = []
    for w in seq:
        text = w.get("word", w.get("text", ""))
        if not norm(str(text)):
            continue
        try:
            words.append(
                {"word": str(text).strip(), "start": float(w["start"]), "end": float(w["end"])}
            )
        except (KeyError, TypeError, ValueError):
            die(f"{path}: entry {w!r} is missing numeric start/end")

    if not words:
        die(f"{path}: zero usable words after normalisation")
    words.sort(key=lambda w: w["start"])
    return words


def ffprobe_duration(audio: Path) -> float:
    """Real audio duration in seconds. Args are a list, never a shell string -
    Git Bash mangles Windows paths inside interpolated commands."""
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=nokey=1:noprint_wrappers=1", str(audio),
            ],
            capture_output=True, text=True, check=True, timeout=60,
        ).stdout.strip()
        return float(out)
    except FileNotFoundError:
        die("ffprobe not found on PATH - install ffmpeg")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        die(f"ffprobe failed on {audio}: {e}")
    except ValueError:
        die(f"ffprobe returned no duration for {audio} - is it really audio?")


def transcribe(audio: Path, provider: str) -> list[dict]:
    """Word-level transcription via Groq or OpenAI. Needs a WORKING key."""
    import urllib.error
    import urllib.request

    cfg = {
        "groq": ("GROQ_API_KEY", "https://api.groq.com/openai/v1/audio/transcriptions",
                 "whisper-large-v3"),
        "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1/audio/transcriptions",
                   "whisper-1"),
    }[provider]
    env_name, url, model = cfg
    key = (os.environ.get(env_name) or "").strip()
    if not key:
        die(f"{env_name} is not set - use --words or --estimate instead")
    if key.lower() in PLACEHOLDER_KEYS or len(key) < 20:
        die(
            f"{env_name} looks like a placeholder ({len(key)} chars). Check the process "
            "environment, not just the config file - an inherited var wins. "
            "Use --estimate to proceed without a key."
        )

    boundary = "----vo-timing-boundary"
    parts: list[bytes] = []

    def field(name: str, value: str) -> None:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode()
        )

    field("model", model)
    field("response_format", "verbose_json")
    field("timestamp_granularities[]", "word")
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
        f'filename="{audio.name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
    )
    parts.append(audio.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            raw = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:300]
        die(f"{provider} transcription failed: HTTP {e.code} {detail}")
    except Exception as e:  # noqa: BLE001
        die(f"{provider} transcription failed: {e!r}")

    tmp = audio.with_suffix(".words.json")
    tmp.write_text(json.dumps(raw), encoding="utf-8")
    print(f"  transcript cached -> {tmp}")
    return load_words(tmp)


def align(beats: list[dict], words: list[dict]) -> None:
    """Greedy sequential alignment of each vo_line onto the transcript word stream.

    Tolerant by design: TTS elides, contracts and re-punctuates, so an expected token
    that cannot be found nearby is skipped rather than treated as a failure. Records
    first/last matched word index per beat, plus the index of its beat_word.
    """
    cursor = 0
    for b in beats:
        expected = tokens_of(b["vo_line"])
        first = last = None
        hits: list[int] = []

        for tok in expected:
            probe = cursor
            limit = min(len(words), cursor + MATCH_WINDOW)
            while probe < limit and norm(words[probe]["word"]) != tok:
                probe += 1
            if probe < limit:
                if first is None:
                    first = probe
                last = probe
                hits.append(probe)
                cursor = probe + 1

        if first is None:
            die(
                f"{b['id']}: could not locate any of this line's words in the transcript. "
                "The audio and the beat sheet are probably out of order, or the VO was "
                "re-recorded without regenerating the beat sheet."
            )
        b["_first"] = first
        b["_last"] = last

        b["_beat_idx"] = None
        if b["beat_word"]:
            target = norm(b["beat_word"])
            for idx in hits:
                if norm(words[idx]["word"]) == target:
                    b["_beat_idx"] = idx
                    break

    matched = sum(1 for b in beats if b["_beat_idx"] is not None)
    print(f"  aligned {len(beats)} beats; {matched} beat_word(s) located exactly")


def synth_words(beats: list[dict], duration: float) -> list[dict]:
    """--estimate: distribute real audio duration across lines by syllable weight."""
    per_beat = [[(w, syllables(w)) for w in b["vo_line"].split()] for b in beats]
    total_syl = sum(s for line in per_beat for _, s in line)
    pauses = SENTENCE_PAUSE * max(0, len(beats) - 1)
    speech = max(0.1, duration - pauses)
    sec_per_syl = speech / total_syl if total_syl else 0.0

    words: list[dict] = []
    t = 0.0
    for i, line in enumerate(per_beat):
        for w, s in line:
            dur = s * sec_per_syl
            words.append({"word": w, "start": round(t, 3), "end": round(t + dur, 3)})
            t += dur
        if i < len(beats) - 1:
            t += SENTENCE_PAUSE
    return words


def build(beats: list[dict], words: list[dict], fps: int, lead_in: int,
          duration: float, method: str, audio: Path) -> dict:
    """Absolute timestamps -> frames. Never sum durations; drift accumulates."""
    total_frames = max(1, round(duration * fps))

    # Scene N starts lead_in frames before its first spoken word, so the pop spring
    # has arrived by the moment the subject is named. Scene 1 cannot start negative.
    starts = [max(0, round(words[b["_first"]]["start"] * fps) - lead_in) for b in beats]
    starts[0] = 0
    for i in range(1, len(starts)):
        if starts[i] <= starts[i - 1]:
            starts[i] = starts[i - 1] + 1  # keep <Series> strictly increasing

    scenes = []
    for i, b in enumerate(beats):
        start = starts[i]
        end = starts[i + 1] if i + 1 < len(starts) else total_frames
        dur = max(1, end - start)

        if b["_beat_idx"] is not None:
            beat_frame = round(words[b["_beat_idx"]]["start"] * fps)
            confidence = "exact" if method != "estimate" else "interpolated"
        else:
            # No beat_word, or it never matched: centre the payoff in the scene and
            # say so, rather than silently pretending it was timed.
            beat_frame = start + dur // 2
            confidence = "centred"
        beat_frame = min(max(beat_frame, start), start + dur - 1)

        scenes.append(
            {
                "id": b["id"],
                "voLine": b["vo_line"],
                "beatWord": b["beat_word"] or None,
                "transitionOut": b["transition_out"],
                "midgroundAsset": b["midground_asset"],
                "foregroundAsset": b["foreground_asset"],
                "from": start,
                "durationInFrames": dur,
                "beatFrame": beat_frame,
                "localBeatFrame": beat_frame - start,
                "beatConfidence": confidence,
            }
        )

    covered = sum(s["durationInFrames"] for s in scenes)
    assert covered == total_frames, f"scene frames {covered} != total {total_frames}"

    return {
        "method": method,
        "fps": fps,
        "leadIn": lead_in,
        "audio": audio.name,
        "audioDuration": round(duration, 3),
        "totalFrames": total_frames,
        "scenes": scenes,
    }


def main() -> int:
    p = argparse.ArgumentParser(
        description="Derive src/timing.json from a voiceover and a beat sheet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("audio", type=Path, help="the voiceover file (mp3/wav/m4a)")
    p.add_argument("--beat-sheet", type=Path, required=True, help="beat-sheet.csv or beats.json")
    p.add_argument("--fps", type=int, default=30)
    p.add_argument("--out", type=Path, default=Path("src/timing.json"))
    p.add_argument("--lead-in", type=int, default=DEFAULT_LEAD_IN,
                   help="frames a scene starts before its first word")

    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--words", type=Path, help="existing word timestamps (most accurate)")
    src.add_argument("--whisper", choices=("groq", "openai"), help="transcribe (needs a key)")
    src.add_argument("--estimate", action="store_true", help="syllable-weighted, no key")

    a = p.parse_args()
    if not a.audio.exists():
        die(f"audio not found: {a.audio}")
    if a.fps < 1:
        p.error("--fps must be >= 1")

    beats = load_beat_sheet(a.beat_sheet)
    print(f"{a.beat_sheet}: {len(beats)} beats")

    duration = ffprobe_duration(a.audio)
    print(f"{a.audio}: {duration:.3f}s ({round(duration * a.fps)} frames @ {a.fps}fps)")

    if a.words:
        words, method = load_words(a.words), "words"
    elif a.whisper:
        words, method = transcribe(a.audio, a.whisper), f"whisper:{a.whisper}"
    else:
        words, method = synth_words(beats, duration), "estimate"
    print(f"  method={method}, {len(words)} words")

    align(beats, words)
    timing = build(beats, words, a.fps, a.lead_in, duration, method, a.audio)

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(timing, indent=2) + "\n", encoding="utf-8")
    print(f"\nwrote {a.out}")

    for s in timing["scenes"]:
        flag = "" if s["beatConfidence"] == "exact" else f"  <-- {s['beatConfidence']}"
        print(
            f"  {s['id']:<28} from={s['from']:>5} dur={s['durationInFrames']:>4} "
            f"beat={s['beatFrame']:>5} (local {s['localBeatFrame']:>4}){flag}"
        )

    if method == "estimate":
        print(
            "\nNOTE: --estimate distributes the real audio duration by syllable count.\n"
            "Scene boundaries land within a few frames; individual beat frames are\n"
            "interpolated inside their line and can be further off. Render the beat\n"
            "frames as stills before shipping, and say plainly that timing was estimated."
        )
    weak = [s["id"] for s in timing["scenes"] if s["beatConfidence"] == "centred"]
    if weak:
        print(f"\nWARNING: no beat_word landed for: {', '.join(weak)} - payoffs centred instead.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

