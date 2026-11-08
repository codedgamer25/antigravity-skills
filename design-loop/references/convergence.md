# Convergence

The loop's failure mode is not "the design is wrong". It is "the agent declares victory". So the stop condition lives in code, in `loop.py`, and it is not yours to interpret.

## The gate

```
passed = overall >= threshold AND no dimension < floor AND no critic veto
```

Defaults: `threshold` 82, `floor` 65, `max_iterations` 6.

Both halves matter. `overall` is a weighted average, so a design that nails a 0.28-weighted palette can clear 82 while its grid sits at 40 — visibly not the reference. The floor is what stops that. Conversely a design with every dimension at 70 clears the floor but not the gate: uniformly approximate is still not a match.

| Setting | Raise when | Lower when |
|---|---|---|
| `--gate` | the user wants a near-forgery, or the reference is a brand asset (88–92) | the ask is "in the spirit of" (74–78) |
| `--floor` | every dimension is load-bearing, e.g. packaging (70–75) | one dimension is knowingly out of scope, e.g. texture on flat vector (55) |
| `--max-iterations` | the format is complex, e.g. a multi-section page (8–10) | a quick style check (3) |

Set these once, at `init`. **Lowering the gate mid-run to make a candidate pass is falsifying the result.** If the terms were genuinely wrong, say so, start a new run directory, and report both runs.

## Flags

`record` prints these when the ledger detects a pathology. Each demands a specific response.

**`stalled: overall moved +0.4`** — under 1.5 points of gain. You are tuning values inside a structure that is wrong. Stop nudging. Re-read the reference PNG, re-read the `init` briefing, and rebuild the weakest dimension from its numbers rather than adjusting yours.

**`backslid: overall fell -20.5`** — you traded a win for a bigger loss. Keep the fix that worked and redo the one that broke; do not revert the whole iteration, or you will lose the ground the trade bought.

**`regression:palette lost 84.8 while you fixed something else`** — a dimension dropped 5+ points that you were not working on. Almost always a global edit: a changed background, a new font stack, a wrapper that shifted every margin. Find the shared cause; do not patch the symptom in two places.

**`exhausted: iteration budget spent`** — stop. Report honestly (below).

Flags are suppressed on a passing iteration. A design that clears the gate does not need a warning about how it got there.

## One dimension per iteration

Fix the first item in `next move`, capture, record. Nothing else.

This is not tidiness. `next move` is ranked by the overall points a fix would buy, with sub-floor dimensions jumping the queue — so the first item is genuinely the highest-value change available. Changing three things at once means the deltas in the next report attribute to nothing, `regression` cannot find its cause, and you have destroyed the only feedback the loop produces.

## Honest failure

When the budget runs out or the loop stalls past rescue, the deliverable is a truthful near-miss. That is a result. A claimed match is a defect, and it is the exact failure this skill exists to prevent.

Report, in this order:

1. `python "$SKILL_ROOT/scripts/loop.py" status --run "$LOOP_RUN"` — the full ledger, unedited.
2. Final `overall` against the gate, and every dimension still below floor, named.
3. The specific physical gap for each: "the reference runs 14 row bands, the candidate runs 9 — its body copy is set at 1.4x the reference's leading".
4. What you would change next, and why the budget stopped you.
5. Any critic issue left unresolved.

Do not describe the output as "matching", "closely matching", "essentially there", or "close enough" while the last `record` exited `1`. Say what the number is.

## After a pass

```bash
python "$SKILL_ROOT/scripts/loop.py" dna --run "$LOOP_RUN" --json "$LOOP_RUN/dna.json"
```

A converged run has produced two things: the artefact, and a measured description of a look that is now known to be reproducible. The second one is the durable asset — hand `dna.json` to design-dna to turn it into a permanent skill, or the next artefact in this style starts the loop from zero all over again.
