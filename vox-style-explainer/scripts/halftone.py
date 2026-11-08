#!/usr/bin/env python3
"""Deterministic halftone + marker-stroke prep for vox-style-explainer cutouts.

Given a transparent-background PNG, produces two files:

    <name>-halftone.png        black-and-white ordered-dither cutout, alpha preserved
    <name>-halftone-stroke.png flat-colour dilated silhouette for the offset marker stroke

The dither is a fixed Bayer matrix, so the same input and flags always give byte-identical
output. That is the whole point: every character in a film must share one dot grid, which an
image model cannot guarantee across separate generations.

Usage:
    python halftone.py --beat-sheet beat-sheet.csv --public public   # midground only
    python halftone.py cutout.png
    python halftone.py scenes/*/*.png --dot 5 --contrast 1.5
    python halftone.py cutout.png --no-stroke
    python halftone.py cutout.png --stroke-spread 9 --stroke-color "#D6252B"

Prefer --beat-sheet: it halftones exactly the midground assets and leaves foregrounds in
colour, in one run, which is what keeps every character on the same dot grid.

Requires: Pillow, numpy.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image, ImageFilter
except ImportError as exc:  # pragma: no cover
    sys.exit(f"missing dependency: {exc.name}. Install with: pip install Pillow numpy")


def bayer_matrix(size: int = 8) -> np.ndarray:
    """Recursive Bayer threshold matrix, normalised to [0, 1)."""
    m = np.array([[0]], dtype=np.float64)
    while m.shape[0] < size:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return m / m.size


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    if len(v) != 6:
        raise argparse.ArgumentTypeError(f"expected #RRGGBB, got {value!r}")
    return tuple(int(v[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def make_halftone(
    img: Image.Image,
    dot: int,
    contrast: float,
    bias: float,
    paper: tuple[int, int, int] | None,
) -> Image.Image:
    """Ordered-dither an RGBA image to black on paper, preserving the subject silhouette."""
    rgba = img.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8)

    grey = np.asarray(rgba.convert("L"), dtype=np.float64) / 255.0
    # Push contrast around mid-grey so the dither has something to bite on. Flat
    # photographic midtones dither into an even 50% screen and lose all form.
    grey = np.clip((grey - 0.5) * contrast + 0.5, 0.0, 1.0)

    base = bayer_matrix(8)
    if dot > 1:
        base = np.kron(base, np.ones((dot, dot), dtype=np.float64))
    h, w = grey.shape
    reps = (h // base.shape[0] + 1, w // base.shape[1] + 1)
    thresholds = np.tile(base, reps)[:h, :w] + bias

    lit = grey > thresholds  # True -> paper shows, False -> ink dot
    out = np.zeros((h, w, 4), dtype=np.uint8)

    if paper is None:
        # Transparent gaps. Only correct over a plain ground with nothing behind the
        # cutout - the offset marker stroke WILL show through every dot gap and the
        # cutout reads as a red fill speckled black instead of black ink on paper.
        out[..., 3] = np.where(lit, 0, alpha)
    else:
        # Opaque within the silhouette: paper where lit, ink where not. This is what
        # printed halftone actually is, and it keeps the red stroke to the offset edge.
        for c in range(3):
            out[..., c] = np.where(lit, paper[c], 0)
        out[..., 3] = alpha

    # No mode= kwarg: it is deprecated and removed in Pillow 13. A 4-channel uint8
    # array already infers RGBA.
    return Image.fromarray(out)


def make_stroke(img: Image.Image, spread: int, colour: tuple[int, int, int]) -> Image.Image:
    """Dilate the alpha channel and fill it flat, giving a hand-drawn outline shape."""
    rgba = img.convert("RGBA")
    # Pad so dilation near the edge is not clipped by the canvas.
    pad = spread + 2
    w, h = rgba.size
    canvas = Image.new("L", (w + pad * 2, h + pad * 2), 0)
    canvas.paste(rgba.getchannel("A"), (pad, pad))

    size = spread * 2 + 1  # MaxFilter needs an odd kernel
    dilated = canvas.filter(ImageFilter.MaxFilter(size))

    out = Image.new("RGBA", dilated.size, (*colour, 0))
    solid = Image.new("RGBA", dilated.size, (*colour, 255))
    out.paste(solid, (0, 0), dilated)
    return out


def process(path: Path, args: argparse.Namespace) -> None:
    if not path.exists():
        print(f"  skip (missing): {path}", file=sys.stderr)
        return

    src = Image.open(path)
    if "A" not in src.convert("RGBA").getbands() or np.asarray(
        src.convert("RGBA").getchannel("A")
    ).min() == 255:
        print(
            f"  warning: {path.name} has no transparency — remove the background before "
            "halftoning or the dither will cover the whole frame",
            file=sys.stderr,
        )

    out_dir = Path(args.out_dir) if args.out_dir else path.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = path.stem

    halftone = make_halftone(
        src,
        dot=args.dot,
        contrast=args.contrast,
        bias=args.threshold_bias,
        paper=None if args.no_fill else args.paper,
    )
    halftone_path = out_dir / f"{stem}-halftone.png"
    halftone.save(halftone_path)
    print(f"  {halftone_path}")

    if not args.no_stroke:
        # The stroke is built from the ORIGINAL alpha, not the dithered one: dilating a dot
        # screen produces a lace edge instead of a solid outline.
        stroke = make_stroke(src, spread=args.stroke_spread, colour=args.stroke_color)
        stroke_path = out_dir / f"{stem}-halftone-stroke.png"
        stroke.save(stroke_path)
        # The stroke canvas is PADDED so dilation is not clipped at the edge, so it is
        # larger than the cutout. The component must subtract this pad, or the stroke
        # sits `pad` px right and down from markerStroke.offsetX/offsetY.
        print(f"  {stroke_path}  (pad={args.stroke_spread + 2}px per side)")


def midground_from_beat_sheet(sheet: Path, public: Path) -> list[Path]:
    """Only midground assets get halftoned - foregrounds stay in colour. Reading the
    beat sheet keeps that rule automatic, so a `*/*.png` glob cannot dither an occluder."""
    import csv
    import json

    if not sheet.exists():
        sys.exit(f"beat sheet not found: {sheet}")
    if sheet.suffix.lower() == ".json":
        raw = json.loads(sheet.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else raw.get("scenes") or raw.get("beats") or []
    else:
        with sheet.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))

    out: list[Path] = []
    for r in rows:
        rid = str(r.get("id") or "").strip()
        if not rid or rid.upper().startswith("EXAMPLE-"):
            continue
        mid = r.get("midground_asset") or ""
        names = mid if isinstance(mid, list) else [m.strip() for m in mid.split(";")]
        for n in names:
            if n and not n.lower().endswith(("-halftone.png", "-halftone-stroke.png")):
                out.append(public / "scenes" / rid / n)
    if not out:
        sys.exit(f"{sheet} names no midground assets")
    return out


def main() -> int:
    p = argparse.ArgumentParser(
        description="Halftone transparent cutouts and bake their offset marker strokes.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("inputs", nargs="*", type=Path, help="transparent PNG cutout(s)")
    p.add_argument("--beat-sheet", type=Path, default=None,
                   help="halftone exactly the midground assets this beat sheet names")
    p.add_argument("--public", type=Path, default=Path("public"),
                   help="project public/ dir, used with --beat-sheet")
    p.add_argument("--dot", type=int, default=4, help="px per dither cell; higher = coarser print")
    p.add_argument("--contrast", type=float, default=1.35, help="contrast push before dithering")
    p.add_argument(
        "--threshold-bias",
        type=float,
        default=0.0,
        help="shift the dither threshold; negative = darker/inkier",
    )
    p.add_argument("--no-stroke", action="store_true", help="skip the marker-stroke silhouette")
    p.add_argument(
        "--paper",
        type=hex_to_rgb,
        default=hex_to_rgb("#EDEBE4"),
        help="colour filling the lit gaps; must match palette.paper in theme.ts",
    )
    p.add_argument(
        "--no-fill",
        action="store_true",
        help="leave dither gaps transparent instead of paper-filled (the stroke will "
        "show through every gap - only use with no stroke behind the cutout)",
    )
    p.add_argument("--stroke-spread", type=int, default=6, help="px of dilation for the stroke")
    p.add_argument("--stroke-color", type=hex_to_rgb, default=hex_to_rgb("#D6252B"))
    p.add_argument("--out-dir", default=None, help="write next to each input by default")
    args = p.parse_args()

    if args.dot < 1:
        p.error("--dot must be >= 1")
    if args.stroke_spread < 1:
        p.error("--stroke-spread must be >= 1")
    if bool(args.inputs) == bool(args.beat_sheet):
        p.error("give either explicit inputs or --beat-sheet, not both and not neither")

    inputs = args.inputs or midground_from_beat_sheet(args.beat_sheet, args.public)

    # One run over the whole set: separate runs can drift --dot and leave one character
    # with visibly coarser dots than the rest.
    for path in inputs:
        print(f"{path}:")
        process(path, args)
    print(f"\n{len(inputs)} cutout(s) processed with dot={args.dot} contrast={args.contrast}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
