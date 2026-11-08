# Named layouts

Ratios tell an agent how a design is proportioned. They do not tell it what to build. A named layout closes that gap: it is a composition an agent can construct cold, in a format the DNA has never seen, and land inside the gate.

This is the field that turns a measurement into a look you can ask for by name.

## Anatomy

```json
{
  "name": "stack-left",
  "when": "The default. Any artefact whose job is a headline plus a list.",
  "recipe": [
    "Flood the frame with `ground`.",
    "Set a 9% margin left and top, 25% right, 27% bottom.",
    "Place the display block at the top margin, ragged right, two lines max.",
    "Drop one 4% gap, then the body list at 1.75 line-height, one item per line.",
    "Close with a 10px `ink` rule at 55% width, 3.5% below the list."
  ],
  "notes": "The right margin is wide on purpose: the rag is the composition."
}
```

**`name`** — short, concrete, and about shape or behaviour: `stack-left`, `single-statement`, `split-60`, `full-bleed-caption`. Not `layout-1`, not `hero`. It will appear in requests ("do the split-60 one"), so it has to be sayable.

**`when`** — the trigger, written so an agent choosing between three layouts picks right on the first read. Say what the content *is*, not what it looks like: "one line of copy and nothing else" beats "for dramatic impact".

**`recipe`** — ordered construction steps, top of the frame downward. Each step places one thing.

**`notes`** — intent and known deviations. This is where a rule earns its authority; a constraint with a reason survives, a constraint without one gets optimised away by the next agent.

## Rules for recipes

- **Fractions, not pixels.** `9% margin`, `55% width`, `1.75 line-height`. Pixels are format-specific and the DNA is not. The one exception is a hairline whose absolute weight is the point — say `10px rule` and mean it.
- **Role names, not hexes.** `` `ground` ``, `` `ink` ``. If a recipe hardcodes `#D9F24B`, a palette revision leaves it stale and nothing catches it.
- **One thing per step.** A step that places three blocks cannot be followed partially, and partial following is what actually happens.
- **Buildable cold.** Assume the agent reading it has never seen the reference. If a step needs the image to make sense, it is a note, not a step.
- **Name the deviation.** If a layout knowingly lands outside the DNA on one dimension — a single-line cover will always undershoot ink coverage — say so in the recipe or notes. Otherwise every future run treats it as a failure and iterates against geometry it cannot change.

## How many

Two to four. One is not a system; it means the look has never been tested against a second problem. More than four usually means several looks wearing one name — check whether the recipes actually share the palette rules and margins, and split the DNA if they do not.

Cover the shapes the format range demands: a dense one, a sparse one, and whatever the user's actual pipeline needs most.

## Good and bad

**Bad:**

> `name`: "hero"
> `when`: "For maximum impact when you want to grab attention."
> `recipe`: ["Big bold headline", "Supporting text below", "Use the brand colours", "Keep it clean and modern"]

Nothing here is measurable, nothing is placed, and "use the brand colours" restates the palette table. An agent building from this will produce something different every time — which is the exact failure the DNA exists to prevent.

**Good:**

> `name`: "split-60"
> `when`: "Two competing subjects — a product and its claim, a speaker and a date."
> `recipe`: ["Fill the top 60% with `ground`, the bottom 40% with `ink`.", "Display type in the upper block, bottom-aligned to the split, 6% from the left margin.", "Body copy in the lower block in `ground`, top-aligned to the split, same left margin.", "No rule at the split — the colour change is the divider."]
> `notes`: "Edge anisotropy drops toward 1 here because the split is a single horizontal edge. Expected; do not add texture to compensate."

Every step places something at a stated position, in role colours, in fractions — and the note pre-empts the one metric that will look wrong.

## Validating a layout

Build it, capture it, check it:

```bash
python "$SKILL_ROOT/scripts/dna.py" check --dna dna.json --candidate split-60.png
```

A layout that cannot pass its own DNA is either written wrong or is a second look. Fix the recipe, or take the layout out and give it its own DNA. Do not lower the gate to admit it.
