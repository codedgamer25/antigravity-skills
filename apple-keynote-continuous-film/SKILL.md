---
name: apple-keynote-continuous-film
description: Build and render 2D continuous-take Apple-Keynote style launch films in code (pure-time seek(t), closed-form spring mechanics, iOS 26 liquid glass displacement shaders, mechanical hexagonal iris aperture, screen-studio zoom handoffs, and EBU R128 audio mastering).
---

# Apple Keynote Continuous Film Motion System

A production framework for engineering 60fps/120fps continuous-take 2D motion graphics and keynote-grade product launch films entirely in code.

---

## 1. Core Principles & Continuous-Take Discipline

1. **Zero Cut / Zero Crossfade Invariant**:
   - The camera never cuts. Scenes never fade to black, crossfade, or blur out.
   - Every subsequent scene, object, or interface container is born from the physical geometry of the previous element (e.g., an app icon expands into a window, a window condenses into a mechanical iris, an iris closes down to an optical lens that morphs into a delivery van).
2. **Deterministic Time Evaluation**:
   - No `requestAnimationFrame` accumulators, no `Date.now()`, no `performance.now()`, and no non-seeded random numbers inside the animation core.
   - Motion is strictly defined as an immutable function of time: $S(t) = \text{evaluate}(t)$, where $t \in [0, T_{\text{total}}]$.
3. **Physical Weight & Overshoot**:
   - Every movement is governed by analytical spring mechanics. Linear or arbitrary bezier easings are prohibited for structural transforms.

---

## 2. Pure-Time `seek(t)` Architecture

The animation engine must expose a single synchronous entry point: `seek(t)`.

```typescript
export interface KeynoteEngine {
  readonly duration: number; // Duration in seconds (e.g. 15.0)
  readonly fps: number;      // Target FPS (60 or 120)
  readonly width: number;    // Canvas width (e.g. 1920 or 3840)
  readonly height: number;   // Canvas height (e.g. 1080 or 2160)
  seek(t: number): void;     // Deterministic evaluation at exact timestamp t
  render(): void;            // Draw current state to canvas / DOM
}
```

### Canvas Implementation Pattern
```javascript
class ContinuousFilm {
  constructor(canvas, config = {}) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.duration = config.duration || 12.0;
    this.fps = config.fps || 60;
    this.width = canvas.width;
    this.height = canvas.height;
  }

  seek(t) {
    // Clamp t to deterministic duration or modulo for looping preview
    const clampedTime = Math.max(0, Math.min(t, this.duration));
    
    // Evaluate scene states purely from clampedTime
    this.ctx.clearRect(0, 0, this.width, this.height);
    this.renderScene(clampedTime);
  }

  renderScene(t) {
    // Pure time-derived transforms and drawing operations
  }
}
```

---

## 3. Closed-Form Analytic Spring Mechanics

Traditional numerical integration (Euler, Verlet) drifts when frame steps vary or during parallel headless rendering. Use the **closed-form solution** of a damped harmonic oscillator:

$$\ddot{x} + 2\zeta\omega_n \dot{x} + \omega_n^2 x = 0$$

Where:
- $\omega_n = \sqrt{k / m} = \sqrt{k}$ (natural frequency, assuming mass $m = 1$)
- $\zeta = \frac{c}{2\sqrt{k m}}$ (damping ratio, where $\zeta = 1$ is critical damping, $\zeta < 1$ is underdamped)
- $\omega_d = \omega_n \sqrt{1 - \zeta^2}$ (damped frequency)

### Single-Target Analytical Step: `springStep(t, k, zeta)`
Calculates normalized position moving from $0 \to 1$ starting at $t = 0$:

