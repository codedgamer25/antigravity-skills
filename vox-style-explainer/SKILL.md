---
name: vox-style-explainer
description: Build a narrated Vox-style motion-graphics explainer in Remotion — a locked paper background that never cuts, black-and-white halftone cutouts with offset red marker strokes, springy staggered pop-ins, and every visual beat timed to the narrated word. Use for Vox or Johnny Harris style explainers, geopolitical/economic/data explainer videos, newsroom motion graphics, halftone paper-collage animation, script-to-rendered-MP4 pipelines, or voiceover-synced scene sequencing.
---

# Vox-style explainer

Turns a script into a rendered 1080p explainer where a fixed paper background never cuts, halftone cutouts spring in over it, and every visual beat lands on the narrated word.

**Load the `remotion` skill alongside this one.** That skill owns Remotion mechanics — compositions, `<Series>`, `<Audio>`, effects, fonts, `calculateMetadata`. This skill owns art direction and pipeline order. Where the two disagree, this file wins; the disagreements are listed in [Deliberate deviations](#deliberate-deviations).

## Division of labour

Settle this out loud at phase 1 so nobody waits on the other. There is exactly one manual step in the whole pipeline, and it is not the user's job to figure out what to type.

| | |
|---|---|
| **You write the prompts.** | Every `midground_prompt` / `foreground_prompt` in the beat sheet is authored here, derived from that beat's `vo_line`. Never hand the user an empty prompt column or ask them what the picture should be — deciding what illustrates the line is the work. → [references/asset-handoff.md](references/asset-handoff.md) |
| **The user generates the images.** | They paste your prompts into whatever image tool they already pay for (the ChatGPT web app, Midjourney, Magnific, Higgsfield, Gemini), save the PNGs to the paths you gave them, and say when it is done. That is their entire involvement in the asset step. |
| **You do everything else.** | Beat sheet, script, scaffold, validation, halftone, stroke baking, components, choreography, `<Series>`, VO sync, render. |

Hand over **one** block covering every asset in the film, after the beat sheet is confirmed and before writing components. Do not drip-feed prompts scene by scene — the user works in one tab, in one batch.

The reason the prompts live in beat-sheet columns rather than in chat: an asset regenerated three weeks later has to match the ones beside it, and the prompt is the only record of what it was supposed to be.

## The three non-negotiables

Everything else is taste. These three are what make the result read as Vox rather than as generic motion graphics:

1. **The background never cuts.** One paper/grid texture holds for the entire film. Scenes change by swapping what sits *on* it, so the piece feels like one continuous camera instead of a slideshow. This single decision does more for the look than any other.
2. **Three layers, always in this order.** Locked background → **midground** (black-and-white halftone cutout of the subject, with an offset red marker stroke behind it) → **foreground** (a full-colour structure or object that occludes the bottom of the midground and anchors the shot). The colour/halftone split between foreground and midground is deliberate: it creates depth without any 3D.
3. **Motion is springy and staggered, never simultaneous.** Elements pop in one after another with 3–6 frame offsets. Nothing arrives at the same time as its neighbour, and nothing soft-fades in.

Read [references/visual-system.md](references/visual-system.md) before writing any component — it carries the exact tokens, stroke geometry and motion constants.

## Pipeline

Run these in order. Phases 1 and 9 are worth slowing down for; the rest is mechanical once the beat sheet is right.

### 1. Script → beat sheet

Cinematic narration runs ~135 wpm, so budget **~2.2 words per second**: a 45-second film is ~100 words and 6–8 beats. One sentence = one beat = one scene. If the user brought a topic rather than a script, write the script first and get it approved — every duration downstream derives from it.

Copy `assets/beat-sheet.template.csv` to the project root and fill **every** column yourself, prompts included — see [Division of labour](#division-of-labour). Its columns are the contract for the whole build:

`id, vo_line, midground_asset, foreground_asset, midground_prompt, foreground_prompt, transition_out, beat_word`

`beat_word` is the one word in the line a visual must land on — `$116`, `trillion`, `leaving`. Phase 9 keys off it. **Never leave it blank.**

Show the filled table to the user and get it confirmed before scaffolding. A wrong beat sheet costs seconds to fix here and an hour to fix in phase 7. This is also the moment to hand over the asset prompt block, so the user can be generating images while you scaffold. → [references/beat-sheet.md](references/beat-sheet.md)

### 2. Lock the visual system

One background for the film, one accent colour, two typefaces maximum. Write them into `src/theme.ts` as the only source of truth, then never hardcode a colour or a spring config inside a scene component. → [references/visual-system.md](references/visual-system.md)

### 3. Scaffold

```bash
npx create-video@latest --yes --blank --no-tailwind my-explainer
```

One folder per beat, with folder names matching beat-sheet ids exactly:

```
public/
  shared/background.png          # the locked background, 1920x1080
  scenes/
    scene-01-peace-deal/         # trump.png, khamenei.png, white-house.png
    scene-02-newspaper/
src/
  theme.ts                       # tokens + motion constants
  timing.json                    # generated in phase 9 — never hand-edited
  scenes/Scene01PeaceDeal.tsx
  MasterSequence.tsx
  Root.tsx
```

Asset filenames mirror the beat sheet so a missing asset shows up as a visible gap rather than a silent fallback.

### 4. Prep the cutouts

Midground cutouts must be transparent PNGs first. The image step is a manual handoff — hand the user one copyable list of every file and its prompt, then validate what comes back before doing anything else:

```bash
python scripts/check_assets.py --beat-sheet beat-sheet.csv --public public
```

That catches the four failures that otherwise surface in phase 7: a missing file, no alpha channel, an alpha channel that is fully opaque (a white background delivered as "transparent"), and a source too small to scale up. It exits non-zero, so it gates the next step. → [references/asset-handoff.md](references/asset-handoff.md)

Then halftone them deterministically:

```bash
python scripts/halftone.py --beat-sheet beat-sheet.csv --public public
```

This is an ordered-dither pass: the same input always yields the same output, so every character in the film matches. **Do not ask an image model to "make it halftone" per asset** — it drifts between assets and you cannot reproduce it later. Reading the beat sheet is what keeps this correct: it halftones exactly the `midground_asset` entries and leaves foregrounds in colour, in **one** run. A `*/*.png` glob would dither the occluders too, and separate runs can drift `--dot` and leave one character coarser than the rest.

It writes `<stem>-halftone.png` and `<stem>-halftone-stroke.png` beside each input. Point components at the `-halftone.png` file, not the original.


### 5. Scene components, prop-driven

Every scene has the same shape and takes every position, scale and timing value as a prop backed by a zod schema, so Remotion Studio renders controls for it. Without the schema there are no controls and phase 7 degrades into hand-editing numbers.

Start each scene from `assets/SceneTemplate.tsx`. → [references/scene-patterns.md](references/scene-patterns.md)

### 6. Animate

`spring()` for every entrance. `interpolate()` for drifts, fades, stroke draws and counters. Stagger siblings by 3–6 frames — foreground leads, midground follows. Constants live in `theme.ts`; the recipes (marker stroke, typewriter, counter, speech bubble, chart draw) are in [references/scene-patterns.md](references/scene-patterns.md).

### 7. Tune in Studio

```bash
npx remotion studio
```

Adjust props in the right-hand panel, then **persist every value you keep**. Studio's save writes back into `<Composition defaultProps>`, which must be a hardcoded literal — a computed expression there fails with `defaultProps prop must be a hardcoded value`. → [references/troubleshooting.md](references/troubleshooting.md)

### 8. Voiceover before assembly

Generate or collect the VO **before** building the master sequence. Every duration derives from the narration, so assembling first means doing this phase twice. Use the `remotion` skill's `rules/voiceover.md` for ElevenLabs, or accept a user-supplied mp3.

### 9. Word-level sync

```bash
python scripts/vo_timing.py voiceover.mp3 --beat-sheet beat-sheet.csv --fps 30 --out src/timing.json
```

Emits per-scene `from` / `durationInFrames`, plus the absolute frame of each `beat_word` so in-scene events land on the syllable. Import it; never type a duration by hand. → [references/vo-sync.md](references/vo-sync.md)

### 10. Music, then render

Bed music at roughly −18 dB under the VO, ducking further under narration. Then render in chunks rather than one long pass:

```bash
npx remotion render MasterSequence out/explainer.mp4 --frames=0-450
```

Chunking matters: a full render spins up headless Chrome under sustained load, and a crash 90% through a single-pass render costs the whole render.

## Verification

Before calling it done:

- `npx remotion still MasterSequence out/check.png --frame=<beat frame>` at each `beat_word` frame — confirm the visual actually lands on the word.
- Scrub the master in Studio once end to end, watching for a background that jumps between scenes (non-negotiable #1 broken) or two elements arriving together (#3 broken).
- Confirm the rendered MP4's duration matches the VO duration within a frame.

Audio sounding jerky while scrubbing in Studio is a Studio artifact, not a defect — it renders clean. Do not "fix" it.

## Asset reality check

**The image step is a manual handoff, and that is the normal shape of this pipeline — not a failure.** The user generates the cutouts in whatever image tool they already pay for (the ChatGPT web app, Midjourney, Magnific, Higgsfield, Gemini) and drops the files into the scene folders. Everything after that is automated. Say this once, at phase 1, so nobody waits on an asset that was never coming.

**Do not assume an image API exists.** A ChatGPT subscription is not API access, and the two are billed separately. Verified on this machine on 2026-09-02: `~/.codex/auth.json` holds `auth_mode: "chatgpt"` with `OPENAI_API_KEY: null`, and although that token is live, `POST /v1/images/generations` returns **401 `Missing scopes: api.model.images.request`** for both `dall-e-2` and `gpt-image-1`; `/v1/models` returns 403. The `OPENAI_API_KEY` environment variable is the 8-character `sk-12345` placeholder, and `OPENAI_BASE_URL` points at `http://127.0.0.1:8001/v1`, which is not listening. So: no programmatic generation here until a real `platform.openai.com` key with prepaid credit exists, and a real key must not go into `OPENAI_API_KEY` while that base URL is set. → [references/asset-handoff.md](references/asset-handoff.md)

What the handoff needs, so it only happens once:

| | |
|---|---|
| Format | PNG with a **real alpha channel**. A white background is not transparency — `halftone.py` warns and the dither then covers the whole frame. |
| Naming | Exactly the `midground_asset` / `foreground_asset` filenames from the beat sheet, in the matching `public/scenes/<id>/` folder. |
| Size | Midground figures ≥ 1200 px on the long edge; they get scaled up in-frame more than people expect. |
| Framing | Full body with headroom, feet included. The foreground occludes the lower body — you cannot crop what the composition needs to hide. |
| Style | Ordinary colour photo or illustration. **Do not** ask the image tool for halftone; phase 4 does that deterministically so every asset shares one dot grid. |

Everything else is handled here:

- **All cutout processing.** Halftoning, greyscaling, marker-stroke silhouettes and compositing: `scripts/halftone.py`. Background *removal* is the user's or a tool's job.
- **Stock footage and plates.** The Pexels MCP is wired up and keyless (verified working), and the `unsplash-asset-images` / `aura-asset-images` skills cover backgrounds, structures, tankers and ocean plates, including video plates for keying. Stock cannot give you a specific named person.
- **Voiceover** needs an ElevenLabs key or a user-supplied audio file. Ask for the with-timestamps response if ElevenLabs is used — it makes phase 9 exact for free.
- If the piece uses real people's likenesses and a recognizable house style, say once that publishing is the user's call, then proceed.


## Deliberate deviations

Two places this skill overrides its inputs, both on purpose:

- **The `remotion` skill says prefer `interpolate()` over `spring()`.** Here, entrances are `spring()` — the springy overshoot *is* the style. Keep `interpolate()` for everything continuous.
- **The source workflow assembles the master sequence, then adds voiceover and retimes.** Do voiceover first (phase 8 before assembly). Timing derived from a transcript beats timing nudged by eye, and it removes a whole retiming pass.

## Reference map

| File | Use it for |
|---|---|
| [references/visual-system.md](references/visual-system.md) | Colours, type, texture, stroke geometry, motion constants |
| [references/beat-sheet.md](references/beat-sheet.md) | Column semantics, a worked example, common beat-sheet mistakes |
| [references/asset-handoff.md](references/asset-handoff.md) | What to ask the image tool for, validating delivered cutouts, halftone gotchas |
| [references/scene-patterns.md](references/scene-patterns.md) | Scene component shape, marker stroke, typewriter, counter, keyed video, chart draw |
| [references/vo-sync.md](references/vo-sync.md) | Transcript → frame math, landing beats on words, retiming |
| [references/troubleshooting.md](references/troubleshooting.md) | `defaultProps`, missing Studio controls, jerky audio, Windows paths, render crashes |

| Script / asset | Does |
|---|---|
| `scripts/check_assets.py` | Validates delivered assets against the beat sheet; gates phase 4 |
| `scripts/halftone.py` | Deterministic ordered-dither halftone + pre-baked marker-stroke silhouette |
| `scripts/vo_timing.py` | Voiceover + beat sheet → `src/timing.json` (frames, beat frames, durations) |
| `assets/beat-sheet.template.csv` | Copy to the project root and fill; the `EXAMPLE-` rows are a hard error if left in |
| `assets/SceneTemplate.tsx` | Copy per beat; carries the zod schema and the foreground-leads entrance order |

