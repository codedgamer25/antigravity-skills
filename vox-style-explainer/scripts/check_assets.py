#!/usr/bin/env python3
"""Validate delivered cutouts against the beat sheet before phase 4.

Run this the moment the asset folder comes back from the image tool. It catches the
four failures that otherwise surface in phase 7: a missing file, a PNG with no alpha
channel, a "transparent" PNG whose alpha is fully opaque (a white background), and a
source too small to scale up in a 1920-wide frame.

    python check_assets.py --beat-sheet beat-sheet.csv --public public

Exit code is non-zero if anything is not OK, so it can gate the halftone step.

Requires: Pillow, numpy.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    sys.exit(f"missing dependency: {exc.name}. Install with: pip install Pillow numpy")

MIN_LONG_EDGE = 1200
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".m4v"}


def load_rows(path: Path) -> list[dict]:
    if not path.exists():
        sys.exit(f"check_assets: beat sheet not found: {path}")
    if path.suffix.lower() == ".json":
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, list) else raw.get("scenes") or raw.get("beats") or []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def expected_assets(rows: list[dict], public: Path) -> list[tuple[str, Path, str]]:
    """-> [(scene_id, path, role)] for every asset the beat sheet names."""
    out: list[tuple[str, Path, str]] = []
    for r in rows:
        rid = str(r.get("id") or "").strip()
        if not rid or rid.upper().startswith("EXAMPLE-"):
            continue
        folder = public / "scenes" / rid

        mid = r.get("midground_asset") or ""
        names = mid if isinstance(mid, list) else [m.strip() for m in mid.split(";")]
        for n in names:
            if n:
                out.append((rid, folder / n, "midground"))

        fg = (r.get("foreground_asset") or "").strip()
        if fg:
            out.append((rid, folder / fg, "foreground"))
    return out


def inspect(path: Path, min_long_edge: int) -> tuple[str, str]:
    """-> (verdict, detail). verdict is OK / WARN / FAIL."""
    if not path.exists():
        return "FAIL", "missing"

    if path.suffix.lower() in VIDEO_SUFFIXES:
        kb = path.stat().st_size // 1024
        if kb == 0:
            return "FAIL", "zero-byte video"
        note = "" if path.suffix.lower() == ".webm" else "; keying needed (prefer .webm with alpha)"
        return "OK", f"video, {kb} KB{note}"

    try:
        im = Image.open(path)
        im.load()
    except Exception as e:  # noqa: BLE001
        return "FAIL", f"unreadable ({type(e).__name__})"

    rgba = im.convert("RGBA")
    w, h = rgba.size
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8)

    if "A" not in im.convert("RGBA").getbands():
        return "FAIL", f"{w}x{h}, no alpha channel"
    if alpha.min() == 255:
        return "FAIL", f"{w}x{h}, alpha fully opaque - background not removed"

    transparent = 100.0 * (alpha == 0).mean()
    detail = f"{w}x{h}, {transparent:.0f}% transparent"
    if max(w, h) < min_long_edge:
        return "WARN", detail + f", long edge < {min_long_edge}px"
    if transparent < 5.0:
        return "WARN", detail + ", suspiciously little transparency"
    return "OK", detail


def main() -> int:
    p = argparse.ArgumentParser(description="Check beat-sheet assets before halftoning.")
    p.add_argument("--beat-sheet", type=Path, required=True)
    p.add_argument("--public", type=Path, default=Path("public"))
    p.add_argument("--min-long-edge", type=int, default=MIN_LONG_EDGE)
    a = p.parse_args()

    assets = expected_assets(load_rows(a.beat_sheet), a.public)
    if not assets:
        sys.exit("check_assets: the beat sheet names no assets")

    counts = {"OK": 0, "WARN": 0, "FAIL": 0}
    current = None
    for scene, path, role in assets:
        if scene != current:
            print(f"\n{scene}")
            current = scene
        verdict, detail = inspect(path, a.min_long_edge)
        counts[verdict] += 1
        mark = {"OK": "  ok  ", "WARN": " warn ", "FAIL": " FAIL "}[verdict]
        print(f"  [{mark}] {role:<10} {path.name:<28} {detail}")

    print(f"\n{counts['OK']} ok, {counts['WARN']} warning(s), {counts['FAIL']} failure(s)")
    if counts["FAIL"]:
        print("Fix the failures before running halftone.py - see references/asset-handoff.md")
        return 1
    if counts["WARN"]:
        print("Warnings are shippable but will show as soft edges or upscaling artefacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
