---
version: 0.1.0
name: design-loop
description: |
  Iterate a design against a gold-standard reference until it objectively matches, using deterministic visual measurement instead of self-assessment. Deconstructs the reference into grid, colour, type and texture ratios, scores every candidate on six separable dimensions, ranks the single next fix, and refuses to call it a match until both an overall gate and a per-dimension floor pass. Works on HTML, SVG, live URLs, stills, and video. Use when: "make this match the reference", "why doesn't my design look like this", "recreate this poster/landing page/deck in that style", "keep iterating until it's right", or any request that supplies an inspiration image and asks for output in its style. Chain into design-dna to make a converged look permanent and reusable. NOT for: designing with no reference (use frontend-design), generating images from prompts (use higgsfield-generate), reproducing a look already codified (use design-dna), or functional/accessibility testing (use webapp-testing).
argument-hint: "[reference image, URL, or design to match] [what to build]"
allowed-tools: Bash, Read, Write, Edit, Glob, Agent
---

# Design Loop

Design output drifts because nobody measures it. This skill replaces "that looks close" with a score per dimension, a floor, and a ranked next move — then keeps looping until the numbers agree with the reference.

**You do not decide when the design matches. `loop.py` does.** Announce a match only when it prints `PASS`. Everything else in this file exists to make that gate meaningful.

## Bootstrap

1. Resolve `SKILL_ROOT` to the absolute directory containing this SKILL.md, then create a run directory:

   ```bash
   LOOP_RUN="${PWD}/design-loop-run"
   mkdir -p "${LOOP_RUN}"
   ```

2. On Windows, run `python`, not `python3` — the `python3` command is the Microsoft Store stub and will not execute these scripts. Substitute it in every command below.
3. Preflight only what the source format needs:

   ```bash
   python -c "import numpy, PIL; print('core ok')"
   python -c "import playwright; print('web ok')"   # html, svg, url sources
   ffprobe -version >/dev/null && echo "video ok"    # video sources
   ```

   Missing pieces: `pip install pillow numpy`, `pip install playwright && python -m playwright install chromium`. Never install system packages without the user's permission; ffmpeg has no pip fallback, so ask.

## Script mapping

| Operation | Command |
|---|---|
| Render any artefact to a measurable PNG | `python "$SKILL_ROOT/scripts/capture.py" SOURCE --out shot.png` |
| Sample a video into stills + contact sheet | `python "$SKILL_ROOT/scripts/capture.py" clip.mp4 --out-dir frames/` |
| Measure one image | `python "$SKILL_ROOT/scripts/visual_dna.py" measure IMG.png` |
| Score candidate against reference, one shot | `python "$SKILL_ROOT/scripts/visual_dna.py" compare REF.png CAND.png` |
| Open a run and register the gold standard | `python "$SKILL_ROOT/scripts/loop.py" init --run "$LOOP_RUN" --reference REF.png` |
| Score an iteration into the ledger | `python "$SKILL_ROOT/scripts/loop.py" record --run "$LOOP_RUN" --candidate CAND.png` |
| Re-read the ledger and the next move | `python "$SKILL_ROOT/scripts/loop.py" status --run "$LOOP_RUN"` |
| Emit the converged DNA for design-dna | `python "$SKILL_ROOT/scripts/loop.py" dna --run "$LOOP_RUN" --json dna.json` |

`record` exits `0` on `PASS` and `1` on `FAIL`, so it is safe to drive from a shell conditional. Never edit `run.json` by hand — it is the ledger the gate reads.

## Core loop

1. **Get the gold standard.** One reference the user actually endorses. Accept an image, a URL, or a file; normalise it first so the reference and every candidate travel the same path:

   ```bash
   python "$SKILL_ROOT/scripts/capture.py" "<reference>" --out "$LOOP_RUN/reference.png"
   ```

   If the user offers several references, ask which single one is the standard, or capture each and treat the rest as secondary evidence. Two gold standards means no gate.

2. **Read the reference yourself.** `Read` the PNG. The measurement gives you ratios; your eyes give you the intent — what the design is *doing*, what it refuses to do. Do this before you write a line of markup.

3. **Register it.** This prints the DNA briefing you will build against:

   ```bash
   python "$SKILL_ROOT/scripts/loop.py" init --run "$LOOP_RUN" \
     --reference "$LOOP_RUN/reference.png" --brief "<what the user asked for>" \
     --format poster --max-iterations 6
   ```

   Raise `--gate` above 82 only when the user wants a near-forgery; lower it for "in the spirit of". Never lower it mid-run to make a candidate pass.

4. **Build from the briefing, not from memory.** Copy the printed hexes, margins, band counts, size ratio and ink coverage into the artefact. Read [dimensions](references/dimensions.md) for what each number governs. Prefer HTML/SVG you control over generated imagery — the loop can only fix what you can edit.

