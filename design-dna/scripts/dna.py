#!/usr/bin/env python3
"""Codify a converged look into a permanent, reusable skill.

design-loop proves a design matches a reference. This turns that proof into DNA -
palette roles and coverage, grid ratios, type scale, texture, named layouts, and an
explicit list of what the look never does - then emits a standalone skill that
rebuilds it in any format and measures its own output against the same numbers.

The point is permanence. A converged iteration is luck you cannot spend twice; a
DNA with a checker attached is a look you can reproduce on demand.

CLI:
  python dna.py extract  --reference REF.png --name slug [--loop-run RUN] [--out dna.json]
  python dna.py validate --dna dna.json
  python dna.py emit     --dna dna.json --out-dir DIR
  python dna.py check    --dna dna.json --candidate CAND.png
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = 1
HEX = re.compile(r"^#[0-9A-Fa-f]{6}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$")
ROLE_ORDER = ("ground", "ink", "accent", "support", "support2", "support3")
BAR_WIDTH = 22


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _bar(score: float) -> str:
    filled = int(round(score / 100 * BAR_WIDTH))
    return "#" * filled + "." * (BAR_WIDTH - filled)


def _vd():
    """Locate design-loop's visual_dna.py.

    Measurement is optional in this skill: `validate` and `emit` are pure text work
    and must keep working on a machine that only has the DNA file.
    """
    here = Path(__file__).resolve().parent
    for c in (here / "visual_dna.py",
              here.parents[1] / "design-loop" / "scripts" / "visual_dna.py"):
        if c.exists():
            sys.path.insert(0, str(c.parent))
            import visual_dna as vd
            return vd
    raise SystemExit("[dna] visual_dna.py not found. Install the design-loop skill "
                     f"beside this one, or copy its scripts/visual_dna.py into {here}.")


def cmd_extract(a: argparse.Namespace) -> int:
    """Measure a reference into a DNA draft. The qualitative half is left blank on
    purpose - `validate` will name every field an agent still has to write."""
    vd = _vd()
    ref = Path(a.reference)
    if not ref.exists():
        raise SystemExit(f"[dna] reference not found: {ref}")
    m = vd.measure_file(ref)
    pal = [e for e in m["palette"] if e["coverage"] >= 0.005]

    source = {"reference": str(ref.resolve()), "measured": _now()}
    if a.loop_run:
        rj = Path(a.loop_run) / "run.json"
        if not rj.exists():
            raise SystemExit(f"[dna] no design-loop run at {rj}")
        run = json.loads(rj.read_text(encoding="utf-8"))
        best = next((e for e in reversed(run["iterations"]) if e["gate"]["passed"]), None)
        source.update({"loop_run": str(Path(a.loop_run).resolve()),
                       "converged": best is not None,
                       "iterations": len(run["iterations"]),
                       "proven_overall": best["overall"] if best else None,
                       "proven_artefact": best["candidate"] if best else None})
        # A DNA is only worth codifying once the loop has proven it reproducible.
        if best is None:
            print("[dna] warning: that run never passed its gate. You are codifying "
                  "an unproven look.", file=sys.stderr)

    dna = {
        "schema": SCHEMA,
        "name": a.name,
        "title": a.title or a.name.replace("-", " ").title(),
        "version": "1.0.0",
        "created": _now(),
        "brief": a.brief,
        "formats": [],
        "source": source,
        "palette": {
            "roles": {r: e["hex"] for r, e in zip(ROLE_ORDER, pal)},
            "coverage": {e["hex"]: e["coverage"] for e in pal},
            "rules": [],
        },
        "grid": {"aspect": m["aspect"], "margins": m["margins"],
                 "columns": m["grid"]["columns"], "rows": m["grid"]["rows"],
                 "mass_centroid": m["mass_centroid"]},
        "type": {"scale_ratio": m["type_scale_proxy"], "dominance": m["dominance"],
                 "families": {}, "cases": {}},
        "texture": {"ink_coverage": m["ink_coverage"], "edge_density": m["edge_density"],
                    "edge_anisotropy": m["edge_anisotropy"],
                    "texture_energy": m["texture_energy"]},
        "layouts": [],
        "forbidden": [],
        "gate": {"threshold": a.gate, "floor": a.floor},
        "measurement": m,
    }
    out = Path(a.out or f"{a.name}-dna.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dna, indent=2, default=vd._json_default), encoding="utf-8")

    print(f"[dna] draft written to {out}")
    print(f"  measured        {ref.name}  aspect {m['aspect']}  "
          f"{m['grid']['columns']} col / {m['grid']['rows']} rows")
    print(f"  palette roles   " + ", ".join(f"{r}={h}" for r, h in dna["palette"]["roles"].items()))
    print(f"  type scale      {m['type_scale_proxy']}x, dominance {m['dominance']}")
    print("  still to write  palette.rules, type.families, layouts[], forbidden[], formats[]")
    print("  next            fill those in, then `dna.py validate`")
    return 0


def _validate(d: dict) -> tuple[list[str], list[str]]:
    errs: list[str] = []
    warns: list[str] = []

    if d.get("schema") != SCHEMA:
        errs.append(f"schema must be {SCHEMA}, got {d.get('schema')!r}")
    if not SLUG.match(str(d.get("name", ""))):
        errs.append("name must be a kebab-case slug, e.g. acid-summit")
    if not str(d.get("title", "")).strip():
        errs.append("title is empty")

    pal = d.get("palette") or {}
    roles = pal.get("roles") or {}
    if len(roles) < 2:
        errs.append("palette.roles needs at least a ground and an ink colour")
    for r, h in roles.items():
        if not HEX.match(str(h)):
            errs.append(f"palette.roles.{r} is not a #RRGGBB hex: {h!r}")
    cov = pal.get("coverage") or {}
    for h, v in cov.items():
        if not HEX.match(str(h)):
            errs.append(f"palette.coverage key is not a hex: {h!r}")
        elif not isinstance(v, (int, float)) or not 0 <= v <= 1:
            errs.append(f"palette.coverage[{h}] must be a 0..1 fraction, got {v!r}")
    for r, h in roles.items():
        if cov and h not in cov:
            warns.append(f"palette.roles.{r} ({h}) has no measured coverage")
    if not pal.get("rules"):
        warns.append("palette.rules is empty - state how the colours divide the frame")

    g = d.get("grid") or {}
    for k in ("aspect", "columns", "rows", "margins", "mass_centroid"):
        if k not in g:
            errs.append(f"grid.{k} is missing")
    if isinstance(g.get("margins"), dict):
        for side in ("left", "right", "top", "bottom"):
            if side not in g["margins"]:
                errs.append(f"grid.margins.{side} is missing")

    t = d.get("type") or {}
    for k in ("scale_ratio", "dominance"):
        if not isinstance(t.get(k), (int, float)):
            errs.append(f"type.{k} must be a number")
    if not t.get("families"):
        warns.append("type.families is empty - name the display and body faces")

    tex = d.get("texture") or {}
    for k in ("ink_coverage", "edge_density", "texture_energy"):
        if not isinstance(tex.get(k), (int, float)):
            errs.append(f"texture.{k} must be a number")

    # The qualitative half is what makes a DNA reusable rather than a screenshot of
    # some numbers. A look with no named layout cannot be rebuilt in a new format.
    layouts = d.get("layouts") or []
    if not layouts:
        errs.append("layouts[] is empty - name at least one composition "
                    "(see references/named-layouts.md)")
    for i, lo in enumerate(layouts):
        if not str(lo.get("name", "")).strip():
            errs.append(f"layouts[{i}].name is empty")
        if not str(lo.get("when", "")).strip():
            errs.append(f"layouts[{i}].when is empty - say when to reach for it")
        if not (lo.get("recipe") or []):
            errs.append(f"layouts[{i}].recipe is empty - list the blocks top to bottom")
    if not (d.get("forbidden") or []):
        errs.append("forbidden[] is empty - name what this look never does")
    if not (d.get("formats") or []):
        warns.append("formats[] is empty - list the formats this DNA is proven on")

    gate = d.get("gate") or {}
    for k in ("threshold", "floor"):
        if not isinstance(gate.get(k), (int, float)):
            errs.append(f"gate.{k} must be a number")
    if "measurement" not in d:
        errs.append("measurement is missing - `check` cannot score anything without it")
    return errs, warns


def cmd_validate(a: argparse.Namespace) -> int:
    d = json.loads(Path(a.dna).read_text(encoding="utf-8"))
    errs, warns = _validate(d)
    for w in warns:
        print(f"[dna] warn  {w}")
    for e in errs:
        print(f"[dna] ERROR {e}")
    if errs:
        print(f"[dna] {len(errs)} error(s) - not ready to emit")
        return 1
    print(f"[dna] {d['name']} v{d.get('version')} is valid"
          + (f" ({len(warns)} warning(s))" if warns else ""))
    return 0


def _pct(v: float) -> str:
    return f"{float(v) * 100:.1f}%"


def _skill_head(d: dict) -> list[str]:
    pal, g, t, tex = d["palette"], d["grid"], d["type"], d["texture"]
    cov = pal.get("coverage") or {}
    hexes = ", ".join(dict.fromkeys(pal["roles"].values()))
    formats = ", ".join(d.get("formats") or []) or "any format"
    L = ["---", f"version: {d.get('version', '1.0.0')}", f"name: {d['name']}",
         "description: |"]
    L.append(f"  Rebuild the {d['title']} look exactly, in any format, and verify the "
             f"result against its measured DNA instead of guessing. Codified from a "
             f"design-loop run: palette {hexes}, "
             f"{g['columns']} column / {g['rows']} row structure, "
             f"{t['scale_ratio']}x type scale, "
             f"{_pct(tex['ink_coverage'])} ink coverage. Proven on {formats}. "
             f"Use when: a request asks for the {d['title']} style by name, or for "
             f"another artefact \"in the same style\" as work already built from this "
             f"DNA. NOT for: matching a new reference the DNA was not built from "
             f"(use design-loop), or open-ended design with no fixed look "
             f"(use frontend-design).")
    L.append('argument-hint: "[artefact to build] [format]"')
    L.append("allowed-tools: Bash, Read, Write, Edit, Glob")
    L.append("---")
    L.append("")
    L.append(f"# {d['title']}")
    L.append("")
    if d.get("brief"):
        L.append(f"{d['brief']}")
        L.append("")
    L.append("This is a measured look, not a mood. Every number below came from a "
             "reference that a design-loop run converged against; `scripts/check.py` "
             "scores new work against the same numbers. Build from the DNA, then check.")
    L.append("")
    L.append("## Palette")
    L.append("")
    L.append("| Role | Hex | Share of the frame |")
    L.append("|---|---|---|")
    for r, h in pal["roles"].items():
        share = _pct(cov[h]) if h in cov else "-"
        L.append(f"| `{r}` | `{h}` | {share} |")
    L.append("")
    for rule in pal.get("rules") or []:
        L.append(f"- {rule}")
    L.append("- Use these hexes literally. A colour outside this list, at more than a "
             "fifth of the frame, drives `color_discipline` to zero on its own.")
    L.append("- `tokens.css` in this skill ships every value below as a CSS custom "
             "property. Import it instead of retyping numbers.")
    L.append("")
    return L


def _skill_body(d: dict) -> list[str]:
    g, t, tex, gate = d["grid"], d["type"], d["texture"], d["gate"]
    m = g["margins"]
    L = ["## Structure", "",
         f"- Aspect {g['aspect']} (width / height). Hold it, or accept a known density "
         f"offset and say so.",
         f"- Margins as fractions of each axis: left {_pct(m['left'])}, "
         f"right {_pct(m['right'])}, top {_pct(m['top'])}, bottom {_pct(m['bottom'])}.",
         f"- {g['columns']} column band(s), {g['rows']} row band(s) of ink.",
         f"- Ink centre of mass at ({g['mass_centroid'][0]}, {g['mass_centroid'][1]}) of "
         f"the frame.", "",
         "## Type", "",
         f"- Scale ratio {t['scale_ratio']}x: the display block is that many times the "
         f"height of a typical text band.",
         f"- Dominance {t['dominance']}: the largest block owns that share of all ink.",
         ]
    for role, fam in (t.get("families") or {}).items():
        L.append(f"- `{role}` face: {fam}")
    for k, v in (t.get("cases") or {}).items():
        L.append(f"- `{k}` case: {v}")
    aniso = tex.get("edge_anisotropy")
    # Interpret the number rather than printing a legend: whoever reads this needs to
    # know which side the reference sits on, not how the metric works.
    reading = ("text-led and horizontally banded" if isinstance(aniso, (int, float))
               and aniso >= 1.25 else "image-led, with no strong banding")
    L += ["", "## Surface", "",
          f"- Ink coverage {_pct(tex['ink_coverage'])} of the frame.",
          f"- Edge density {tex['edge_density']}, anisotropy {aniso} - "
          f"{reading}. Hold that character.",
          f"- Texture energy {tex['texture_energy']}: grain, noise and gradient "
          f"banding must land near this, not above it.", "",
          "## Named layouts", ""]
    for lo in d["layouts"]:
        L.append(f"### {lo['name']}")
        L.append("")
        L.append(f"*{lo['when']}*")
        L.append("")
        for i, step in enumerate(lo["recipe"], 1):
            L.append(f"{i}. {step}")
        if lo.get("notes"):
            L.append("")
            L.append(str(lo["notes"]))
        L.append("")
    L += ["Pick one by name and build it whole. Combining two of them produces a "
          "composition this DNA has never been measured against.", "",
          "## Never", ""]
    for f in d["forbidden"]:
        L.append(f"- {f}")
    L += ["", "## Check before you deliver", "",
          "```bash",
          'python "$SKILL_ROOT/scripts/capture.py" artefact.html --out artefact.png',
          'python "$SKILL_ROOT/scripts/check.py" --candidate artefact.png',
          "```", "",
          f"Passing means overall >= {gate['threshold']} with no dimension below "
          f"{gate['floor']}. `check.py` exits 1 on a fail and names the weakest "
          "dimension first. Do not describe output as on-brand while it exits 1.", "",
          "If a genuinely new format forces a real deviation, do not quietly widen the "
          "DNA: run design-loop against the new artefact, then re-emit this skill at a "
          "bumped version so the change is recorded rather than absorbed.", ""]
    return L


def _skill_md(d: dict) -> str:
    return "\n".join(_skill_head(d) + _skill_body(d))


def _tokens_css(d: dict) -> str:
    pal, g, t, tex = d["palette"], d["grid"], d["type"], d["texture"]
    m = g["margins"]
    lines = [f"/* {d['title']} - generated from {d['name']} DNA v{d['version']}.",
             "   Measured values, not preferences. Edit the DNA and re-emit. */",
             ":root {"]
    for r, h in pal["roles"].items():
        lines.append(f"  --{r}: {h};")
    lines += [f"  --aspect: {g['aspect']};",
              f"  --margin-left: {float(m['left']) * 100:.2f}%;",
              f"  --margin-right: {float(m['right']) * 100:.2f}%;",
              f"  --margin-top: {float(m['top']) * 100:.2f}%;",
              f"  --margin-bottom: {float(m['bottom']) * 100:.2f}%;",
              f"  --type-scale: {t['scale_ratio']};",
              f"  --dominance: {t['dominance']};",
              f"  --target-ink-coverage: {tex['ink_coverage']};",
              "}"]
    for role, fam in (t.get("families") or {}).items():
        lines.append(f"/* {role}: {fam} */")
    return "\n".join(lines) + "\n"


CHECK_PY = '''#!/usr/bin/env python3
"""Score an artefact against this skill's own DNA. Generated by design-dna."""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DNA = HERE.parent / "dna.json"
BAR = 22


