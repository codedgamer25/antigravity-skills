# Formats

One rule outranks everything here: **the reference and every candidate must travel the same capture path.** Same tool, same viewport, same `--full-page` setting, same aspect ratio within about 5%. A viewport crop scored against a full-page screenshot measures your capture flags, not your design, and it will send the loop chasing a layout error that does not exist.

`capture.py` detects the format from the source and always writes a normalised PNG: alpha flattened onto white (a transparent export otherwise reads as black ink and wrecks every ratio) and height clamped to 1998px so `Read` never rejects it.

## HTML

```bash
python "$SKILL_ROOT/scripts/capture.py" poster.html --out v1.png --width 800 --height 1000
```

- `--width`/`--height` are the viewport. Set them to the reference's aspect ratio, not to a default.
- `--full-page` captures the whole scroll height. Use it for landing pages; then capture the reference the same way, or the comparison is meaningless.
- Webfonts and CSS transitions settle *after* load, not on it. The script already waits for network idle plus `--wait 900`; raise `--wait` to 2000+ if the first capture shows fallback type or a mid-transition state.
- `--scale 2` for retina detail when the reference is a high-DPI export. Texture scores are sensitive to this.
- Prefer HTML you wrote over generated imagery. The loop can only repair what you can edit.

## SVG

Same path as HTML. Give the root `<svg>` an explicit `width`/`height` or a `viewBox` plus CSS sizing — an intrinsically sized SVG renders small in the top-left corner and measures as a mostly-empty page with enormous margins.

## Live URLs

```bash
python "$SKILL_ROOT/scripts/capture.py" "https://example.com" --out ref.png --width 1440 --full-page
```

- Cookie banners, chat widgets and sticky headers occlude the design and land in the palette as off-brand colour. Capture, `Read` the PNG, and if something is covering the page, screenshot a specific section instead or dismiss it in a page that you control.
- Login walls and region locks cannot be captured. Ask the user for an export rather than retrying.
- `--dark` sets `prefers-color-scheme: dark` when the reference is a dark-mode capture.
- **Do not capture from an already-open preview pane.** A hidden or backgrounded pane throttles `requestAnimationFrame`, which holds stale colours through a theme change and fabricates contrast differences that do not exist in a real render. `capture.py` launches its own headless Chromium for exactly this reason.
- **Do not run a production build while a dev server is serving the URL you are capturing.** A shared build directory leaves the dev server 404-ing its own chunks, and the page then measures as unstyled — a catastrophic, entirely fictitious layout failure.

## Stills

An image source is just normalised and copied. This is the path for a reference the user pasted, a Savee/Refero grab, or a rendered export from another tool. Nothing is inferred and nothing is resized except an over-tall image.

## Decks

Export each slide to PNG, then run **one loop per slide** against its matching reference slide — slides differ in density by design, so scoring a title slide against a content slide guarantees a false failure. If the user wants one style verdict, loop the master/template slide only and treat the rest as applications of the converged DNA.

## Video

```bash
python "$SKILL_ROOT/scripts/capture.py" clip.mp4 --out-dir frames/ --frames 9
```

Samples 9 evenly spaced stills (skipping the first and last 4% — fades are not the design) plus a 3-column contact sheet, and prints every path as JSON.

- `Read` the contact sheet first to judge the arc in one image, then `Read` individual frames.
- Motion DNA is judged on held frames. Score frame-to-frame: `init` against the reference's key frame and `record` the corresponding candidate frame, or run the loop on the contact sheets when both have the same frame count and aspect.
- Frames land at 1280px wide with `-2` height, so aspect is preserved automatically.
- ffmpeg is invoked with list-form arguments, never a shell string, so Windows paths and timestamps survive intact. Keep it that way if you extend the script.

## Aspect mismatch

If the reference and the deliverable genuinely differ in shape — a square reference, a 16:9 deliverable — the loop still works, because margins, coverage and dominance are all fractions. But `grid.rows` and `density` will carry real, unfixable offsets. Say so at `init`, lower `--floor` for `density` deliberately by lowering the global floor, and note the compromise in delivery instead of iterating against a gap that geometry created.
