# Voiceover sync

The narration is the timeline. Every scene boundary and every in-scene payoff derives from where words actually fall in the audio, not from durations anyone chose.

## Frame math

```
frame = round(seconds * fps)
```

At 30 fps one frame is 33 ms — well below the ~80 ms threshold where a mistimed visual starts to feel wrong. So rounding is safe, but **accumulation is not**: always derive each boundary from an absolute timestamp. Summing per-scene durations drifts by a frame or two per scene and the last beat lands visibly late.

## Scene boundaries

Scene *N* runs from its own lead-in to the lead-in of scene *N+1*:

```
scene.from            = firstWordFrame(N) - LEAD_IN
scene.durationInFrames = scene.from(N+1) - scene.from(N)
```

`LEAD_IN` is the important part and the thing most people miss.

**Why the lead-in exists.** The `pop` spring takes roughly 20 frames to settle and reaches ~90% around frame 13. If a scene starts exactly on the word that names its subject, the subject is still flying in as it is spoken — it reads as a beat behind for the entire film. Starting the scene ~10 frames early means the element has arrived by the moment it is named.

```
LEAD_IN = 10   # frames at 30 fps; 8 for tight cuts, 14 for heavy foregrounds
```

The final scene's duration runs to the end of the audio, not to the end of the last word — trailing silence belongs to the scene that owns it, and cutting on the last syllable feels clipped.

## Beat words

`beat_word` from the beat sheet resolves to an absolute frame, then to a scene-local frame for the component:

```
beatFrame        = round(wordStart(beat_word) * fps)
localBeatFrame   = beatFrame - scene.from
```

`<Series.Sequence>` resets `useCurrentFrame()` to 0, so components must receive the **local** value. Passing the absolute frame is the single most common cause of "the counter never fires."

For a counter, the ramp *ends* on `localBeatFrame`. For a chart, the last data point lands there. For a headline, the typewriter finishes there. In all three cases the event completes on the word rather than starting on it.

## Getting word timestamps

Three modes, in order of preference.

### 1. Pre-existing word timestamps (exact, no key) — the path to aim for

If the voice tool returned alignment data, use it. Ask ElevenLabs for the **with-timestamps** response when generating the VO; it costs nothing extra and makes this phase exact.

```bash
python scripts/vo_timing.py voiceover.mp3 --beat-sheet beat-sheet.csv --words words.json
```

`--words` accepts four shapes and normalises them itself — no pre-processing needed. All four are covered by the script's tests and produce identical frame output:

| Source | Shape it arrives in |
|---|---|
| Already normalised | `{"words": [{"word": "Oil", "start": 0.42, "end": 0.61}, ...]}` |
| A bare array | `[{"word": ..., "start": ..., "end": ...}, ...]` |
| Whisper `verbose_json` | `{"segments": [{"words": [...]}, ...]}` |
| ElevenLabs with-timestamps | `{"alignment": {"characters": [...], "character_start_times_seconds": [...], "character_end_times_seconds": [...]}}` — character-level, collapsed to words on whitespace |

### 2. Transcribe with Whisper (exact, needs a working key)

```bash
python scripts/vo_timing.py voiceover.mp3 --beat-sheet beat-sheet.csv --whisper groq
```

Requires `GROQ_API_KEY` or `OPENAI_API_KEY`. A *present* key is not a *working* key: the script rejects anything under 20 characters or matching a known placeholder **before** spending a request, and prints where to look. On this machine that check fires immediately — `OPENAI_API_KEY` is the 8-character `sk-12345` placeholder living in the Windows *User* environment, where it shadows a blank config file, so treat this mode as unavailable here until a real key is set. The transcript is cached beside the audio as `<audio>.words.json`, so a re-run costs nothing.


### 3. Estimate from audio duration (approximate, no key)

```bash
python scripts/vo_timing.py voiceover.mp3 --beat-sheet beat-sheet.csv --estimate
```

Measures the real audio duration with `ffprobe`, then distributes it across lines weighted by syllable count, with a fixed inter-sentence pause. Scene boundaries land within a few frames; individual `beat_word` positions are interpolated within their line and can be off by more.

**Say so when you use this mode.** It is good enough to build and review against, not good enough to ship without checking the beat frames as stills. The generated `timing.json` carries `"method": "estimate"` so the choice stays visible.

## Verifying

For each scene, render the beat frame and look at it:

```bash
npx remotion still MasterSequence out/beat-03.png --frame=<beatFrame>
```

The payoff should be **complete** in that still — number fully counted, chart fully drawn, headline fully typed. If it is mid-motion, the event is starting on the word instead of ending on it.

Then check the two ends: frame 0 should be the first scene fully arrived, and the final frame should not be mid-exit.

## When the voiceover changes

Regenerate; never patch. A re-recorded line shifts every subsequent timestamp, so hand-editing one duration silently breaks everything after it.

```bash
python scripts/vo_timing.py voiceover-v2.mp3 --beat-sheet beat-sheet.csv --words words-v2.json --out src/timing.json
```

Because scene props live in `defaultProps` and only timing lives in `timing.json`, a VO change costs one command and no re-tuning. That separation is the reason phase 7 (Studio tuning) and phase 9 (timing) are kept in different files — do not let a duration leak into a scene component.

## Music

Bed music sits at roughly `volume={0.12}` against a VO at `1.0`, which is about −18 dB. Duck a further 3–4 dB under narration if the track has any midrange content. Foley — a page turn on a paper wipe, a low hit on a hard cut — goes on the cut frame, not the frame after.
