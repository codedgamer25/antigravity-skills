# Emission

`emit` writes a complete, standalone skill. Nothing about it depends on this skill, on the original reference image, or on the loop run that proved it.

```
<out-dir>/
  SKILL.md            generated from the DNA - frontmatter, palette table, structure,
                      type, surface, named layouts, prohibitions, self-check
  dna.json            the source of truth, copied verbatim
  tokens.css          every measured value as a CSS custom property
  scripts/check.py    scores an artefact against dna.json; exits 1 on a fail
  scripts/visual_dna.py   copied in so the package survives design-loop moving
  scripts/capture.py      copied in so the package can render its own output
```

Install by moving the directory under `~/.claude/skills/`. The slug in `name:` is what makes it discoverable, so it should be the phrase a user would actually say.

## The self-check

```bash
python "<skill>/scripts/check.py" --candidate artefact.png
python "<skill>/scripts/check.py" --candidate artefact.png --json report.json
```

It loads `dna.json`, compares the candidate against the stored `measurement`, applies the DNA's own gate, prints a per-dimension bar chart with anything below floor marked, names missing palette colours by hex, and exits `1` on a fail with the fix order.

`check.py` finds the measurement core beside itself first, then falls back to an installed design-loop skill. Both present is fine. Neither present is a clear error, not a silent pass.

This is what makes the look permanent rather than remembered: the emitted skill can refuse its own output.

## Re-emitting

`emit` overwrites `SKILL.md`, `dna.json`, `tokens.css`, and `scripts/check.py`. It does **not** overwrite an existing `visual_dna.py` or `capture.py`, and it leaves any file it did not create alone.

So: **never hand-edit the emitted `SKILL.md`.** Those edits vanish on the next re-emit, usually months later, usually unnoticed. Durable additions go one of two places:

- **Into `dna.json`**, then re-emit — this is the right home for a new layout, a new prohibition, a corrected font name.
- **Into files `emit` does not touch** — `references/*.md`, `templates/*.html`, an example artefact. Reference them from `dna.json` (a layout `notes` field is a fine place) so the generated SKILL.md points at them.

## Versioning

`version` in `dna.json` drives the emitted skill's frontmatter.

| Change | Bump | Also do |
|---|---|---|
| Added a layout, a format, a prohibition | minor | re-emit; nothing built before is invalidated |
| Reworded rules or notes | patch | re-emit |
| A measured value changed (new reference, re-capture, real palette revision) | **major** | re-emit, and say what moved — artefacts built before were checked against different numbers |

A major bump is a genuine event: everything previously produced under this DNA was verified against a gate that no longer exists. Say so plainly rather than letting the look drift one silent re-extraction at a time.

## Extending by hand

Useful additions the generator does not make:

- `templates/<layout>.html` — a working skeleton per named layout, using `tokens.css`. Cheapest possible way to make the next artefact land inside the gate on the first try.
- `references/copy.md` — tone, caps discipline, line-length rules. Extraction cannot see any of it.
- An `examples/` directory with one passing artefact per layout, so a future agent can `Read` a target instead of imagining one.

Keep these outside the four generated files, and mention them from the DNA so the generated SKILL.md links them.

## Chaining back

An emitted skill and design-loop are complementary, not alternatives. When a new artefact in the style fails its own check twice and you cannot see why, run design-loop with the DNA's proven artefact as the gold standard: the loop's per-dimension deltas and ranked fix order will name what the checker can only score.
