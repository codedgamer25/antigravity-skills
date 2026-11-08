#!/usr/bin/env python3
"""Convergence engine for design-loop: a ledger that decides when to stop.

The loop's failure mode is not "the design is wrong", it is "the agent declares
victory". So the stop condition lives here, in code: every iteration is measured
against the gold standard, scored per dimension, and compared to the previous
iteration. The ledger detects stalls and regressions, hands back a ranked fix
order, and refuses to pass a design that is still below floor on any dimension.

CLI:
  python loop.py init   --run RUN --reference REF.png --brief "..." [--format poster]
  python loop.py record --run RUN --candidate CAND.png [--changed "..."] [--critic C.json]
  python loop.py status --run RUN
  python loop.py dna    --run RUN [--json OUT]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import visual_dna as vd  # noqa: E402

STALL_DELTA = 1.5      # overall gain below this counts as no progress
REGRESSION_DROP = 5.0  # per-dimension drop that counts as a regression
BAR_WIDTH = 22


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_file(run: str | Path) -> Path:
    return Path(run) / "run.json"


def _load(run: str | Path) -> dict:
    f = _run_file(run)
    if not f.exists():
        raise SystemExit(f"[loop] no run at {f} - start with `loop.py init`")
    return json.loads(f.read_text(encoding="utf-8"))


def _save(run: str | Path, state: dict) -> None:
    f = _run_file(run)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(state, indent=2, default=vd._json_default), encoding="utf-8")


def _bar(score: float) -> str:
    filled = int(round(score / 100 * BAR_WIDTH))
    return "#" * filled + "." * (BAR_WIDTH - filled)


def cmd_init(a: argparse.Namespace) -> int:
    ref = Path(a.reference)
    if not ref.exists():
        raise SystemExit(f"[loop] reference not found: {ref}")
    state = {
        "created": _now(),
        "brief": a.brief,
        "format": a.format,
        "reference": {"path": str(ref.resolve()), "measurement": vd.measure_file(ref)},
        "gate": {"threshold": a.gate, "floor": a.floor, "max_iterations": a.max_iterations},
        "iterations": [],
    }
    _save(a.run, state)
    m = state["reference"]["measurement"]
    pal = ", ".join(f"{e['hex']} {e['coverage'] * 100:.0f}%"
                    for e in m["palette"] if e["coverage"] >= 0.01)
    print(f"[loop] run initialised at {Path(a.run) / 'run.json'}")
    print(f"  format          {a.format}")
    print(f"  gold standard   {ref.name}  {m['size'][0]}x{m['size'][1]}  aspect {m['aspect']}")
    print(f"  palette         {pal}")
    print(f"  structure       {m['grid']['columns']} col / {m['grid']['rows']} row bands, "
          f"margins L{m['margins']['left']} R{m['margins']['right']} "
          f"T{m['margins']['top']} B{m['margins']['bottom']}")
    print(f"  hierarchy       size ratio {m['type_scale_proxy']}, dominance {m['dominance']}")
    print(f"  density         ink {m['ink_coverage']}, edges {m['edge_density']}, "
          f"texture {m['texture_energy']}")
    print(f"  gate            overall >= {a.gate}, every dimension >= {a.floor}, "
          f"max {a.max_iterations} iterations")
    return 0


def _flags(state: dict, scores: dict, overall: float, prev: dict | None) -> list[str]:
    """Name the pathologies that make a loop run forever."""
    flags: list[str] = []
    n = len(state["iterations"]) + 1
    if prev:
        gain = overall - prev["overall"]
        if gain <= -STALL_DELTA:
            flags.append(f"backslid: overall fell {gain:.1f} - you traded one dimension "
                         "for another; keep the win and redo the loss")
        elif gain < STALL_DELTA:
            flags.append(f"stalled: overall moved {gain:+.1f} - stop nudging values, "
                         "rebuild the weakest dimension from the reference")
        for d in vd.DIMENSIONS:
            drop = prev["scores"][d] - scores[d]
            if drop >= REGRESSION_DROP:
                flags.append(f"regression:{d} lost {drop:.1f} while you fixed something else")
    if n >= state["gate"]["max_iterations"]:
        flags.append("exhausted: iteration budget spent - report the honest gap, "
                     "do not claim a match")
    return flags


def cmd_record(a: argparse.Namespace) -> int:
    state = _load(a.run)
    cand = Path(a.candidate)
    if not cand.exists():
        raise SystemExit(f"[loop] candidate not found: {cand}")

    ref_m = state["reference"]["measurement"]
    cand_m = vd.measure_file(cand)
    cmp = vd.compare(ref_m, cand_m)
    g = vd.gate(cmp, state["gate"]["threshold"], state["gate"]["floor"])

    critic = None
    if a.critic:
        critic = json.loads(Path(a.critic).read_text(encoding="utf-8"))
        # A critic can only ever veto. It cannot wave a design through a metric
        # floor, and it cannot be the reason a failing design "looks fine".
        if critic.get("verdict", "").lower() not in ("pass", "match"):
            g["passed"] = False
            g.setdefault("vetoes", []).append("critic")

    prev = state["iterations"][-1] if state["iterations"] else None
    entry = {
        "n": len(state["iterations"]) + 1,
        "at": _now(),
        "candidate": str(cand.resolve()),
        "changed": a.changed or "",
        "scores": cmp["scores"],
        "overall": cmp["overall"],
        "gate": g,
        "palette_detail": cmp["palette_detail"],
        "measurement": cand_m,
        "critic": critic,
        # Flags are pathologies of a loop still running; a passing iteration is done.
        "flags": [] if g["passed"] else _flags(state, cmp["scores"], cmp["overall"], prev),
    }
    state["iterations"].append(entry)
    _save(a.run, state)
    _print_iteration(state, entry, prev)
    return 0 if g["passed"] else 1


# Each failing dimension maps to one concrete rebuild instruction. Vague critique
# is what makes a loop spin forever; naming the single next move is what ends it.
FIXES = {
    "palette": "sample the reference hexes and use only those, then match the coverage "
               "share of its top two colours before touching anything else",
    "color_discipline": "delete every colour the reference never used: tints, shadows, "
                        "borders, hover states, stock photography",
    "layout": "rebuild the frame, do not nudge it - copy the reference margins and its "
              "column/row band count, then place blocks on that grid",
    "hierarchy": "widen the size gap between the display block and body copy, and give "
                 "the dominant block the same share of the ink as the reference",
    "density": "change content mass, not alignment - the page carries too much or too "
               "little ink and edge detail for this reference",
    "texture": "match the surface: grain, noise, blur, gradient banding, image detail",
}


def _print_iteration(state: dict, e: dict, prev: dict | None) -> None:
    g = e["gate"]
    floor = g["floor"]
    verdict = "PASS" if g["passed"] else "FAIL"
    print(f"[loop] iteration {e['n']}/{state['gate']['max_iterations']}  {verdict}  "
          f"overall {e['overall']:.1f} (gate {g['threshold']:.0f}, floor {floor:.0f})")
    if e["changed"]:
        print(f"  changed  {e['changed']}")
    for d in vd.DIMENSIONS:
        s = e["scores"][d]
        delta = f"{s - prev['scores'][d]:+7.1f}" if prev else "       "
        print(f"  {d:<17}{s:5.1f}{delta}  {_bar(s)}"
              + ("  < floor" if s < floor else ""))

    for p in [x for x in e["palette_detail"] if not x["matched"]][:4]:
        print(f"  missing colour  {p['ref']} ({p['ref_coverage'] * 100:.0f}% of the "
              f"reference) - nearest you used is {p['nearest']}, dE {p['delta_e']}")

    if e["critic"]:
        c = e["critic"]
        print(f"  critic          {c.get('verdict', '?')}"
              + (f" - {c['summary']}" if c.get("summary") else ""))
        for issue in (c.get("issues") or [])[:5]:
            print(f"    - {issue}")
    for f in e["flags"]:
        print(f"  ! {f}")

    if g["passed"]:
        print("  -> converged. Run `loop.py dna` and hand the result to design-dna so "
              "the look outlives this one artefact.")
        return
    if not g["fix_order"]:
        print("  -> every dimension is at gate level; the only gap left is the critic's. "
              "Fix its issues verbatim - do not re-tune the metrics.")
        return
    print("  -> next move, weakest first:")
    for d in g["fix_order"][:3]:
        print(f"     {d} ({e['scores'][d]:.0f}): {FIXES[d]}")


def cmd_status(a: argparse.Namespace) -> int:
    state = _load(a.run)
    its = state["iterations"]
    print(f"[loop] {Path(a.run).name}  format {state['format']}  "
          f"{len(its)}/{state['gate']['max_iterations']} iterations")
    if state["brief"]:
        print(f"  brief           {state['brief']}")
    print(f"  gold standard   {Path(state['reference']['path']).name}")
    if not its:
        print("  no candidates recorded yet")
        return 1
    print("  " + f"{'n':>3}{'overall':>9}" + "".join(f"{d[:9]:>10}" for d in vd.DIMENSIONS)
          + "   verdict")
    for e in its:
        print("  " + f"{e['n']:>3}{e['overall']:>9.1f}"
              + "".join(f"{e['scores'][d]:>10.1f}" for d in vd.DIMENSIONS)
              + f"   {'PASS' if e['gate']['passed'] else 'FAIL'}")
    print()
    _print_iteration(state, its[-1], its[-2] if len(its) > 1 else None)
    return 0 if its[-1]["gate"]["passed"] else 1


def cmd_dna(a: argparse.Namespace) -> int:
    """Emit the run's gold-standard DNA so design-dna can make it permanent."""
    state = _load(a.run)
    its = state["iterations"]
    winner = next((e for e in reversed(its) if e["gate"]["passed"]), None)
    best = winner or (max(its, key=lambda e: e["overall"]) if its else None)
    vd._emit({
        "brief": state["brief"],
        "format": state["format"],
        "gate": state["gate"],
        "converged": winner is not None,
        "iterations": len(its),
        "reference": state["reference"],
        "best": None if best is None else {
            "n": best["n"], "candidate": best["candidate"], "overall": best["overall"],
            "scores": best["scores"], "measurement": best["measurement"]},
    }, a.out)
    return 0 if winner else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Convergence ledger for design-loop.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    i = sub.add_parser("init", help="register the gold standard and the gate")
    i.add_argument("--run", required=True, help="run directory; holds run.json")
    i.add_argument("--reference", required=True, help="gold-standard PNG")
    i.add_argument("--brief", default="")
    i.add_argument("--format", default="unspecified",
                   help="poster | website | deck | packaging | video | ...")
    i.add_argument("--gate", type=float, default=82.0)
    i.add_argument("--floor", type=float, default=65.0)
    i.add_argument("--max-iterations", type=int, default=6)

    r = sub.add_parser("record", help="score one candidate and update the ledger")
    r.add_argument("--run", required=True)
    r.add_argument("--candidate", required=True, help="candidate PNG from capture.py")
    r.add_argument("--changed", default="", help="what you changed since the last iteration")
    r.add_argument("--critic", help="sub-agent verdict JSON; can only veto")

    s = sub.add_parser("status", help="show the ledger and the current next move")
    s.add_argument("--run", required=True)

    d = sub.add_parser("dna", help="emit the gold-standard DNA for design-dna")
    d.add_argument("--run", required=True)
    d.add_argument("--json", dest="out")

    a = ap.parse_args(argv)
    return {"init": cmd_init, "record": cmd_record,
            "status": cmd_status, "dna": cmd_dna}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