5. **Capture and record.** Same capture path as the reference, then:

   ```bash
   python "$SKILL_ROOT/scripts/capture.py" "$LOOP_RUN/v1.html" --out "$LOOP_RUN/v1.png" --width 800 --height 1000
   python "$SKILL_ROOT/scripts/loop.py" record --run "$LOOP_RUN" --candidate "$LOOP_RUN/v1.png" \
     --changed "first build from the DNA briefing"
   ```

   Always pass `--changed`. A ledger of scores with no record of what moved them is a ledger you cannot learn from.

6. **Critique with a sub-agent, then repair.** Run the critic from [critic-protocol](references/critic-protocol.md) and pass its verdict back through `record --critic`. Then fix **only the first item in `next move`**. One dimension per iteration; a change that touches everything teaches you nothing.

7. **Loop from step 5** until `PASS`, or until the ledger says stop. Read [convergence](references/convergence.md) for the exact stop rules and what each flag demands.

8. **Hand off.** On `PASS`, offer design-dna so the look survives past this artefact:

   ```bash
   python "$SKILL_ROOT/scripts/loop.py" dna --run "$LOOP_RUN" --json "$LOOP_RUN/dna.json"
   ```

## The critic

Metrics catch ratios; they do not catch "the eye lands in the wrong place". So each iteration also gets a fresh pair of eyes — a sub-agent that sees the reference and the candidate side by side with no memory of how hard you worked on the candidate.

The critic **can only veto**. A `fail` verdict blocks the gate; a `pass` verdict never lifts a design over a metric floor. This asymmetry is the point: it is why the loop cannot talk itself into finishing. Exact prompt and verdict schema live in [critic-protocol](references/critic-protocol.md).

If sub-agents are unavailable, do the critique inline — but `Read` both PNGs again in that same turn first, and write the verdict JSON to disk before scoring, so the judgement is committed before you see whether it was convenient.

## Reading the report

```
  palette           84.8        ###################...
  layout            56.0        ############..........  < floor
  density           35.9        ########..............  < floor
  -> next move, weakest first:
     layout (56): rebuild the frame, do not nudge it - copy the reference margins ...
```

- `< floor` — the gate cannot pass while this is showing, no matter how high `overall` climbs.
- `next move` is ranked by the overall points a fix would buy, with sub-floor dimensions jumping the queue. It is an instruction, not a menu.
- `missing colour #D9F24B (94% of the reference)` — a load-bearing colour is absent. Sample it, do not approximate it.
- Deltas are versus the previous iteration. A dimension that gained while another lost by more is a trade, not progress.

## Invariants

- Reference and candidates must travel the same capture path, at the same aspect ratio. Comparing a full-page screenshot against a viewport crop measures your capture settings, not your design.
- The gate's terms are fixed at `init`. Changing `--gate`, `--floor`, or the reference mid-run resets the run; say so out loud and start a new run directory rather than quietly editing `run.json`.
- One dimension per iteration. Named fix, recorded in `--changed`.
- Scores are ratio-level, so a poster and a website built from the same DNA measure alike. Never compare across two different references in one run.
- The critic never overrides a metric floor, and the metrics never overrule a critic veto.
- Never report a match, "close enough", or "matching the reference" while the last `record` exited `1`.

## Failure policy

- **Capture fails twice** on the same source: report the concrete error and switch format (URL → local HTML, video → contact sheet). Do not hand-write a PNG or fake a measurement.
- **`stalled`** — two iterations, no real gain. Stop tuning values. Rebuild the weakest dimension from the reference geometry.
- **`backslid`** — you traded a win for a loss. Keep the win, redo the loss; do not revert wholesale.
- **`exhausted`** — the iteration budget is spent. Report the honest gap: final scores, which dimensions are below floor, and what you would change next. A truthful near-miss is a result; a claimed match is a defect.
- If the reference is unreachable, unreadable, or the user never supplied one, say so and stop. This skill has no meaning without a gold standard.

## Delivery

1. The artefact, plus the final capture PNG.
2. The ledger table from `status` — every iteration, every dimension, the verdict.
3. The final scores with anything below floor named explicitly.
4. What the critic vetoed and how it was resolved.
5. On `PASS`, the `dna.json` path and the offer to codify it with design-dna.

## Reference index

- [Dimensions](references/dimensions.md) — what each of the six scores measures, what moves it, and what it deliberately ignores.
- [Critic protocol](references/critic-protocol.md) — the sub-agent prompt, the verdict JSON schema, and the veto rule.
- [Convergence](references/convergence.md) — gate terms, flags, stop rules, and honest-failure reporting.
- [Formats](references/formats.md) — capture recipes and gotchas for HTML, SVG, live URLs, stills, decks, and video.
