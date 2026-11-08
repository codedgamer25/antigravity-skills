/**
 * SceneTemplate.tsx — copy to src/scenes/SceneNNSlug.tsx and rename the two exports.
 *
 * Contract (see references/scene-patterns.md):
 *   - Every position/scale/timing value is a prop backed by a zod schema, so Remotion
 *     Studio renders controls for it. No schema means no controls.
 *   - pop(0) is the FOREGROUND. Midground indices start at 1 so the ground plane
 *     establishes before the figures.
 *   - `beatFrame` arrives already converted to scene-local frames by MasterSequence.
 *   - interpolate() stays inline in the style prop, on individual CSS properties
 *     (scale/translate/rotate) — never composed into a transform string.
 */
import React from "react";
import { z } from "zod";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from "remotion";

import { Cutout } from "../components/Cutout";
import { Foreground } from "../components/Foreground";
import { motion } from "../theme";

/** One placed image. `flipStroke` mirrors the red marker stroke for facing pairs. */
const placement = z.object({
  src: z.string(),
  x: z.number(),
  y: z.number(),
  scale: z.number(),
  flipStroke: z.boolean(),
});

// RENAME: sceneNNSlugSchema
export const sceneTemplateSchema = z.object({
  /** Entrance order == array order. Outermost figure last. */
  midground: z.array(placement),
  /** null for map/chart beats with no occluder. */
  foreground: placement.nullable(),
  /** Frames to hold before the first spring starts. Usually 0. */
  entranceDelay: z.number(),
  /**
   * Scene-local frame the payoff must COMPLETE on, from timing.json.
   * MasterSequence passes `s.beatFrame - s.from`. Never hand-type this.
   */
  beatFrame: z.number(),
});

export type SceneTemplateProps = z.infer<typeof sceneTemplateSchema>;

// RENAME: SceneNNSlug
export const SceneTemplate: React.FC<SceneTemplateProps> = ({
  midground,
  foreground,
  entranceDelay,
  beatFrame,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // One spring for the whole film. Variety comes from stagger, not per-element tuning.
  const pop = (index: number) =>
    spring({
      frame: frame - entranceDelay - index * motion.stagger,
      fps,
      config: motion.pop,
    });

  return (
    <AbsoluteFill>
      {/*
        NO <Background /> here. The background lives once in MasterSequence, outside
        the <Series>. Mounting it per scene remounts the texture on every cut and it
        flickers by a pixel — the exact seam non-negotiable #1 exists to prevent.
      */}

      {midground.map((item, i) => (
        <Cutout key={item.src} {...item} progress={pop(i + 1)} rise={40} />
      ))}

      {foreground ? (
        <Foreground {...foreground} progress={pop(0)} rise={60} />
      ) : null}

      {/*
        BEAT PAYOFF — delete if this beat has none.
        The event ENDS on beatFrame; it does not start there. A counter, chart or
        typewriter that begins moving on the word always reads late.

        <Counter to={116} landFrame={beatFrame} prefix="$" />
      */}
    </AbsoluteFill>
  );
};
