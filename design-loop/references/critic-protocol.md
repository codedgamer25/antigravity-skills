# Critic protocol

The metrics measure ratios. They cannot see that the eye lands on the wrong element, that the crop cuts a word, or that a layout is technically correct and visually dead. So every iteration also gets a fresh pair of eyes.

## The veto rule

The critic **can only veto**.

- `fail` → the gate fails, whatever the numbers say.
- `pass` → nothing. It never lifts a design over a metric floor, never raises `overall`, never substitutes for a measurement.

This asymmetry is the whole reason the loop terminates honestly. A critic that could approve would eventually approve, because it is the same model that built the candidate.

## Spawning the critic

Run it as a sub-agent so it has no memory of the build. Give it exactly two images and no history:

```
You are a design critic. You have never seen these files before and you have no
stake in either one.

REFERENCE (the gold standard): <absolute path to reference.png>
CANDIDATE (must match it): <absolute path to candidate.png>

Read both images. Then answer only this: if a client asked for the reference and
received the candidate, what would they object to?

Rules:
- Judge the candidate against the reference only. Do not judge whether the
  reference is good, and do not suggest improvements to the reference.
- Ignore content differences (different words, different names, different photo
  subject). Judge structure, colour behaviour, weight, spacing, rhythm, crop.
- Be specific and physical: "the headline sits 40% down, the reference starts it
  at the top margin", not "the hierarchy could be stronger".
- Every issue must be actionable in one edit. No taste notes, no praise.
- If you find nothing a client would object to, verdict is "pass". Do not invent
  an issue to look thorough, and do not pass to be agreeable.

Return ONLY this JSON, no prose around it:
{"verdict": "pass" | "fail",
 "summary": "<one sentence>",
 "issues": ["<specific, physically described, one-edit fix>", ...],
 "worst": "<the single issue to fix first, or null>"}
```

Write the returned JSON to disk, then score it:

```bash
python "$SKILL_ROOT/scripts/loop.py" record --run "$LOOP_RUN" \
  --candidate "$LOOP_RUN/v2.png" --changed "rebuilt the grid" \
  --critic "$LOOP_RUN/critic-2.json"
```

`loop.py` treats any verdict other than `pass`/`match` as a veto, records the issues in the ledger, and adds `critic` to `gate.vetoes`.

## Schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `verdict` | `"pass"` \| `"fail"` | yes | anything not `pass`/`match` vetoes |
| `summary` | string | yes | one sentence, shown in the iteration report |
| `issues` | string[] | yes on `fail` | each one actionable in a single edit |
| `worst` | string \| null | no | fix this first when the metrics are already at gate level |

Malformed JSON is a critic failure, not a candidate failure: re-run the critic once, then fall back to the inline route below. Never guess what it meant to say.

## No sub-agents available

Do the critique inline, but keep the commitment order intact:

1. `Read` the reference PNG again, in this turn. Not from memory of ten iterations ago.
2. `Read` the candidate PNG.
3. Write the verdict JSON to disk **before** running `record`.

Committing the judgement before you see the score is what preserves the veto's independence. Writing it afterwards, once the numbers are in, is self-assessment wearing a JSON hat.

## When the critic and the metrics disagree

- **Metrics pass, critic vetoes** → the critic is right by construction. Fix `worst`, re-capture, re-record. The report will tell you every dimension is at gate level and the only remaining gap is the critic's.
- **Metrics fail, critic passes** → ignore the pass and fix the sub-floor dimension. A human eye tolerating a 2x density error does not make it a match, and the next artefact built from this DNA will not be so lucky.
- **Both fail on different things** → metrics first. They name a dimension; the critic names a symptom, and the symptom often disappears when the dimension is rebuilt.
