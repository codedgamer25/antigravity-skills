---
name: creative-code-video-motion-stack
description: Full creative code, animation, 3D, asset, sound, and export pipeline across 6 layers (agent skills, animation, 3D, assets, sound, export) using Remotion, Motion Canvas, Three.js/R3F, GSAP, and the 8-phase loop.
metadata:
  tags: remotion, motion-canvas, gsap, threejs, r3f, rive, lottie, video, animation, 3d, export, sound
---

# Creative Code Video & Motion Stack

A layered toolset and execution loop for building programmatic video, web motion, interactive 3D, and audio-reactive animations.

---

## 1. Tool Selection by Layer

### Layer 1: Agent Skills & Workflow Integration
Meta-instructions and AI coding agent toolkits for deterministic animation and timeline authoring:
- **Remotion Skills**: Official video authoring workflows, composition scaffolding, layout rules, and rendering guidelines for AI coding agents.
- **Motion AI Kit**: Structured Motion (Framer Motion) docs, transition heuristics, layout animation rules, and gesture guidance for AI coding agents.
- **GSAP Skills**: Timelines, stagger math, scroll triggers, and strict React/DOM cleanup patterns (`gsap.context()`).

### Layer 2: 2D & Timeline Animation
Engines for user interfaces, vector graphics, diagrams, and programmatic video timelines:
- **Remotion**: Programmatic React-based video timeline engine (`useCurrentFrame()`, `interpolate()`, `<Sequence>`, `<Composition>`).
- **Motion Canvas**: Programmatic technical diagrams, explainer animations, and math/vector scenes written in TypeScript generators.
- **Motion (formerly Framer Motion)**: Declarative React UI motion, layout transitions, exit/enter animations, and gesture handling.
- **GSAP (GreenSock)**: High-performance timeline sequencer, SVG morphing, text split animations, and scroll-driven choreography.
- **Anime.js**: Lightweight JavaScript animation engine for SVG path animations, complex CSS transforms, and staggered DOM effects.
- **Rive Web**: State-machine-driven interactive vector runtime connecting vector graphics to state changes.
- **dotLottie Web**: High-efficiency runtime player for rendering and controlling lightweight Lottie vector animations.

### Layer 3: 3D, Physics & Postprocessing
Interactive and rendered WebGL/WebGPU 3D graphic pipelines:
- **Three.js**: Fundamental WebGL scene graph, custom shaders, perspective/orthographic cameras, and lighting.
- **React Three Fiber (R3F)**: Declarative Three.js wrapper component system for React.
- **Drei**: Production helper abstractions for R3F (cameras, text rendering, environment maps, controls, loaders).
- **React Three Rapier**: Fast WebAssembly-powered rigid-body physics, colliders, joints, and raycasting for R3F scenes.
- **React Postprocessing**: Cinema-grade image finishing passes (bloom, Depth of Field, chromatic aberration, tone mapping).

### Layer 4: Asset Preparation & Title Cards
Vector normalization, dynamic graphics generation, and asset prep:
- **SVGO**: Lossless and lossy SVG optimizer and cleaner prior to animating paths or feeding into timelines.
- **Satori**: Generates clean, resolution-independent SVG title cards and graphic layouts from JSX and CSS Flexbox.

### Layer 5: Sound & Audio Systems
Audio playback, sound synthesis, mixing, and reactive cues:
- **Howler.js**: Web Audio API / HTML5 Audio wrapper for sound effects, audio sprites, volume fades, spatial panning, and cross-browser playback.

### Layer 6: Export & Rendering
Browser and server-side video compilation, encoding, and transcoding:
- **Mediabunny**: In-browser client-side video encoding, format conversion, and fast web stream export.
- **FFmpeg**: Industry-standard CLI / WASM pipeline for headless video stitching, high-fidelity H.264/HEVC/ProRes encoding, resolution scaling, and inspection.

---

## 2. The 8-Phase Production Loop

Follow this sequential pipeline for creative code motion & video projects:

```
[1. Brief] ➔ [2. Design] ➔ [3. Animate] ➔ [4. Build] ➔ [5. Sound] ➔ [6. Render] ➔ [7. Review] ➔ [8. Ship]
```

1. **Brief**
   - Define duration, canvas aspect ratio (16:9, 9:16, 1:1), target FPS (30 or 60), audience, and core narrative beats.
2. **Design**
   - Establish typography, layout bounds, color palette, and vector cards using Satori, Figma, or SVGO-cleaned SVG vectors.
3. **Animate**
   - Choreograph timing, easing curves (`cubic-bezier`), enter/exit stages, and keyframe interpolations using GSAP, Motion Canvas, or Remotion.
4. **Build**
   - Assemble composite layers: integrate 3D scenes (Three.js/R3F/Drei), physics (Rapier), UI components, and state machines (Rive/Lottie).
5. **Sound**
   - Score audio cues, SFX triggers, audio sprites, and ambient beds; synchronize keyframe events to beats using Howler.js or Remotion `<Audio>`.
6. **Render**
   - Compile target compositions via Mediabunny (in-browser) or Remotion CLI / FFmpeg (headless multi-threaded export).
7. **Review**
   - Inspect frame drops, audio-video sync, color grading, compression artifacts, and mobile/retina readability.
8. **Ship**
   - Package final artifacts (MP4, WebM, Lottie JSON, or interactive embed bundles) with production-ready asset caching.

---

## 3. Layer Selection Decision Matrix

| Requirement / Scenario | Recommended Layer Tools |
|---|---|
| **Programmatic Explainer / Code Video** | Remotion + Motion Canvas + Satori + Remotion Skills |
| **Interactive Web UI & Gestures** | Motion + GSAP + Rive Web |
| **3D Interactive Scene or Game** | Three.js + React Three Fiber + Drei + React Three Rapier + React Postprocessing |
| **Sound Effects & Audio Triggering** | Howler.js |
| **Serverless / Client Export Pipeline** | Mediabunny (Browser) or Remotion + FFmpeg (CLI/Server) |
| **SVG Micro-interactions** | SVGO + Anime.js or GSAP |
