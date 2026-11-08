# Extraction

## Choosing the reference

One artefact, in the format the look is most native to. A poster look extracts from a poster, not from a screenshot of a poster on a wall.

Never extract from a moodboard, a collage, or a grid of thumbnails. The measurement will faithfully describe the *collage* — nine column bands, four competing palettes, a texture score dominated by the gaps — and every artefact built from it will be wrong in a way no dimension can name.

| Source | Extract like this |
|---|---|
| Converged design-loop run | `extract --reference "$LOOP_RUN/reference.png" --loop-run "$LOOP_RUN"` — the DNA carries the proof |
| Single reference image | `extract --reference ref.png` — works, but the look is *asserted*, not proven |
| Live site | capture full-page at the reference viewport first, then extract from that PNG |
| Video | capture stills, `Read` the contact sheet, extract from one **held** frame — never a transition |
| Deck | extract from the master/template slide, not a content slide |

## When the user has several references

Measure them all before choosing:

```bash
for f in ref-*.png; do python "$LOOP_SCRIPTS/visual_dna.py" measure "$f" --json "${f%.png}.json"; done
```

Extract from the most representative one, then use the DNA to score the others:

```bash
python "$SKILL_ROOT/scripts/dna.py" check --dna dna.json --candidate ref-2.png
```

This is the sharpest tool in this skill. A sibling reference that scores well confirms the DNA generalises. A sibling that lands below floor on one dimension is telling you that dimension **varies across the look** and is not part of its identity — for example a body of work with consistent colour and wildly different density. Handle it explicitly: note the variance in `palette.rules` or the layout's `notes`, and lower the DNA's `floor` rather than pretending the variance is an error every future artefact must avoid.

Two references that disagree on colour are not one look. Emit two DNAs.

## Roles are a guess

`extract` assigns roles positionally by coverage: largest area becomes `ground`, next becomes `ink`, then `accent`, then `support`. That is right most of the time and wrong in specific, predictable ways:

- A dark design with a large photograph gets the photo's dominant tone as `ground`.
- A two-tone design where the accent is *tiny but load-bearing* (a 1% red rule) may not appear at all — coverage below 0.5% is dropped from the palette entirely. If a colour matters more than its area, add it to `roles` by hand and say so in `palette.rules`; it will not be scored, so the rule text is what carries it.
- Anti-aliased type between a light ground and dark ink can surface a mid-grey. Delete it from `roles`; leave `coverage` alone, since it is measured. `check` still scores it, and reports it as a *missing blend* rather than a missing colour when it is absent — meaning the candidate's ground and ink do not blend to the same tone. The fix is always their hexes or their type size, never adding the blend as a third colour.

Rename freely. Roles are names *you* will use in every layout recipe, so they should mean something in this look's language: `ground`, `ink`, `accent`, `wash`, `signal`.

## What extraction cannot see

The measurement is pixels. These are invisible to it and must be written into the named half or they are lost:

- **Font identity.** It measures the size *ratio*, never the family. Two faces at the same scale measure identically.
- **Copy behaviour** — caps, sentence case, line-length discipline, one-item-per-line lists.
- **Motion and interaction** — transitions, hover states, scroll behaviour.
- **Semantic colour** — that `accent` means "live now" and never "error".
- **Production facts** — stock, finish, bleed, spot colour, print vs screen.
- **Intent** — why the right margin is wide, why nothing is centred. The `forbidden[]` list is where intent survives; a rule with a reason gets followed, a rule without one gets optimised away.

## After extraction

`Read` the reference PNG once more with the draft JSON open. For each measured number, find the thing in the image that produced it. If you cannot — if the draft says 14 row bands and you count 6 blocks — the capture is wrong, or the reference is not what you thought it was. Fix that before writing a single layout.
