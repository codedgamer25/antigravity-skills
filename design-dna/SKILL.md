---
version: 0.1.0
name: design-dna
description: |
  Turn a look that already works into a permanent, reusable skill. Codifies a design into explicit DNA — palette roles and coverage, grid and margin ratios, type scale, surface energy, named layouts, and an explicit list of what the look never does — then emits a standalone self-checking skill so the same look is reproducible on demand, in any format, without re-deriving it. Use when: "make this our style", "save this look", "turn this into a skill", "keep every future asset consistent with this", or immediately after a design-loop run converges. NOT for: chasing a reference that has not converged yet (use design-loop first), one-off design with no reuse (use frontend-design), or generating imagery from a prompt (use higgsfield-generate).
argument-hint: "[converged design-loop run or reference image] [name for the look]"
allowed-tools: Bash, Read, Write, Edit, Glob
---

# Design DNA

A design that came out right once is luck. This skill converts it into numbers and named recipes, then writes a skill that carries them — so the tenth artefact in a style looks like the first without anybody remembering how the first was made.

Two halves, and both are required:

- **Measured** — palette coverage, margin fractions, band counts, type scale, ink and texture energy. `dna.py extract` fills these; you never type them by hand.
- **Named** — what the colours are *for*, the layouts by name, and the prohibitions. Only you can write these, and `dna.py validate` refuses to emit without them. A DNA with no named layout is a screenshot of some numbers.

## Bootstrap

1. Resolve `SKILL_ROOT` to the absolute directory containing this SKILL.md.
2. On Windows run `python`, not `python3`.
3. `dna.py` needs the measurement core from the design-loop skill. It looks for `visual_dna.py` beside itself, then in `../../design-loop/scripts/`. `validate` and `emit` work without it; `extract` and `check` do not.

   ```bash
   python -c "import numpy, PIL; print('core ok')"
   ```

## Script mapping

| Operation | Command |
|---|---|
| Measure a reference into a DNA draft | `python "$SKILL_ROOT/scripts/dna.py" extract --reference REF.png --name slug` |
| Same, carrying a converged loop's proof | `... extract --reference REF.png --name slug --loop-run RUN` |
| Check a DNA is complete enough to emit | `python "$SKILL_ROOT/scripts/dna.py" validate --dna dna.json` |
| Write the permanent skill package | `python "$SKILL_ROOT/scripts/dna.py" emit --dna dna.json --out-dir DIR` |
| Score an artefact against a DNA | `python "$SKILL_ROOT/scripts/dna.py" check --dna dna.json --candidate CAND.png` |

`validate` and `check` exit `1` on failure. `emit` refuses outright on an invalid DNA rather than writing a half-skill.

## Core workflow

1. **Establish what you are codifying.** The best source is a converged design-loop run: the look is already proven reproducible against a gold standard. A bare reference image works too, but say plainly that it is unproven — nothing has yet demonstrated the look can be rebuilt.

2. **Extract.**

   ```bash
   python "$SKILL_ROOT/scripts/dna.py" extract \
     --reference reference.png --name acid-summit --title "Acid Summit" \
     --brief "<one sentence on what the look is for>" \
     --loop-run "$LOOP_RUN" --out acid-summit-dna.json
   ```

   This measures and stores everything quantitative, including the full reference measurement — which is what lets the emitted skill check itself forever without the original image. Read [extraction](references/extraction.md) for what to do when the reference is a set, a video, or a live site.

3. **Read the reference, then write the named half.** `Read` the reference PNG and edit the JSON: `palette.rules`, `type.families` and `cases`, `formats`, `layouts[]`, `forbidden[]`. Roles come out of extraction positionally by coverage — rename `support` to `accent`, or merge them, if the measurement guessed wrong. [Named layouts](references/named-layouts.md) is the important one; [dna-schema](references/dna-schema.md) is the field-by-field contract.