```javascript
/**
 * Closed-form unit step response for a spring oscillator
 * @param {number} t - Time elapsed since trigger (seconds)
 * @param {number} k - Stiffness (typical: 100 - 400)
 * @param {number} zeta - Damping ratio (0.5 - 0.85 for keynote snap)
 * @returns {number} Value from 0 approaching 1 with natural overshoot
 */
export function springStep(t, k = 180, zeta = 0.72) {
  if (t <= 0) return 0;
  
  const omegaN = Math.sqrt(k);
  
  if (zeta < 1.0) {
    // Underdamped (standard keynote organic snap with subtle overshoot)
    const omegaD = omegaN * Math.sqrt(1 - zeta * zeta);
    const decay = Math.exp(-zeta * omegaN * t);
    const envelope = Math.cos(omegaD * t) + (zeta * omegaN / omegaD) * Math.sin(omegaD * t);
    return 1 - decay * envelope;
  } else if (zeta === 1.0) {
    // Critically damped (fastest settle without overshoot)
    return 1 - Math.exp(-omegaN * t) * (1 + omegaN * t);
  } else {
    // Overdamped
    const s = Math.sqrt(zeta * zeta - 1);
    const r1 = -omegaN * (zeta - s);
    const r2 = -omegaN * (zeta + s);
    return 1 - (r2 * Math.exp(r1 * t) - r1 * Math.exp(r2 * t)) / (r2 - r1);
  }
}
```

### Multi-Target Linear Superposition Accumulator
When an element moves from $A \to B \to C$ across multiple beats, compute the response analytically by superposing delta steps:

```javascript
/**
 * Analytic multi-keyframe spring accumulator
 * @param {number} t - Current absolute time
 * @param {number} baseValue - Initial state at t = 0
 * @param {Array<{t: number, value: number, k?: number, zeta?: number}>} keyframes
 */
export function springAccumulator(t, baseValue, keyframes) {
  let currentValue = baseValue;
  let previousTarget = baseValue;

  for (let i = 0; i < keyframes.length; i++) {
    const kf = keyframes[i];
    if (t < kf.t) break;

    const delta = kf.value - previousTarget;
    const elapsed = t - kf.t;
    const step = springStep(elapsed, kf.k || 220, kf.zeta || 0.75);
    
    currentValue += delta * step;
    previousTarget = kf.value;
  }

  return currentValue;
}
```

---

## 4. iOS "Liquid Glass" Shader & Specular Rim Refraction

Keynote liquid glass panels exhibit:
1. Distance-field rounded corners ($sdRoundRect$).
2. Refractive background displacement with chromatic separation.
3. Fresnel specular rim lighting with micro-bevel reflections.

### Signed Distance Field: `sdRoundRect`
$$\vec{p} = |p| - \vec{b} + r$$
$$d(p) = \|\max(\vec{p}, 0)\| + \min(\max(p_x, p_y), 0) - r$$

```glsl
// Liquid Glass Fragment Shader (WebGL2)
#version 300 es
precision highp float;

in vec2 vUv;
out vec4 fragColor;

uniform sampler2D uBackdrop; // Rendered background snapshot
uniform vec2 uResolution;
uniform vec4 uRect;          // x, y, width, height
uniform float uRadius;       // Corner radius in px
uniform float uThickness;    // Refraction thickness
uniform vec3 uRimColor;      // e.g. vec3(1.0, 1.0, 1.0)
uniform float uChromatic;    // Chromatic dispersion factor (e.g. 0.008)

float sdRoundRect(vec2 p, vec2 b, float r) {
  vec2 d = abs(p) - b + vec2(r);
  return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)) - r;
}

void main() {
  vec2 pixelPos = vUv * uResolution;
  vec2 rectCenter = uRect.xy + uRect.zw * 0.5;
  vec2 localPos = pixelPos - rectCenter;
  vec2 halfSize = uRect.zw * 0.5;

  float dist = sdRoundRect(localPos, halfSize, uRadius);

  if (dist > 0.0) {
    discard; // Outside glass container
  }

  // Refraction normal gradient derived from distance field
  float eps = 1.0;
  float dx = sdRoundRect(localPos + vec2(eps, 0.0), halfSize, uRadius) - dist;
  float dy = sdRoundRect(localPos + vec2(0.0, eps), halfSize, uRadius) - dist;
  vec2 normal2D = normalize(vec2(dx, dy));

  // Edge depth factor for lens bulge
  float edgeDist = -dist;
  float bulge = smoothstep(0.0, uRadius * 1.5, edgeDist);
  vec2 refrOffset = normal2D * (1.0 - bulge) * uThickness / uResolution;

  // Chromatic dispersion sampling
  float r = texture(uBackdrop, vUv + refrOffset * (1.0 + uChromatic)).r;
  float g = texture(uBackdrop, vUv + refrOffset).g;
  float b = texture(uBackdrop, vUv + refrOffset * (1.0 - uChromatic)).b;
  vec3 glassColor = vec3(r, g, b);

  // Specular Fresnel Rim
  float rim = pow(clamp(1.0 - edgeDist / (uRadius * 0.35), 0.0, 1.0), 3.0);
  glassColor += uRimColor * rim * 0.85;

  // Subtle interior ambient absorption
  glassColor = mix(glassColor, vec3(0.98, 0.99, 1.0), 0.06);

  fragColor = vec4(glassColor, 1.0);
}
```

