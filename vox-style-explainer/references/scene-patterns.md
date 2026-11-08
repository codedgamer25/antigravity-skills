# Scene patterns

Working component recipes for this style. All of them assume `src/theme.ts` exports `palette`, `type`, `motion`, `markerStroke` and `texture` as defined in [visual-system.md](visual-system.md).

Install once: `npm i zod`, and `npx remotion add @remotion/effects` if you use the keyed-video or render-time halftone recipes.

## Scene component shape

Every scene follows this shape. The zod schema is what makes Studio render controls — no schema, no controls, and phase 7 becomes hand-editing numbers.

```tsx
// src/scenes/Scene01Summit.tsx
import { z } from "zod";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring } from "remotion";
import { Background } from "../components/Background";
import { Cutout } from "../components/Cutout";
import { Foreground } from "../components/Foreground";
import { motion } from "../theme";

const placement = z.object({
  src: z.string(),
  x: z.number(),          // px from centre, negative = left
  y: z.number(),          // px from bottom baseline
  scale: z.number(),
  flipStroke: z.boolean(), // mirrors the marker stroke for facing pairs
});

export const scene01Schema = z.object({
  midground: z.array(placement),
  foreground: placement.nullable(),
  entranceDelay: z.number(),
});

export const Scene01Summit: React.FC<z.infer<typeof scene01Schema>> = ({
  midground,
  foreground,
  entranceDelay,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Foreground leads, midground follows, outermost figure last.
  const pop = (index: number) =>
    spring({
      frame: frame - entranceDelay - index * motion.stagger,
      fps,
      config: motion.pop,
    });

  return (
    <AbsoluteFill>
      <Background />
      {midground.map((item, i) => (
        <Cutout key={item.src} {...item} progress={pop(i + 1)} rise={40} />
      ))}
      {foreground && <Foreground {...foreground} progress={pop(0)} rise={60} />}
    </AbsoluteFill>
  );
};
```

Two details that are easy to get wrong:

- **`pop(0)` is the foreground.** Midground indices start at 1 so the ground plane always establishes first.
- **Keep `interpolate()` calls inline in the `style` prop** and animate individual CSS properties (`scale`, `translate`, `rotate`) rather than composing a `transform` string. Studio can only edit values it can find in the style object.

## Wiring it in Root.tsx

`defaultProps` must be a **hardcoded literal**. Studio's "save default props" rewrites this object in place, and it refuses to write into a computed expression.

```tsx
// src/Root.tsx
import { Composition } from "remotion";
import { Scene01Summit, scene01Schema } from "./scenes/Scene01Summit";

export const RemotionRoot = () => (
  <>
    <Composition
      id="Scene01Summit"
      component={Scene01Summit}
      schema={scene01Schema}
      durationInFrames={120}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{
        midground: [
          { src: "scenes/scene-01-summit/envoy-a.png", x: -430, y: 0, scale: 1.0, flipStroke: false },
          { src: "scenes/scene-01-summit/envoy-b.png", x: 430, y: 0, scale: 1.0, flipStroke: true },
        ],
        foreground: { src: "scenes/scene-01-summit/ministry.png", x: 0, y: -40, scale: 1.6, flipStroke: false },
        entranceDelay: 0,
      }}
    />
  </>
);
```

Register **one composition per scene** while building, plus the master. Per-scene compositions are what make phase 7 tolerable — you tune a scene without scrubbing past the ones before it.

## Cutout with offset marker stroke

The signature element. One transform group holds stroke and cutout so a prop change moves both.

```tsx
// src/components/Cutout.tsx
import { Img, staticFile, interpolate, Easing } from "remotion";
import { markerStroke, motion } from "../theme";

type Props = {
  src: string;
  x: number;
  y: number;
  scale: number;
  flipStroke: boolean;
  progress: number; // 0..1 from spring()
  rise: number;     // px it travels up on entry
};

// halftone.py pads the stroke canvas by (stroke-spread + 2) px per side so the
// dilation is not clipped at the image edge. The padded PNG is therefore larger
// than the cutout, and the pad must be subtracted or the stroke sits that many px
// right and down from the offsets in theme.ts. The script prints the value it used.
const STROKE_PAD = markerStroke.spread + 2;

export const Cutout: React.FC<Props> = ({ src, x, y, scale, flipStroke, progress, rise }) => {
  const dx = flipStroke ? -markerStroke.offsetX : markerStroke.offsetX;

  return (
    <div
      style={{
        position: "absolute",
        left: "50%",
        bottom: 0,
        translate: `${x}px ${y + (1 - progress) * rise}px`,
        scale: String(scale),
        opacity: interpolate(progress, [0, 0.35], [0, 1], {
          extrapolateRight: "clamp",
          easing: Easing.bezier(...motion.ease),
        }),
        transformOrigin: "bottom center",
      }}
    >
      {/* dilated red silhouette, offset — produced by scripts/halftone.py --stroke */}
      <Img
        src={staticFile(src.replace(/\.png$/, "-stroke.png"))}
        style={{
          position: "absolute",
          left: dx - STROKE_PAD,
          top: markerStroke.offsetY - STROKE_PAD,
          rotate: `${markerStroke.rotation}deg`,
        }}
      />
      <Img src={staticFile(src)} />
    </div>
  );
};
```