def _vd():
    for c in (HERE / "visual_dna.py",
              HERE.parents[1] / "design-loop" / "scripts" / "visual_dna.py"):
        if c.exists():
            sys.path.insert(0, str(c.parent))
            import visual_dna as vd
            return vd
    raise SystemExit("[check] visual_dna.py not found beside this script or in the "
                     "design-loop skill.")


def main() -> int:
    ap = argparse.ArgumentParser(description="Check an artefact against the DNA.")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--dna", default=str(DNA))
    ap.add_argument("--json", dest="out")
    a = ap.parse_args()

    vd = _vd()
    d = json.loads(Path(a.dna).read_text(encoding="utf-8"))
    cmp = vd.compare(d["measurement"], vd.measure_file(a.candidate))
    g = vd.gate(cmp, d["gate"]["threshold"], d["gate"]["floor"])

    print(f"[check] {d['name']} v{d['version']}  "
          f"{'PASS' if g['passed'] else 'FAIL'}  overall {cmp['overall']:.1f} "
          f"(gate {g['threshold']:.0f}, floor {g['floor']:.0f})")
    for dim in vd.DIMENSIONS:
        s = cmp["scores"][dim]
        filled = int(round(s / 100 * BAR))
        print(f"  {dim:<17}{s:5.1f}  {'#' * filled}{'.' * (BAR - filled)}"
              + ("  < floor" if s < g["floor"] else ""))
    roles = {v.upper() for v in d["palette"]["roles"].values()}
    blend = False
    for p in [x for x in cmp["palette_detail"] if not x["matched"]][:4]:
        # A missing tone with no role is a blend the palette should produce by
        # itself - anti-aliased type, an overlap. Never add it as a literal hue.
        named = p["ref"].upper() in roles
        blend = blend or not named
        print(f"  missing {'colour' if named else 'blend '}  {p['ref']} - "
              f"nearest used {p['nearest']}, dE {p['delta_e']}")
    if blend:
        print("  (a blend is a symptom: fix the roles and their sizes, "
              "do not add the blend as a colour)")
    if not g["passed"]:
        print("  -> fix first: " + ", ".join(g["fix_order"][:3]))
    if a.out:
        Path(a.out).write_text(json.dumps({**cmp, "gate": g}, indent=2,
                                          default=vd._json_default), encoding="utf-8")
    return 0 if g["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
'''


def cmd_emit(a: argparse.Namespace) -> int:
    """Write a standalone skill package that rebuilds the look and checks itself."""
    dna_path = Path(a.dna)
    d = json.loads(dna_path.read_text(encoding="utf-8"))
    errs, warns = _validate(d)
    for w in warns:
        print(f"[dna] warn  {w}")
    if errs:
        for e in errs:
            print(f"[dna] ERROR {e}")
        raise SystemExit("[dna] refusing to emit an invalid DNA - fix the errors above")

    out = Path(a.out_dir)
    (out / "scripts").mkdir(parents=True, exist_ok=True)
    (out / "SKILL.md").write_text(_skill_md(d), encoding="utf-8")
    (out / "dna.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
    (out / "tokens.css").write_text(_tokens_css(d), encoding="utf-8")
    (out / "scripts" / "check.py").write_text(CHECK_PY, encoding="utf-8")

    # Copy the measurement core in so the emitted skill survives design-loop being
    # moved, renamed, or uninstalled. Permanence is the entire point.
    copied, kept = [], []
    here = Path(__file__).resolve().parent
    for cand_dir in (here, here.parents[1] / "design-loop" / "scripts"):
        for f in ("visual_dna.py", "capture.py"):
            dst = out / "scripts" / f
            if dst.exists():
                # A re-emit never overwrites these - an older package may be pinned
                # to the core it was verified against.
                if f not in copied and f not in kept:
                    kept.append(f)
            elif (cand_dir / f).exists():
                shutil.copy2(cand_dir / f, dst)
                copied.append(f)
    if "visual_dna.py" not in copied + kept:
        print("[dna] warn  visual_dna.py not found; check.py will fall back to the "
              "installed design-loop skill at run time", file=sys.stderr)

    print(f"[dna] emitted skill {d['name']} v{d['version']} to {out}")
    print(f"  SKILL.md        {len(_skill_md(d).splitlines())} lines, "
          f"{len(d['layouts'])} named layout(s), {len(d['forbidden'])} prohibition(s)")
    print(f"  self-check      python \"{out / 'scripts' / 'check.py'}\" --candidate X.png")
    bundled = [f"{f} (copied)" for f in copied] + [f"{f} (kept)" for f in kept]
    print(f"  bundled         {', '.join(bundled) or 'nothing (using design-loop at run time)'}")
    print("  install         move this directory under ~/.claude/skills/ to make the "
          "look permanent")
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    vd = _vd()
    d = json.loads(Path(a.dna).read_text(encoding="utf-8"))
    if "measurement" not in d:
        raise SystemExit("[dna] this DNA has no stored measurement - re-run `extract`")
    cmp = vd.compare(d["measurement"], vd.measure_file(a.candidate))
    g = vd.gate(cmp, d["gate"]["threshold"], d["gate"]["floor"])
    print(f"[dna] {d['name']} v{d['version']}  {'PASS' if g['passed'] else 'FAIL'}  "
          f"overall {cmp['overall']:.1f} (gate {g['threshold']:.0f}, "
          f"floor {g['floor']:.0f})")
    for dim in vd.DIMENSIONS:
        s = cmp["scores"][dim]
        print(f"  {dim:<17}{s:5.1f}  {_bar(s)}"
              + ("  < floor" if s < g["floor"] else ""))
    roles = {v.upper() for v in d["palette"]["roles"].values()}
    blend = False
    for p in [x for x in cmp["palette_detail"] if not x["matched"]][:4]:
        named = p["ref"].upper() in roles
        blend = blend or not named
        print(f"  missing {'colour' if named else 'blend '}  {p['ref']} - "
              f"nearest used {p['nearest']}, dE {p['delta_e']}")
    if blend:
        print("  (a blend is a symptom: fix the roles and their sizes, "
              "do not add the blend as a colour)")
    if not g["passed"]:
        print("  -> fix first: " + ", ".join(g["fix_order"][:3]))
    if a.out:
        Path(a.out).write_text(json.dumps({**cmp, "gate": g}, indent=2,
                                          default=vd._json_default), encoding="utf-8")
    return 0 if g["passed"] else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Codify a look into a reusable skill.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("extract", help="measure a reference into a DNA draft")
    e.add_argument("--reference", required=True)
    e.add_argument("--name", required=True, help="kebab-case slug, e.g. acid-summit")
    e.add_argument("--title", default="")
    e.add_argument("--brief", default="")
    e.add_argument("--loop-run", help="a converged design-loop run directory")
    e.add_argument("--gate", type=float, default=82.0)
    e.add_argument("--floor", type=float, default=65.0)
    e.add_argument("--out")

    v = sub.add_parser("validate", help="check a DNA is complete enough to emit")
    v.add_argument("--dna", required=True)

    m = sub.add_parser("emit", help="write a standalone, self-checking skill package")
    m.add_argument("--dna", required=True)
    m.add_argument("--out-dir", required=True)

    c = sub.add_parser("check", help="score an artefact against a DNA")
    c.add_argument("--dna", required=True)
    c.add_argument("--candidate", required=True)
    c.add_argument("--json", dest="out")

    a = ap.parse_args(argv)
    return {"extract": cmd_extract, "validate": cmd_validate,
            "emit": cmd_emit, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
