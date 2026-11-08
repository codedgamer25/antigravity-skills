# Troubleshooting

Failures specific to this pipeline, in rough order of how often they bite.

## `defaultProps prop must be a hardcoded value`

```
Can't save default props: defaultProps prop must be a hardcoded value
in the <Composition> tag with the ID "Scene01Summit"
```

Studio's "save default props" rewrites the object literally in your source file, so it refuses to write into anything it cannot parse as a literal.

Breaks it:

```tsx
defaultProps={{ ...baseProps, midground: buildMidground(assets) }}
defaultProps={SCENE_01_PROPS}
defaultProps={{ scale: BASE_SCALE * 1.6 }}
```

Works:

```tsx
defaultProps={{ midground: [{ src: "scenes/scene-01-summit/envoy-a.png", x: -430, y: 0, scale: 1, flipStroke: false }] }}
```

Every value inline, no spreads, no imported constants, no arithmetic. This makes `Root.tsx` verbose and that is the correct trade — it is the only file Studio writes to, and verbosity there buys you working sliders everywhere else.

Note the asymmetry: `theme.ts` constants are fine *inside* scene components. The restriction is only on the `defaultProps` object.

## No prop controls appear in Studio

The right-hand Props panel is empty or read-only. Causes, in order:

1. **No `schema` on the `<Composition>`.** The schema is what generates the controls; `defaultProps` alone gives you a JSON blob you cannot drag.
2. **`zod` not installed**, so the schema import silently resolves to nothing. `npm i zod`.
3. **Schema shape does not match `defaultProps`** — Studio falls back to the raw JSON tab rather than erroring. Compare them field by field.
4. **Values are computed inside the component** rather than passed as props. A `scale` derived from a constant cannot be tuned; it has to enter through the schema.

Ask for controls on *every* element explicitly when scaffolding. Position, scale, rotation and entrance offset for each asset is the minimum useful set — that is what makes phase 7 a five-minute pass instead of an hour of edit-save-reload.

## Audio sounds jerky or stuttery while scrubbing

Expected. Remotion Studio decodes audio on demand while scrubbing; the rendered output is clean. Do not add crossfades, re-encode the VO, or "fix" timing in response to it. Confirm with a short render before believing any audio defect you only heard in Studio.

## Keyed video plate renders black

WebGL2 effects need the ANGLE renderer during render. Studio works without it, so this only shows up in the output file:

```ts
// remotion.config.ts
import { Config } from "@remotion/cli/config";
Config.setChromiumOpenGlRenderer("angle");
```

If it is still black, the effect import slug is probably wrong — most are `@remotion/effects/<slug>` but a few differ. Check the effects docs rather than guessing.

## Background visibly seams or flickers between scenes

Non-negotiable #1 is broken. Almost always because `<Background />` is rendered inside each scene instead of once outside the `<Series>`. A remount re-rasterises the texture and can land it a subpixel off.

Second cause: the background asset is not exactly 1920 × 1080 and is being scaled with a non-integer factor per scene. Resize the source, do not scale at render.

## Counter, chart, or typewriter never fires

`beatFrame` was passed as an absolute frame. `<Series.Sequence>` resets `useCurrentFrame()` to 0, so a component inside it never sees frame 1400 and the interpolate range never opens. Convert to scene-local before passing:

```tsx
beatFrame={s.beatFrame - s.from}
```

## Everything arrives at once

Non-negotiable #3. Check that the stagger index is actually varying — `pop(i)` inside a `.map()` with `i` shadowed, or `pop(0)` copy-pasted across siblings, both produce a simultaneous entrance that looks like a slideshow.

## Halftone dots look different between two assets

An image model was asked to halftone them separately. Re-run every cutout through `scripts/halftone.py` with the same flags. The whole reason that script exists is that the dither is deterministic; two model generations never match.

Also check you have not mixed pre-baked halftone with the render-time `halftone()` effect in one film.

## Render crashes partway through

Render in chunks and keep them small enough to restart cheaply:

```bash
npx remotion render MasterSequence out/part-01.mp4 --frames=0-450
npx remotion render MasterSequence out/part-02.mp4 --frames=451-900
```

Then concatenate with ffmpeg's concat demuxer. A full-length single pass runs headless Chrome under sustained load for minutes; on hardware with any thermal or memory instability that is the worst possible shape of workload, and a crash at 90% costs the entire render.

Also worth lowering before blaming the machine: `--concurrency=2` and `--scale=0.5` for review renders.

## Windows path problems

Two distinct traps:

- **ffmpeg filter arguments.** Git Bash rewrites POSIX-looking paths inside `-filter_complex` and similar arguments, producing "no such file" for a file that plainly exists. Build filtergraphs from Python with `subprocess` and a list of args instead of a shell string.
- **`staticFile()` always takes forward slashes**, relative to `public/`, with no leading slash. `staticFile("scenes/scene-01/a.png")` — never a backslash and never an absolute path.

## A shell parked in the project directory blocks the build

A terminal whose working directory is inside the build output can hold a lock that makes the next build hang with no error after printing its banner. Move the shell out of the project before rebuilding, and clear stale output directories from PowerShell if `rm -rf` will not.