### Canvas 2D Fallback Implementation
For standard 2D canvas, simulate liquid glass using an offscreen backdrop buffer with multi-layer stroke clips:
```javascript
export function drawLiquidGlass2D(ctx, backdropCanvas, x, y, w, h, r, rimIntensity = 1.0) {
  ctx.save();
  
  // Rounded rect clip path
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
  ctx.clip();

  // Draw displaced background (slight zoom-in to simulate 1.12 index of refraction)
  const scale = 1.04;
  ctx.drawImage(
    backdropCanvas,
    x - (w * (scale - 1)) / 2,
    y - (h * (scale - 1)) / 2,
    w * scale,
    h * scale
  );

  // Subtle frosted glaze tint
  ctx.fillStyle = 'rgba(255, 255, 255, 0.07)';
  ctx.fill();

  // Specular Rim Gradient
  const grad = ctx.createLinearGradient(x, y, x + w, y + h);
  grad.addColorStop(0, `rgba(255, 255, 255, ${0.45 * rimIntensity})`);
  grad.addColorStop(0.3, 'rgba(255, 255, 255, 0.05)');
  grad.addColorStop(0.8, 'rgba(255, 255, 255, 0.0)');
  grad.addColorStop(1, `rgba(255, 255, 255, ${0.3 * rimIntensity})`);

  ctx.lineWidth = 1.5;
  ctx.strokeStyle = grad;
  ctx.stroke();

  ctx.restore();
}
```

---

## 5. Mechanical 6-Blade Hexagonal Iris Aperture

A continuous mechanical transition involves 6 interlocking iris blades rotating tangentially around a central hexagonal aperture opening from $R_{\text{closed}}$ to $R_{\text{open}}$.

