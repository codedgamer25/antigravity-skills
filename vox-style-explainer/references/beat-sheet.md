# Beat sheet

The beat sheet is the single source of truth for the build. Scene folders, component names, scene order, and every duration derive from it. Get it right before scaffolding.

## Columns

| Column | Meaning | Example |
|---|---|---|
| `id` | Scene slug. Becomes the asset folder and the component name. `scene-NN-slug`, zero-padded, ordered. | `scene-03-oil-tanker` |
| `vo_line` | The exact narration sentence for this beat. One sentence, one beat, one scene. | `Oil prices skyrocketed to $116 a barrel.` |
| `midground_asset` | Filename of the halftone cutout(s). Semicolon-separate multiples, in entrance order. | `tanker.png` |
| `foreground_asset` | Filename of the full-colour occluder. Blank means the scene has no foreground. | `ocean-plate.webm` |
| `midground_prompt` | **You author this**, from the `vo_line` — the image-generation prompt the user pastes into their image tool. Also the only record of what the asset was supposed to be, so a regeneration later still matches. | `high-contrast B&W halftone cut-out of an oil tanker, side profile, transparent background` |
| `foreground_prompt` | Same, for the foreground. | `keyed ocean waves, front-on, alpha channel` |
| `transition_out` | How this scene leaves. One of `hard-cut`, `slide-up`, `closer-move`, `paper-wipe`. | `slide-up` |
| `beat_word` | The one word in `vo_line` a visual must land on. Never blank. | `$116` |

Extra columns are fine and ignored by tooling — `notes`, `duration_hint`, `source` all survive round-trips.

## Worked example

A five-beat, ~30-second film on a fictional shipping-lane closure:

| id | vo_line | midground_asset | foreground_asset | transition_out | beat_word |
|---|---|---|---|---|---|
| `scene-01-summit` | `Two governments announced a deal in March.` | `envoy-a.png;envoy-b.png` | `ministry.png` | `hard-cut` | `deal` |
| `scene-02-strait` | `But a single strait carried a fifth of the world's fuel.` | `map-strait.png` | — | `slide-up` | `fifth` |
| `scene-03-tanker` | `When it closed, freight rates tripled overnight.` | `tanker.png` | `ocean-plate.webm` | `closer-move` | `tripled` |
| `scene-04-inflation` | `Shipping costs pushed consumer prices to a decade high.` | `cpi-line.png` | `cargo-crane.png` | `hard-cut` | `decade` |
| `scene-05-close` | `Trade routes rarely fail loudly. They fail quietly, and then all at once.` | `route-map.png` | — | `paper-wipe` | `quietly` |

Note what the `beat_word` column buys: `tripled` in scene 3 is the frame the freight-rate counter finishes counting, and `decade` in scene 4 is the frame the line chart's last point lands. Without it, those two events get eyeballed and always feel a beat late.

## Rules

**One sentence per beat.** A two-sentence beat means the visual has to hold through a clause it does not illustrate, and it always reads as a stall. Split it.

**6–8 beats for 45 seconds.** Fewer and each scene overstays; more and the springs never finish before the cut. If the script yields 14 beats, the script is too long, not the beat sheet.

**Order is final at this step.** Reordering after phase 5 means renaming folders, components, and every asset path. Argue about order now.

**Every `midground_asset` must be nameable before you scaffold.** "Some kind of chart" is not an asset. If you cannot say what the picture is, the beat is not written yet.

**Blank `foreground_asset` is legitimate** — map and chart beats often have no occluder. Two consecutive foreground-less beats, though, will feel flat; alternate them.

## Common mistakes

| Mistake | What goes wrong |
|---|---|
| `beat_word` left blank | Phase 9 falls back to centring the event in the scene; every payoff lands slightly early |
| `beat_word` not present in `vo_line` | `vo_timing.py` errors out rather than guessing — fix the spelling to match the narration exactly, including `$` and digits |
| Two scenes sharing an asset folder | Studio prop saves from one scene silently overwrite the other's |
| `id` renumbered without renaming folders | Assets 404 at render time but Studio shows the last cached frame, so it looks fine until the render |
| Narration written to the visuals | Always the reverse: write the line, then decide what shows it |

## Machine-readable form

`scripts/vo_timing.py` reads the CSV directly. If you would rather work in JSON, the equivalent shape is:

```json
[
  {
    "id": "scene-03-tanker",
    "vo_line": "When it closed, freight rates tripled overnight.",
    "midground_asset": ["tanker.png"],
    "foreground_asset": "ocean-plate.webm",
    "transition_out": "closer-move",
    "beat_word": "tripled"
  }
]
```

Pass `--beat-sheet beats.json` and the script detects the format from the extension.
