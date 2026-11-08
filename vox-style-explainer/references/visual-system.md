# Visual system

Lock every value here into `src/theme.ts` before writing a scene. Scene components import tokens; they never hold literals.

This is a **technique vocabulary** — halftone collage, offset stroke, locked ground — not a clone of any publisher's brand. Pick your own palette and typefaces from the ranges below rather than reproducing a specific outlet's identity.

## Canvas

| | |
|---|---|
| Resolution | 1920 × 1080 |
| Frame rate | 30 fps |
| Duration | Derived from the voiceover (phase 9), never chosen |
| Safe margin | 96 px on all sides; nothing meaningful crosses it |

30 fps, not 60: the motion language is discrete pops, and 30 halves render time for no visible loss.

## Palette

Five roles, and only five. More than one accent and the collage turns muddy.

```ts
export const palette = {
  paper:      "#EDEBE4", // background base — warm off-white, never pure white
  paperShade: "#DFDCD2", // grid lines, panel edges, soft shadow on paper
  ink:        "#1A1A18", // halftone blacks, body type
  stroke:     "#D6252B", // the offset marker stroke — one red, used nowhere else
  accent:     "#F0821E", // number labels, bars, chart fills, lower-third blocks
} as const;
```

Rules that matter more than the hex values:

- **`paper` is never `#FFF`.** A pure-white ground kills the print illusion instantly.
- **`stroke` is reserved.** The red appears only as the offset marker stroke behind midground cutouts. The moment it also becomes a text colour, it stops reading as a drawn stroke.
- **Foreground objects stay in their own colours**, desaturated ~15% and lifted ~8% in luminance so they sit on the paper rather than punching through it.
- Midground is pure `ink` on transparent. No greys beyond what the halftone dither produces.

## Texture

Two overlays, both static, both extremely subtle. They do the "printed" work:

```ts
export const texture = {
  gridSpacing: 64,      // px between grid lines on the background
  gridOpacity: 0.35,    // paperShade at this alpha
  grainOpacity: 0.06,   // fixed-noise PNG over everything, screen blend
  vignette: 0.10,       // radial darkening at the corners
};
```

The grain must be a **static** image, not per-frame noise — animated grain reads as video compression artifacting and fights the print feel. Grid lines belong to the background asset itself so they can never drift relative to it.

## The offset marker stroke

The signature move, and the cheapest depth in the whole style. Behind each midground cutout sits a copy of the same cutout, filled flat red, displaced a few pixels — as if someone outlined the figure by hand and missed.

```ts
export const markerStroke = {
  offsetX: 14,        // px right; negative for figures facing left
  offsetY: 10,        // px down — always down, gravity reads as shadow
  rotation: -1.2,     // deg; the imperfection is the point
  spread: 6,          // px of dilation so the red reads as a stroke, not a twin
  color: palette.stroke,
};
```

Build it as a dilated silhouette, not a second photo:

1. Take the halftoned cutout's alpha channel.
2. Dilate the alpha by `spread` px.
3. Fill it flat `stroke`.
4. Offset by `offsetX` / `offsetY`, rotate by `rotation`.
5. Render it immediately beneath the cutout in the same transform group, so props move both together.

Mirror `offsetX` per figure so two facing subjects have strokes on their outer edges. Strokes pointing the same way on a facing pair looks like a mistake.

`scene-patterns.md` has the working component.

## Typography

Three faces, each with one job. Load via `@remotion/google-fonts`.

| Role | Face | Weight | Use |
|---|---|---|---|
| Display | `Playfair Display` or `Libre Baskerville` | 700 | Newspaper headlines, title cards |
| Numeric | `Archivo` or `Barlow Condensed` | 800 | `$116`, `39 TRILLION`, chart labels |
| Utility | `IBM Plex Mono` | 500 | Source credits, dates, small annotations |

Sizing for 1080p — these are floors, and video type runs far larger than web type:

```ts
export const type = {
  hero:    { size: 148, tracking: -0.02, leading: 0.92 },
  number:  { size: 196, tracking: -0.03, leading: 0.9  },
  headline:{ size:  76, tracking: -0.01, leading: 1.05 },
  label:   { size:  34, tracking:  0.08, leading: 1.2  }, // uppercase
  credit:  { size:  22, tracking:  0.12, leading: 1.2  },
};
```

Big numbers get a solid `accent` block behind or beside them, never a gradient. Uppercase `label` text is always tracked out; uppercase at web tracking looks cramped on a 1080p frame.

## Motion constants

The entire film uses one spring and one easing curve. Variety comes from stagger and distance, not from per-element tuning.

```ts
export const motion = {
  pop:  { damping: 12, mass: 0.6, stiffness: 120 }, // every entrance
  settle: { damping: 26, mass: 1.0, stiffness: 90 }, // rare; heavy objects
  stagger: 5,        // frames between siblings — 3 is tight, 6 is lazy
  driftPerSecond: 8, // px of slow continuous drift on the foreground
  ease: [0.16, 1, 0.3, 1] as const, // Easing.bezier args for interpolate()
};
```

Entrance order within a scene, always:

1. **Foreground** springs up first, from `+60 px` below its resting position.
2. **Midground** figures follow, `stagger` frames apart, from `+40 px`, outermost figure last.
3. **Type and numbers** last, `stagger * 2` after the final figure.

Foreground first is counter-intuitive and load-bearing: it establishes the ground plane so the figures read as standing behind something rather than floating.

The `pop` spring overshoots by roughly 6% — that overshoot is the style. Do not replace it with a clamped `interpolate()`.

## Transitions between scenes

The background never cuts, so transitions only move the layers above it:

| Name | What moves | When |
|---|---|---|
| **Hard cut** | Everything above the background swaps in one frame | Default; use for most beats |
| **Slide-up** | Outgoing layers exit up, incoming enter from below | Cause → effect beats |
| **Closer move** | Foreground scales 1.0 → 1.08 across the scene | Escalation, dread |
| **Paper wipe** | A `paperShade` panel sweeps across, layers swap beneath | Section change only, at most twice per film |

Never cross-dissolve. A dissolve between two halftone cutouts turns both to mush.