Note the filename: `halftone.py` writes `<stem>-halftone.png` and `<stem>-halftone-stroke.png`. So a `midground_asset` of `tanker.png` becomes `tanker-halftone.png` in `staticFile()`, and the `.replace()` above resolves its stroke. Point `src` at the **halftoned** file, not the original.

`scripts/halftone.py --stroke` pre-bakes the dilated silhouette so no per-frame filter work happens at render time. Pre-baking beats an SVG filter here: filters re-run every frame for a shape that never changes.

## Number counter that lands on a word

The most-noticed timing detail in the whole style. `landFrame` comes from `timing.json`, not from a guess.

```tsx
// src/components/Counter.tsx
import { useCurrentFrame, interpolate, Easing } from "remotion";
import { palette, type as t, motion } from "../theme";

export const Counter: React.FC<{
  to: number;
  landFrame: number;
  rampFrames?: number;
  prefix?: string;
}> = ({ to, landFrame, rampFrames = 26, prefix = "" }) => {
  const frame = useCurrentFrame();
  const value = interpolate(frame, [landFrame - rampFrames, landFrame], [0, to], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(...motion.ease),
  });

  return (
    <span
      style={{
        fontFamily: "Archivo",
        fontWeight: 800,
        fontSize: t.number.size,
        letterSpacing: `${t.number.tracking}em`,
        color: palette.ink,
        background: palette.accent,
        padding: "0 18px",
      }}
    >
      {prefix}
      {Math.round(value).toLocaleString()}
    </span>
  );
};
```

The ramp **ends** on `landFrame` — it does not start there. A counter that starts moving on the word always reads late.

## Typewriter reveal

For newspaper headlines and lower thirds. Reveal by character count, not by opacity.

```tsx
const chars = Math.floor(
  interpolate(frame, [start, start + text.length * 1.4], [0, text.length], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  })
);
return <span>{text.slice(0, chars)}</span>;
```

`1.4` frames per character is roughly newsroom pace at 30 fps. Below 1.0 it reads as a wipe; above 2.0 the audience finishes reading before the machine does.

## Keyed video plate

For an ocean, smoke or crowd plate delivered on a solid background. `colorKey()` needs a canvas-based component — `<Video>` from `@remotion/media`, not `<Img>`.

```tsx
import { Video } from "@remotion/media";
import { colorKey } from "@remotion/effects/color-key";
import { staticFile } from "remotion";

<Video
  src={staticFile("scenes/scene-03-tanker/ocean-plate.mp4")}
  effects={[colorKey({ color: "#00B140", similarity: 0.32, smoothness: 0.08 })]}
  loop
/>;
```

Verify the import slug against the effects docs before relying on it; most are `@remotion/effects/<slug>`. Effects use WebGL2, so renders need this in `remotion.config.ts` or the plate comes out black:

```ts
import { Config } from "@remotion/cli/config";
Config.setChromiumOpenGlRenderer("angle");
```

Prefer a `.webm` with a real alpha channel when you can get one — keying is always a compromise, and green fringing on a halftone edge is very visible.

## Render-time halftone

`scripts/halftone.py` pre-bakes cutouts, which is the default and what you want for characters. Use the render-time `halftone()` effect instead only when the source is *video* or when the user wants to tune dot size live in Studio:

```tsx
import { halftone } from "@remotion/effects/halftone";
<Video src={staticFile("plate.mp4")} effects={[halftone({ dotSize: 4 })]} />;
```

Do not mix the two on the same film. Pre-baked and render-time dot grids will not align, and the mismatch reads as two different textures.

## Master sequence

`<Series>` chains the scenes. Every duration comes from `timing.json`; nothing here is typed by hand.

```tsx
// src/MasterSequence.tsx
import { Series, AbsoluteFill } from "remotion";
import { Audio } from "@remotion/media";
import { staticFile } from "remotion";
import timing from "./timing.json";
import { SCENES } from "./scenes";        // id -> { component, props }
import { Background } from "./components/Background";

export const MasterSequence = () => (
  <AbsoluteFill>
    {/* One background for the whole film, outside the Series — this is what stops the cut. */}
    <Background />
    <Series>
      {timing.scenes.map((s) => {
        const { component: Scene, props } = SCENES[s.id];
        return (
          <Series.Sequence key={s.id} durationInFrames={s.durationInFrames} layout="none">
            <Scene {...props} beatFrame={s.beatFrame - s.from} />
          </Series.Sequence>
        );
      })}
    </Series>
    <Audio src={staticFile("voiceover.mp3")} />
    <Audio src={staticFile("music.mp3")} volume={0.12} />
  </AbsoluteFill>
);
```

**`<Background />` sits outside the `<Series>`.** Putting it inside each scene remounts it on every cut, and a remounted texture flickers by a pixel — which is exactly the seam non-negotiable #1 exists to prevent.

`beatFrame` is converted to scene-local frames before it reaches the component, since `<Series.Sequence>` resets `useCurrentFrame()` to 0.

## Composition duration

Let the VO define it rather than hardcoding a number that drifts:

```tsx
<Composition
  id="MasterSequence"
  component={MasterSequence}
  fps={30}
  width={1920}
  height={1080}
  durationInFrames={timing.totalFrames}
  defaultProps={{}}
/>
```

`timing.totalFrames` is a literal in the generated JSON, so this stays a static import — no `calculateMetadata` needed unless the VO is fetched at runtime.