```javascript
/**
 * 6-Blade Hexagonal Iris Geometry
 * @param {CanvasRenderingContext2D} ctx
 * @param {number} cx - Center X
 * @param {number} cy - Center Y
 * @param {number} outerR - Maximum chassis radius
 * @param {number} openFactor - 0.0 (fully closed) to 1.0 (fully open)
 * @param {number} rotation - Global chassis orientation angle
 */
export function drawMechanicalIris(ctx, cx, cy, outerR, openFactor, rotation = 0) {
  const blades = 6;
  const baseAngle = (Math.PI * 2) / blades;
  
  // Iris aperture radius mapping
  const minAperture = 0;
  const maxAperture = outerR * 0.78;
  const currentAperture = minAperture + (maxAperture - minAperture) * openFactor;
  
  // Tangential blade angle derived from aperture opening
  const bladeAngleOffset = (1 - openFactor) * 0.58;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(rotation);

  for (let i = 0; i < blades; i++) {
    const angle = i * baseAngle;
    ctx.save();
    ctx.rotate(angle);

    // Blade path: tangential sliding curved polygon
    ctx.beginPath();
    const pivotX = Math.cos(bladeAngleOffset) * outerR;
    const pivotY = Math.sin(bladeAngleOffset) * outerR;

    ctx.moveTo(currentAperture, 0);
    ctx.lineTo(outerR, 0);
    ctx.arc(0, 0, outerR, 0, baseAngle * 1.35);
    ctx.lineTo(pivotX, pivotY);
    ctx.closePath();

    // Dark titanium metallic gradient
    const bladeGrad = ctx.createLinearGradient(0, 0, outerR, outerR * 0.5);
    bladeGrad.addColorStop(0, '#1c1d22');
    bladeGrad.addColorStop(0.5, '#282a30');
    bladeGrad.addColorStop(1, '#0f1013');

    ctx.fillStyle = bladeGrad;
    ctx.fill();

    // Micro-machined edge stroke highlight
    ctx.lineWidth = 1.0;
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.18)';
    ctx.stroke();

    ctx.restore();
  }

  // Central aperture border ring
  if (currentAperture > 1.0) {
    ctx.beginPath();
    for (let i = 0; i < blades; i++) {
      const a = i * baseAngle + bladeAngleOffset;
      const x = Math.cos(a) * currentAperture;
      const y = Math.sin(a) * currentAperture;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  ctx.restore();
}
```

---

## 6. Morphing Shape State Machine (Checkmark $\to$ Spinner $\to$ Van $\to$ Gift)

Continuous-take films morph iconic silhouettes without breaking continuity by maintaining an equal number of parametric Bezier control points across all key figures ($N = 64$ points).

```javascript
/**
 * Normalized 64-point cubic spline morph interpolator
 */
export class MorphShapeStateMachine {
  constructor() {
    this.states = new Map();
  }

  registerState(name, pointList64) {
    if (pointList64.length !== 64) {
      throw new Error(`Morph points must be normalized to exactly 64 points. Received ${pointList64.length}`);
    }
    this.states.set(name, pointList64);
  }

  /**
   * Pure-time interpolation between state sequence
   * @param {Array<{state: string, tStart: number, tEnd: number, k?: number, zeta?: number}>} timeline
   * @param {number} t
   */
  evaluate(timeline, t) {
    for (let i = 0; i < timeline.length - 1; i++) {
      const current = timeline[i];
      const next = timeline[i + 1];

      if (t >= current.tStart && t < next.tStart) {
        const fromPts = this.states.get(current.state);
        const toPts = this.states.get(next.state);
        
        const transitionDuration = next.tStart - current.tStart;
        const progress = (t - current.tStart) / transitionDuration;
        
        // Spring-eased morph factor
        const springFactor = springStep(progress * 1.5, current.k || 200, current.zeta || 0.78);
        const factor = Math.min(1.0, Math.max(0.0, springFactor));

        return this.interpolatePoints(fromPts, toPts, factor);
      }
    }

    // Default to last registered state
    const last = timeline[timeline.length - 1];
    return this.states.get(last.state);
  }

  interpolatePoints(ptsA, ptsB, factor) {
    const result = new Array(ptsA.length);
    for (let i = 0; i < ptsA.length; i++) {
      result[i] = {
        x: ptsA[i].x + (ptsB[i].x - ptsA[i].x) * factor,
        y: ptsA[i].y + (ptsB[i].y - ptsA[i].y) * factor,
      };
    }
    return result;
  }

  draw(ctx, points, cx, cy, scale = 1.0, fillStyle = '#000000') {
    if (!points || points.length === 0) return;
    
    ctx.save();
    ctx.translate(cx, cy);
    ctx.scale(scale, scale);
    ctx.fillStyle = fillStyle;

    ctx.beginPath();
    ctx.moveTo(points[0].x, points[0].y);
    for (let i = 1; i < points.length; i++) {
      ctx.lineTo(points[i].x, points[i].y);
    }
    ctx.closePath();
    ctx.fill();

    ctx.restore();
  }
}
```

