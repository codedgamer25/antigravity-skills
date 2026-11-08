# Effect stack

Apply in this order. Values are measured from the source unless marked *inferred*.

## 0. Timebase — do this first

```
fps           20        exact; every published format is 20fps
frame grid    0.05s     quantise every cut and effect boundary to this
resolution    1280x720  master; 1080p exists but is the same 20fps
pix_fmt       yuv420p
```

Everything else is secondary to the frame rate. A 24 or 30fps render with identical cuts
and grades does not read as this video.

## 1. Per-clip framing (source-inherited, not global)

Measured bar geometry across 100 frames:

| Bar size (of 288px height) | Share of frames | Effective aspect |
|---|---|---|
| ≤3px — none | 69% | 16:9 full frame |
| 4-15px | 2% | ~1.9:1 |
| 16-28px | 15% | ~2.0-2.2:1 |
| 29-40px | 9% | **2.36:1** |
| >40px | 4% | wider |

Side bars (pillarbox) ≥20px on 16% of frames, p90 154px — that's 4:3-era anime windowed
inside 16:9.

**Rule:** leave each clip's native framing alone. Do not normalise, do not add a global
matte. The inconsistency between shots is part of the texture.

## 2. Grade

Per segment — see `grades.md`. Applied per clip, not as one timeline-wide LUT: p90
saturation stays high (84-94%) even in segments whose mean is 15%, so individual shots
keep punch while the section average drains.

## 3. Motion blur and bloom

This is what produces the smeared, aberration-looking frames. Directional/zoom blur along
the dominant motion vector, plus a bloom lift in highlights. *Inferred* — no clean
measurement, but confirmed by the absence of channel separation (below).

Suggested starting point, tune by eye:

```
directional blur   6-14px along motion vector, on the fastest 2-4 frames of a whip
bloom threshold    ~0.75 luma, intensity 0.3-0.6
```

## 4. Grain

```
grain amount   residual std 2.9/255 median  (p10 0.8, p90 6.9)
```

Low. Heaviest on the VHS-transfer shots, near-zero on clean digital anime. Apply per clip
matched to source texture, not as a uniform layer.

Verify a render against the source with:

```bash
python -c "
from PIL import Image, ImageFilter; import numpy as np, sys
im=Image.open(sys.argv[1]).convert('L')
a=np.asarray(im,dtype=np.float32)
b=np.asarray(im.filter(ImageFilter.GaussianBlur(1.5)),dtype=np.float32)
print('grain residual std: %.2f' % (a-b).std())
" frame.jpg
```

## 5. Do not add

- **RGB split / chromatic aberration — absent.** Best-fit horizontal R→B shift was 0px in
  90 of 93 sampled frames (search range ±6px, centre crop, correlation maximum). Re-check
  any render the same way; a non-zero mode means you added something the source doesn't
  have.
- **Global letterbox — absent.** See §1.
- **Heavy film grain — absent.** See §4.
- **Datamosh / glitch blocks — not observed** in any sampled frame.

## Re-deriving the measurements

```bash
# stream properties
ffprobe -v error -select_streams v:0 \
  -show_entries stream=r_frame_rate,width,height,nb_frames -of default=nw=1 video.mp4

# per-frame mean colour + spatial std + luma deltas (full decode, 32x18)
ffmpeg -v error -i video.mp4 -vf "scale=32:18:flags=area" \
  -f rawvideo -pix_fmt rgb24 - | python an.py

# cut list
ffmpeg -v error -i video.mp4 -vf "select='gt(scene,0.30)',metadata=print:file=cuts.txt" \
  -an -f null -

# native-res samples for grain / channel alignment / bar geometry
ffmpeg -v error -i video.mp4 -vf "fps=1/12" -q:v 2 native/n_%03d.jpg
```
