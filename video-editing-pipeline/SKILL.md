---
name: video-editing-pipeline
description: Video editing workflows, FFmpeg encoding, scriptwriting, pacing, cut grammar, color grading pipelines (LUTs/ACES), motion graphics choreography, and audio mixing for YouTube, shorts, launch films, and cinematic presentations. Use when user asks for video editing, FFmpeg command generation, storyboard pacing, or post-production pipelines.
---

# Video Production & Editing Pipeline

Standards and technical protocols for high-fidelity post-production, timeline structuring, and programmatic media manipulation.

## 1. Edit Grammar & Pacing
- **Cut Types & Rhythm:** J-cuts, L-cuts, match cuts, invisible pans, and eye-trace continuity.
- **Narrative Pacing:** Dynamic tension curves, drop anticipation, downbeat alignments, micro-pauses for cognitive relief, and decisive endings.
- **Aspect Ratio Mastery:** 16:9 cinematic landscape, 9:16 vertical shorts/reels, and 1:1 responsive squares.

## 2. Programmatic Media (FFmpeg & Remotion)
- **High-Performance Encoding:** `libx264`/`libx265`, `-crf 16-20`, GOP size calibration (`-g 1` for intra-frame seeking), and `yuv420p` pixel format parity.
- **Audio Conditioning:** Loudnorm to `-14 LUFS`, high-pass rumble filters (80Hz cut), sidechain compression, and precise peak timing alignment.
- **Filter Chains:** Complex filtergraphs (`complex_filter`) for picture-in-picture, split-screens, color balance adjustments, and text burn-ins.