---

## 7. Screen-Studio Zoom Handoffs

Transition seamlessly from a 2D micro-UI component to a macroscopic 3D studio device perspective without matrix disjunctions:

```javascript
/**
 * Coordinate-space camera handoff matching tangent velocity
 * @param {number} t - Current timestamp
 * @param {number} tHandoff - Timestamp when micro transforms to studio macro
 */
export function calculateCameraMatrix(t, tHandoff) {
  const dt = t - tHandoff;
  
  if (dt < 0) {
    // Micro UI Mode: 2D flat scale
    const microScale = springStep(t, 240, 0.85);
    return {
      scale: 1.0 + microScale * 0.05,
      pitch: 0,
      yaw: 0,
      translateX: 0,
      translateY: 0,
      glassReflectivity: 0.2
    };
  } else {
    // Studio Perspective Mode: Smooth tilt and pull back
    const pullBack = springStep(dt, 160, 0.72);
    return {
      scale: 1.05 - pullBack * 0.45,
      pitch: pullBack * 18.5,             // Tilt back 18.5 degrees
      yaw: Math.sin(dt * 0.8) * 4.0,       // Gentle camera orbit
      translateX: -pullBack * 120,        // Shift to asymmetric studio composition
      translateY: pullBack * 40,
      glassReflectivity: 0.2 + pullBack * 0.65
    };
  }
}
```

---

## 8. EBU R128 Audio Mastering Pipeline

1. **Beat-Grid Synchronization**:
   - $BPM = 120 \implies 1 \text{ beat} = 0.500\text{s}$.
   - All visual transitions occur precisely on $1/4$ or $1/8$ beat subdivisions.
2. **Sidechain Ducking**:
   - Music dips $-4.5\text{dB}$ with an immediate $15\text{ms}$ attack and $350\text{ms}$ exponential release on mechanical snaps and bass impacts.
3. **Target Standard**:
   - Integrated Loudness: **-14.0 LUFS** (±0.5 LUFS).
   - Maximum True Peak: **-1.0 dBTP**.
   - Loudness Range (LRA): $\le 7.0$ LU.

### Two-Pass FFmpeg Audio Mastering Script
```bash
#!/usr/bin/env bash
set -euo pipefail

INPUT_AUDIO="raw_mix.wav"
OUTPUT_AUDIO="mastered_audio.wav"

# Pass 1: Analyze Integrated Loudness and Dynamic Range
echo "=== PASS 1: Analyzing Loudness Metrics ==="
ffmpeg -i "$INPUT_AUDIO" -af loudnorm=I=-14:TP=-1.0:LRA=7:print_format=json -f null - 2> loudnorm_stats.json

# Parse JSON parameters
MEASURED_I=$(grep "input_i" loudnorm_stats.json | tr -d '", ' | cut -d: -f2)
MEASURED_TP=$(grep "input_tp" loudnorm_stats.json | tr -d '", ' | cut -d: -f2)
MEASURED_LRA=$(grep "input_lra" loudnorm_stats.json | tr -d '", ' | cut -d: -f2)
MEASURED_THRESH=$(grep "input_thresh" loudnorm_stats.json | tr -d '", ' | cut -d: -f2)
TARGET_OFFSET=$(grep "target_offset" loudnorm_stats.json | tr -d '", ' | cut -d: -f2)

# Pass 2: Apply Two-Pass Linear Normalization
echo "=== PASS 2: Conforming to EBU R128 (-14 LUFS, -1.0 dBTP) ==="
ffmpeg -y -i "$INPUT_AUDIO" -af \
  "loudnorm=I=-14:TP=-1.0:LRA=7:measured_I=${MEASURED_I}:measured_TP=${MEASURED_TP}:measured_LRA=${MEASURED_LRA}:measured_thresh=${MEASURED_THRESH}:offset=${TARGET_OFFSET}:linear=true" \
  -ar 48000 -c:a pcm_s24le "$OUTPUT_AUDIO"

echo "Audio mastering complete: $OUTPUT_AUDIO"
```

