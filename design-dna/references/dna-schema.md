# DNA schema

`schema: 1`. Fields marked **M** are measured by `extract` and must not be hand-edited; **Y** are yours to write.

| Field | Type | | Required | Notes |
|---|---|---|---|---|
| `schema` | int | M | yes | must be `1` |
| `name` | string | Y | yes | kebab-case slug; becomes the emitted skill's directory and `name:` |
| `title` | string | Y | yes | human name, used in headings and the description |
| `version` | semver string | Y | yes | bump on every re-emit; see [emission](emission.md) |
| `created` | ISO 8601 | M | yes | set at extraction |
| `brief` | string | Y | no | one sentence: what the look is for |
| `formats` | string[] | Y | warn | formats the look is proven on, e.g. `["poster", "social 1:1"]` |
| `source.reference` | path | M | yes | the measured artefact |
| `source.loop_run` | path | M | no | present when `--loop-run` was passed |
| `source.converged` | bool | M | no | `true` only if that run passed its gate |
| `source.proven_overall` | number | M | no | the passing score |
| `palette.roles` | {role: hex} | M/Y | yes, ≥2 | measured positionally, renamed by you |
| `palette.coverage` | {hex: 0..1} | M | yes | area share of each palette colour |
| `palette.rules` | string[] | Y | warn | how the colours divide the frame |
| `grid.aspect` | number | M | yes | width / height |
| `grid.margins` | {left,right,top,bottom} | M | yes | fractions of each axis |
| `grid.columns` / `grid.rows` | int | M | yes | ink band counts |
| `grid.mass_centroid` | [x, y] | M | yes | ink centre of mass, as fractions |
| `type.scale_ratio` | number | M | yes | tallest row band / median row band |
| `type.dominance` | number | M | yes | largest band's share of all ink |
| `type.families` | {role: string} | Y | warn | `display`, `body`, … — the one thing pixels cannot tell you |
| `type.cases` | {role: string} | Y | no | caps, sentence case, list behaviour |
| `texture.ink_coverage` | number | M | yes | fraction of the frame that is ink |
| `texture.edge_density` | number | M | yes | mean absolute luminance gradient |
| `texture.edge_anisotropy` | number | M | no | horizontal / vertical gradient energy |
| `texture.texture_energy` | number | M | yes | image minus its own box blur |
| `layouts` | object[] | Y | **yes, ≥1** | see [named layouts](named-layouts.md) |
| `forbidden` | string[] | Y | **yes, ≥1** | what the look never does |
| `gate.threshold` | number | Y | yes | overall score the emitted checker demands |
| `gate.floor` | number | Y | yes | per-dimension minimum |
| `measurement` | object | M | yes | the full `visual_dna` measurement of the reference |

## `layouts[]` entries

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | short, memorable, referenced by name in requests |
| `when` | string | yes | the trigger — when an agent should reach for this one |
| `recipe` | string[] | yes | ordered construction steps, top of the frame downward |
| `notes` | string | no | intent, known deviations, the reason behind an odd choice |

## What validation enforces

- Errors: bad slug, missing or malformed measured fields, non-hex colours, coverage outside 0..1, fewer than two palette roles, a layout missing `name`/`when`/`recipe`, **empty `layouts[]`**, **empty `forbidden[]`**, missing `measurement`, non-numeric gate.
- Warnings: empty `palette.rules`, empty `type.families`, empty `formats`, a role whose hex has no measured coverage.

`emit` proceeds on warnings and refuses on errors.

## `measurement` is load-bearing

It is the stored measurement of the reference, and it is what every future artefact is compared against — by `dna.py check` and by the emitted skill's own `check.py`. This is why the emitted package never needs the original image again, and why editing a measured number by hand is not a shortcut but a silent break: the numbers in `SKILL.md` and the numbers in `measurement` would then describe different designs, and only one of them is enforced.

If a measured value is wrong, the capture was wrong. Re-capture, re-extract, re-emit.
