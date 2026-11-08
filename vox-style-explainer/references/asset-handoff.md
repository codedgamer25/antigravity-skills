# Asset handoff

The one manual step in the pipeline. Getting it right once costs a few minutes; getting it wrong means discovering missing assets in phase 7, after the components are already written.

## Why it is manual

Image generation is not reachable from here. See the Asset reality check in [SKILL.md](../SKILL.md) for what was actually tested — the short version is that a ChatGPT *subscription* carries no API scopes, so the tokens that work fine for chat return `401 Missing scopes: api.model.images.request` at `/v1/images/generations`.

That is fine. The user already has an image tool with a UI. Treat the handoff as a scheduled part of phase 4, not as a blocker: hand over one list, get one folder back.

## Writing the prompts

**You write these, not the user.** Deriving a picture from a sentence is the work; asking the user what the image should be hands the hard part back. Fill `midground_prompt` and `foreground_prompt` for every beat before the handoff.

Start from the line's most concrete noun. If the line has none, the beat needs a stand-in — this style leans on physical objects for abstractions rather than on charts or icons:

| Abstraction in the line | Concrete stand-in |
|---|---|
| inflation, prices rising | a supermarket receipt, a price tag, a till display |
| debt, deficit | a stack of banded notes, a ledger page |
| a treaty, an agreement | two figures at a lectern, a signed page |
| a trade collapse | an idle crane, an empty container yard |
| a decision, a policy | the building it came out of, shot front-on |

Then assemble the prompt from a fixed skeleton, in this order:

```
<subject>, <pose/framing>, <lighting>, <background>, <format>
```

Three of those five must be **identical in every prompt in the film**, because that is what makes eight separately-generated assets look like one set:

- **lighting** — pick one and repeat it verbatim, e.g. `flat even daylight, no hard shadows`
- **background** — always `plain background, transparent PNG`
- **format** — always `full body, feet visible, headroom above the head` for figures

Only `<subject>` and `<pose/framing>` change per asset. Worked derivation:

> `vo_line`: *"When it closed, freight rates tripled overnight."*
> Concrete noun: the ship. Midground subject is the tanker; the beat's payoff (`tripled`) is a counter, not an image.
> `midground_prompt`: `oil tanker, side profile at eye level, flat even daylight no hard shadows, plain background, transparent PNG`
> `foreground_prompt`: `ocean waves seen head-on from just above the waterline, flat even daylight, alpha channel, .webm`

Do **not** put these in a prompt: the word *halftone* (phase 4 does it deterministically), a colour palette (the midground is dithered to pure ink), a named living person's likeness unless the user asked for it, or any styling that names a publisher or artist.

## Give the user one list, not a conversation

After the beat sheet is confirmed, emit every asset as a single copyable block — one line per file, with its prompt and its destination path. Do not drip-feed requests scene by scene; the user is going to sit in one tab and generate them in a batch.

```
public/scenes/scene-01-summit/envoy-a.png
  full-body photo of a diplomat at a lectern, three-quarter view, neutral
  expression, plain background, transparent PNG, feet visible

public/scenes/scene-01-summit/ministry.png
  government ministry facade, front-on, flat midday light, transparent PNG
```

The prompts are the ones you authored into the `midground_prompt` / `foreground_prompt` columns, reproduced verbatim — which is why those columns exist. An asset regenerated three weeks later has to match the ones beside it, and the prompt is the only record of what it was supposed to be.

Close the handoff with the two things the user needs to know: that the paths are exact and the folders already exist, and that they should say when the folder is done rather than reporting file by file.

## What to ask the image tool for

| Ask for | Not |
|---|---|
| Transparent PNG, alpha channel | "white background" — that is not transparency |
| Full body, feet included, headroom | Tight crops. The foreground hides the lower body; you cannot occlude what was cropped out |
| Plain, even lighting | Dramatic side light. The halftone dither turns hard shadows into black mud |
| Ordinary colour photo or illustration | **Halftone.** Phase 4 does that deterministically; per-asset halftoning drifts between assets |
| ≥ 1200 px on the long edge | 512 px. Figures get scaled well past 100% in a 1920-wide frame |
| Neutral or slightly turned pose | Anything with motion blur or an outstretched limb crossing the frame edge |

If the tool refuses transparency, ask for a flat single-colour background and remove it afterwards — `rembg`, `remove.bg`, or the tool's own eraser. Foregrounds need alpha too, since they occlude the midground.

## Validate before halftoning

```bash
python scripts/check_assets.py --beat-sheet beat-sheet.csv --public public
```

Checks every `midground_asset` and `foreground_asset` in the beat sheet against the folder tree and reports, per file: missing, no alpha channel, fully-opaque alpha, too small, or OK. Run it the moment the folder comes back — it is the difference between one round trip and three.

Only then run phase 4:

```bash
python scripts/halftone.py public/scenes/*/*.png
```

`halftone.py` writes `<stem>-halftone.png` plus `<stem>-halftone-stroke.png` beside each input. **Point components at the `-halftone.png` file, not the original.** The stroke canvas is padded by `stroke-spread + 2` px per side so dilation is not clipped at the edge; the `Cutout` component subtracts that pad, and the script prints the value it used.

## Common failures

| Symptom | Cause |
|---|---|
| The dither covers the whole frame | Source had no alpha. `halftone.py` warns; the warning was skipped |
| Red stroke sits low and right of where `theme.ts` says | Stroke pad not subtracted in `Cutout` |
| Two figures' strokes point the same way | `flipStroke` not set on the right-hand figure |
| A figure's feet float above the foreground | Cropped source. Regenerate; do not fix with `y` |
| One character's dots look coarser than the rest | Assets halftoned in separate runs with different `--dot`. Re-run the whole folder in one command |
| Asset 404s at render but Studio looks fine | Studio is showing a cached frame. Trust the render, and check the id/folder names match the beat sheet |
