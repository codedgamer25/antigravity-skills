# Dimensions

Six scores, weighted into one `overall`. They are deliberately **separable**: a design with the right colours on the wrong grid must score high on colour and low on layout, so a failing number names exactly one real fix. If two dimensions always move together, the second one is telling you nothing.

| Dimension | Weight | Measures | Tolerance before it hits 0 |
|---|---|---|---|
| `palette` | 0.28 | Are the reference's load-bearing colours present, at roughly its coverage? | colour ΔE00 > 10, or 25 points of coverage gap |
| `color_discipline` | 0.17 | How much candidate area is colour the reference never used? | 20% of the frame off-palette |
| `layout` | 0.20 | Margins, mass centroid, column and row band counts | 12% of the axis per margin; 20% centroid drift |
| `hierarchy` | 0.15 | Size contrast between the display block and a typical one, plus that block's share of ink | 2.3x size-ratio error; 30 points of dominance |
| `density` | 0.12 | Ink coverage and edge count — is the page as full as the reference? | 2.5x ink error; 3.0x edge error |
| `texture` | 0.08 | Surface energy: grain, noise, blur, gradient banding, image detail | 3.3x texture error |

Ratio-level throughout. A 1080px poster and a 1440px landing page built from the same DNA measure alike, which is what makes one gate serve every format.

## What moves each one

**`palette`** — the exact hexes and their area share. Extraction adaptive-quantises to 12 colours, then merges entries closer than ΔE00 6 so anti-aliasing does not read as a new brand colour. Only colours covering ≥0.5% count. A near-miss is worse than an omission here: the report names the missing hex, its share of the reference, and the nearest colour you actually used. Sample it; do not eyeball it.

**`color_discipline`** — the single best slop detector. It ignores what you got right and measures only the area you painted in colours the reference never had: gradients, drop shadows, browser-default link blue, a stock photo, a hover state baked into the screenshot. Deleting is the fix, never adding.

**`layout`** — the frame. Margins are fractions of each axis; the centroid is where the ink's centre of mass sits; band counts come from projection profiles of the ink mask (a "band" is a contiguous run of inked rows or columns, with gutters thinner than 1.5% of the axis bridged and bands thinner than 1.2% dropped). Row bands approximate text lines and blocks; column bands approximate the grid. Low layout with high palette means you kept the colours and invented the structure — rebuild the frame from the reference's numbers instead of nudging padding.

**`hierarchy`** — deliberately colour-blind. `type_scale_proxy` is the tallest row band over the median one: the ratio between display type and body copy. `dominance` is the largest band's share of all ink. Nothing about tone enters this score, so a candidate that is structurally identical but wrongly coloured scores ~100 here and ~0 on palette. That separation is a design decision, not an oversight; it is what lets the fix order be trusted.

**`density`** — content mass, not alignment. Ink coverage is the fraction of pixels perceptually distinct from the background (ΔE00 > 8); edge density is the mean absolute luminance gradient. Both are log-scaled, because doubling the amount of text matters and adding two words does not. Low density with high layout means the frame is right and the page is too empty or too busy — add or cut content, do not re-align it.

**`texture`** — the image minus its own box blur. Catches grain, noise overlays, photographic detail, gradient banding, and heavy compression. Lowest weight, because it is the easiest thing to fake and the least load-bearing; do not chase it while anything else is below floor.

## Diagnostics, not scores

`measure` also emits `ink_bg_contrast`, `ink_tonal_spread`, `chroma`, `edge_anisotropy`, `aspect`, `background`, and the raw band coordinates. These are unscored on purpose — earlier versions scored tonal spread inside `hierarchy`, which let a colour mistake destroy the structure score and sent the loop chasing the wrong fix. Read them when a score is confusing; never argue with the gate using them.

`edge_anisotropy` (horizontal over vertical gradient energy) is the most useful of these: well above 1 means a text-heavy, horizontally banded design; near 1 means an image-led one.

## Cross-checking a suspicious score

```bash
python "$SKILL_ROOT/scripts/visual_dna.py" measure reference.png --json ref.json
python "$SKILL_ROOT/scripts/visual_dna.py" measure candidate.png --json cand.json
```

Diff `grid.rows`, `margins`, `type_scale_proxy` and `palette` coverages directly. If the two measurements agree and the score still looks wrong, the capture differs — check aspect ratio and `--full-page` before doubting the metric.
