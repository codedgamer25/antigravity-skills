# Beat mapping and cut density

From 1324 cut timestamps (ffmpeg `select='gt(scene,0.30)'`, score median 0.45, p90 0.99)
over 1256.4s.

```
overall rate      63.2 cuts/min
median shot       0.30s   (6 frames)
mean shot         0.91s
p10 / p90         0.05s / 2.15s
minimum           0.05s   (1 frame — the floor is exactly one frame)
```

## Shot length histogram (frames at 20fps)

| Length | Count | Share |
|---|---|---|
| **1 fr** (0.05s) | 278 | **21.0%** |
| **2 fr** (0.10s) | 197 | **14.9%** |
| 3 fr (0.15s) | 83 | 6.3% |
| 4 fr (0.20s) | 52 | 3.9% |
| 5 fr (0.25s) | 37 | 2.8% |
| 8 fr (0.40s) | 32 | 2.4% |
| 11 fr (0.55s) | 31 | 2.3% |
| 18 fr (0.90s) | 31 | 2.3% |

Cumulative: **21% ≤1 frame, 42% ≤3 frames, 51% ≤6 frames, 63% ≤12 frames.**

Read the 1-and-2-frame bucket carefully: 36% of all detected intervals are 1-2 frames
long. Those are mostly **not shot changes** — they are black blinks and luma slams landing
inside a held shot (see `transitions.md`). Separate the two when you build a timeline:

- **Shot changes:** intervals >2 frames. Median around 6 frames.
- **Strobe events:** 1-2 frame black or bright inserts, layered on top.

Treating all 1324 as shot changes gives you an incoherent blur of footage.

## Density per minute

| Minute | Cuts | Median shot | Minute | Cuts | Median shot |
|---|---|---|---|---|---|
| 0:00 | 18 | 0.95s | 11:00 | 110 | 0.20s |
| 1:00 | 100 | 0.20s | 12:00 | 79 | 0.35s |
| 2:00 | 45 | 0.50s | 13:00 | 65 | 0.25s |
| 3:00 | 109 | 0.15s | 14:00 | 43 | 0.70s |
| **4:00** | **132** | **0.15s** | 15:00 | 22 | 1.50s |
| 5:00 | 113 | 0.15s | 16:00 | 35 | 0.65s |
| 6:00 | 92 | 0.20s | 17:00 | 82 | 0.15s |
| 7:00 | 36 | 0.85s | 18:00 | 32 | 1.10s |
| 8:00 | 41 | 0.33s | 19:00 | 28 | 0.95s |
| 9:00 | 87 | 0.45s | 20:00 | 10 | 1.30s |
| 10:00 | 45 | 0.48s | | | |

The dynamic range is 13:1 — from 132 cuts/min at 4:00 to 10 at 20:00. Peaks (4:00-6:00,
11:00, 17:00) sit at 0.15s = **3-frame sustained cutting**. Troughs (15:00, 18:00-20:00)
run 1.0-1.5s shots. Never hold one density for a whole section; the contrast is the point.

## Tempo

Do **not** assume a global grid. Best fit across the whole mix is only **44% of cuts at
150 BPM on a 1/16 grid**; alternatives (70.5 BPM on the beat, 31%) fit nearly as well.
It's a multi-song mix with different tempos, and the detector counts strobe events as cuts,
which smears any grid.

Detect tempo **per section** from your own audio, then:

1. Place shot changes on detected onsets.
2. Quantise every boundary to the 0.05s frame grid — off-grid cuts fight the 20fps judder.
3. Set density from the table above for that section's energy.
4. Layer strobe events independently (`transitions.md`); they do not need to sit on onsets.

`librosa` and `scipy` are not installed on this machine. Either install librosa for onset
detection, or use ffmpeg's `astats`/`silencedetect` for a coarser envelope:

```bash
ffmpeg -i track.wav -af "astats=metadata=1:reset=1,ametadata=print:file=levels.txt" -f null -
```
