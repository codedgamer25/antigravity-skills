# Grades — the seven-segment arc

Measured from per-frame mean RGB at 20fps, black frames (mean luma <18) excluded so the
19% blackout runtime doesn't drag every number toward zero.

| # | Range | Frames | Mean sat | p90 sat | Mean value | Mean RGB | Character |
|---|---|---|---|---|---|---|---|
| 1 | 0:00-1:00 | 663 | **48.1%** | 94.3% | 42.2% | `#5A443A` | Warm, loudest saturation in the mix |
| 2 | 1:00-7:00 | 6076 | 43.0% | 84.3% | 38.2% | `#615047` | Amber/brown body; the climax lives here |
| 3 | 7:00-11:00 | 3927 | 40.2% | 87.6% | 39.8% | `#705D53` | Same family, lifted a little |
| 4 | 11:00-13:30 | 2801 | 21.9% | 52.8% | **60.1%** | `#89807F` | Draining; brightest segment, faint magenta |
| 5 | 13:30-18:30 | 5056 | **14.9%** | 50.9% | 40.2% | `#636163` | Near-monochrome trough |
| 6 | 18:30-20:00 | 1615 | 30.1% | 62.4% | 45.8% | `#6A6C79` | Cool blue-violet recovery |
| 7 | 20:00-end | 242 | 47.2% | 72.8% | 38.2% | `#504E55` | Saturation returns, then 43s of black |

## Reading the arc

The shape is a **descent to monochrome and back**: 48 → 43 → 40 → 22 → 15 → 30 → 47.
Segment 5 is the emotional floor, and it is reached by desaturation rather than by
darkening — value actually *peaks* at segment 4 (60%) on the way down. Brightness and
colour move independently.

30-second hue sampling shows the mechanism inside each segment:

```
0:00-11:00   hue 11-34  (orange/amber), sat 24-72%   warm act
11:00-13:30  hue 305-338 (magenta/pink), sat 6-31%   hinge — cool tints enter as sat falls
14:00-18:00  sat 0-4%                                grey act, hue meaningless
18:30-19:30  hue 222-249 (blue-violet), sat 6-16%    cool act
20:00-end    value 16% → 0%                          fade out
```

## Applying to your own track

Pick the segment matching your section's energy — don't apply the whole arc to a
three-minute song. If the track has one climax, use segment 2 for the body and segment 5
for the breakdown.

Two rules that matter more than the exact hex values:

- **Grade per clip, not per timeline.** p90 saturation stays 51-94% in every segment,
  including the 15% trough. Individual shots stay vivid; only the *average* drains. A
  timeline-wide desaturation gives you a flat, dead grey instead.
- **Move saturation, hold value.** Value only varies 38-60% across the entire 21 minutes.
  Resist darkening to signal mood; pull colour instead.