4. **Validate until clean.**

   ```bash
   python "$SKILL_ROOT/scripts/dna.py" validate --dna acid-summit-dna.json
   ```

   Warnings are advice. Errors are refusals, and the two that catch everyone — empty `layouts[]` and empty `forbidden[]` — are the fields that make the difference between a reusable look and a note-to-self. Write them.

5. **Emit.**

   ```bash
   python "$SKILL_ROOT/scripts/dna.py" emit --dna acid-summit-dna.json \
     --out-dir "$HOME/.claude/skills/acid-summit"
   ```

   Writes `SKILL.md`, `dna.json`, `tokens.css`, `scripts/check.py`, and copies `visual_dna.py` and `capture.py` in so the package survives design-loop being moved or removed. Read [emission](references/emission.md) for what lands where and how to extend it by hand.

6. **Prove the emitted skill.** Before telling the user it is installed, run its own checker against the artefact the DNA came from:

   ```bash
   python "<out-dir>/scripts/check.py" --candidate proven-artefact.png
   ```

   It must exit `0`. A self-checking skill that fails its own source is a broken skill, and the failure is almost always a capture mismatch — same aspect, same tool, same flags.

7. **Tell the user where it lives and what invokes it.** A skill nobody knows about changes nothing. Name the slug, the layouts, and the check command.

## Invariants

- Measured fields are never hand-edited. If a number is wrong, the reference or the capture was wrong — fix that and re-extract. Typing a nicer number into `dna.json` breaks the checker silently, because the stored measurement is what every future artefact is scored against.
- The named half is never auto-generated. Do not invent layouts the reference does not contain, and do not pad `forbidden[]` with generic advice; every prohibition should be something the reference visibly refuses.
- One DNA, one look. A DNA covering "our posters and also our dark-mode dashboard" measures the average of two designs and matches neither. Emit two skills.
- `version` is meaningful. Bump minor for an added layout or format; bump major when a measured value changes, and say what moved and why. The old artefacts were checked against the old numbers.
- The emitted skill's gate is inherited from the DNA. Do not lower it inside the emitted package — that quietly widens the look until it is no look at all.
- Do not promise the emitted skill is Figma, Canva, or design-token-platform output. It is a skill directory plus a CSS file.

## Failure policy

- **`extract` cannot find `visual_dna.py`** — install the design-loop skill beside this one or copy `scripts/visual_dna.py` in. Do not hand-write a measurement block; a fabricated `measurement` makes every future check meaningless.
- **`validate` errors twice on the same field** — you are guessing at the reference instead of reading it. `Read` the PNG again and describe what is actually there.
- **`emit` refuses** — it is refusing an incomplete DNA, which is correct. Fill the fields; do not route around it with a hand-written SKILL.md.
- **The emitted `check.py` fails its own source artefact** — a capture mismatch, not a DNA bug. Compare aspect ratios and capture flags before changing anything in the JSON.
- **Codifying an unproven look** — allowed, and `extract` warns. Say so in delivery: the DNA describes a reference nothing has yet reproduced.

## Delivery

1. The emitted skill's path and slug, plus how a future request triggers it.
2. The layouts by name, with when to use each.
3. The measured summary: palette with coverage, aspect, margins, band counts, type scale.
4. The self-check command, and the result of running it on the source artefact.
5. Whether the look is *proven* (from a converged loop run) or *asserted* (from a bare reference).
6. The `dna.json` path — it is the source of truth, and re-emitting from it is how the skill gets updated.

## Reference index

- [Extraction](references/extraction.md) — choosing the reference, handling sets, video, and live sites, and what extraction cannot see.
- [DNA schema](references/dna-schema.md) — every field, which are measured, which are yours, and what validation enforces.
- [Named layouts](references/named-layouts.md) — how to write a layout that another agent can build from cold.
- [Emission](references/emission.md) — what the emitted package contains, how the self-check works, and how to version it.
