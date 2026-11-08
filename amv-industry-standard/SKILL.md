---
name: amv-industry-standard
version: "1.0.0"
description: Apply the measured edit grammar of Camie's "INDUSTRY STANDARD (AMV ALBUM MIX)" — 20fps gate, single-frame black blinks, 3-frame sustained cutting, and a warm→grey→cool saturation arc — to your own footage and music. Use when asked for an AMV-style, anime-edit, or hard-cut music-video look, or to reproduce that video's style on different material.
argument-hint: "<clips-dir> <audio-file> [section]"
allowed-tools: Bash, Read, Glob
---

# AMV: Industry Standard style

A parameter spec, not a renderer. Every number here was measured from the source video
(1280x720, 20fps, 25128 frames, 20:56) — not estimated by eye. Apply it in ffmpeg,
Premiere, After Effects, Resolve, or a browser canvas; the values transfer.

**Source:** "INDUSTRY STANDARD (AMV ALBUM MIX)" by Camie, `youtu.be/rWQ7tCCGvcM`.

## Copyright boundary — read first

The source mix is built from Camie's copyrighted album audio and copyrighted anime
footage (visible: Bleach, Naruto, a Jujutsu-Kaisen-era digital look, a Lego-animated
segment, VHS-transferred live action). **This skill reproduces the editing grammar, never
the material.** Apply it to footage and music the user owns or has licensed. If asked to
recreate the video itself, say plainly that the assets can't be reproduced and offer this
instead.

## The five things that actually define the look

Ranked by how much each contributes, per measurement:

1. **20fps, everywhere.** Every published format (144p through 1080p) is 20fps, so the
   master is 20fps — not a transcode artifact. This is the single most distinctive choice:
   it reads as deliberate judder, not as low quality. Render at 20fps and quantise every
   cut to a 20fps frame grid (0.05s).
2. **Single-frame black blinks as percussion.** 629 black runs; the median is **1 frame
   long**, and **413 runs are 1-2 frames**. These are not transitions — they're a rhythmic
   instrument, roughly one every 3 seconds. 19% of total runtime (237s) is black.
3. **Three-frame sustained cutting in the peaks.** Median shot is 0.30s; in the 3:00-6:00
   climax the median drops to **0.15s = 3 frames**. 42% of all intervals are ≤3 frames.
4. **A saturation arc, not a fixed grade.** Mean saturation walks 48% → 43% → 40% → 22% →
   **15%** → 30% → 47%: warm and loud, drained to near-monochrome in the middle, then
   recovered. See `references/grades.md`.
5. **Violent luma slams.** 1613 single-frame luma jumps >40/255, i.e. **77 per minute**;
   p99 jump is 134/255. Cut on brightness, not just on subject.

## What the look is NOT — do not add these

Measured absences. Each is a thing an agent would plausibly reach for and would be wrong:

- **No RGB split / chromatic aberration.** Best-fit R→B horizontal shift is **0px in 90 of
  93 sampled frames**. What reads as channel separation is directional motion blur and
  bloom. Adding RGB split makes it look like a different, more generic edit.
- **No uniform cinematic letterbox.** 69% of frames are full-frame 16:9. Bars appear on a
  minority of shots (9% near 2.36:1, 16% with side bars up to 154px) and are **inherited
  from source footage**, not applied globally. Do not stamp 2.39:1 over everything.
- **Only mild grain.** Residual after a 1.5px blur is 2.9/255 median (p90 6.9) — visible
  on the VHS-look shots, near-absent elsewhere. This is source texture plus compression,
  not a heavy grain layer.
- **No reliable global BPM grid.** Best fit is only 44% of cuts at 150 BPM on a 1/16 grid.
  It's a multi-song mix with different tempos. Detect tempo per section; never assume one.

## Files

| File | Contents |
|------|----------|
| `references/effect-stack.md` | Every effect, in order, with measured parameter ranges and the absences above |
| `references/grades.md` | The 7-segment saturation/colour arc with measured mean RGB per segment |
| `references/beat-mapping.md` | Shot-length histogram, cut density per minute, how to place cuts |
| `references/transitions.md` | Black blinks, blackout section breaks, zoom-bursts, whip pans |

## How to apply

1. Read `references/grades.md` and pick the segment whose energy matches the user's track.
2. Read `references/beat-mapping.md` and lay cuts on the detected onsets, quantised to
   0.05s, at the density for that segment.
3. Read `references/effect-stack.md` and apply effects in the listed order.
4. Render 20fps. Check the result against the five defining traits above; if it looks
   smooth, the frame rate or the blink density is wrong.

## Provenance

Measurements came from: `ffprobe` for stream properties; a 32x18 full-decode pass for
per-frame mean colour, spatial std, and luma deltas (`lowres_mean.npy`); ffmpeg
`select='gt(scene,0.30)'` for 1324 cut timestamps; and 93 native-resolution sample frames
for grain, channel alignment, and bar geometry. Re-derive with the commands in
`references/effect-stack.md` if you need to verify a number.