---

## 9. Parallel Playwright Headless Renderer & Loop Validation

Pipes uncompressed frames directly into FFmpeg stdin with zero disk I/O bottlenecks and validates loop seamlessness:

```javascript
// render.mjs - Parallel deterministic frame exporter
import { chromium } from 'playwright';
import { spawn } from 'child_process';
import fs from 'fs';

const CONFIG = {
  url: 'http://localhost:3000',
  width: 1920,
  height: 1080,
  fps: 60,
  duration: 12.0,
  audioPath: 'mastered_audio.wav',
  outputPath: 'keynote_launch_film.mp4',
};

async function render() {
  const totalFrames = Math.round(CONFIG.duration * CONFIG.fps);
  console.log(`Starting render: ${totalFrames} frames @ ${CONFIG.fps} FPS`);

  const browser = await chromium.launch({
    args: ['--enable-gpu', '--use-gl=angle', '--no-sandbox']
  });

  const page = await browser.newPage({
    viewport: { width: CONFIG.width, height: CONFIG.height }
  });

  await page.goto(CONFIG.url, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);

  // Spawn FFmpeg child process
  const ffmpegArgs = [
    '-y',
    '-f', 'image2pipe',
    '-vcodec', 'png',
    '-r', String(CONFIG.fps),
    '-i', '-',
    '-i', CONFIG.audioPath,
    '-c:v', 'libx264',
    '-preset', 'slow',
    '-crf', '16',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '320k',
    '-shortest',
    CONFIG.outputPath
  ];

  const ffmpeg = spawn('ffmpeg', ffmpegArgs);
  ffmpeg.stderr.on('data', (d) => process.stderr.write(d));

  let firstFrameBuffer = null;
  let lastFrameBuffer = null;

  for (let frame = 0; frame < totalFrames; frame++) {
    const t = frame / CONFIG.fps;
    
    // Evaluate exact timestamp inside client context
    await page.evaluate((time) => window.__KEYNOTE_ENGINE__.seek(time), t);

    const buffer = await page.screenshot({ type: 'png', omitBackground: false });

    if (frame === 0) firstFrameBuffer = buffer;
    if (frame === totalFrames - 1) lastFrameBuffer = buffer;

    ffmpeg.stdin.write(buffer);
    
    if (frame % 60 === 0) {
      console.log(`Rendered frame ${frame}/${totalFrames} (${((frame / totalFrames) * 100).toFixed(1)}%)`);
    }
  }

  ffmpeg.stdin.end();
  await new Promise((resolve) => ffmpeg.on('close', resolve));
  await browser.close();

  // Validate seamless loop continuity
  validateLoopSeamlessness(firstFrameBuffer, lastFrameBuffer);
  console.log(`Film successfully exported to ${CONFIG.outputPath}`);
}

function validateLoopSeamlessness(bufA, bufB) {
  if (!bufA || !bufB) return;
  
  // Compare raw buffer sizes or sample decoded bytes
  let diffCount = 0;
  const sampleLength = Math.min(bufA.length, bufB.length);
  for (let i = 0; i < sampleLength; i += 4) {
    if (Math.abs(bufA[i] - bufB[i]) > 3) {
      diffCount++;
    }
  }

  const deltaRatio = diffCount / (sampleLength / 4);
  console.log(`Loop boundary delta ratio: ${(deltaRatio * 100).toFixed(4)}%`);
  
  if (deltaRatio > 0.005) {
    console.warn(`WARNING: Loop delta exceeds continuous threshold (> 0.5% disparity)`);
  } else {
    console.log(`PASS: Seamless loop verified.`);
  }
}

render().catch(console.error);
```
