#!/usr/bin/env python3
"""Deterministic visual-DNA measurement for design-loop / design-dna.

Turns a rendered design into ratio-level features - palette coverage, margins,
grid rhythm, hierarchy contrast, density, texture - and scores a candidate
against a gold-standard reference. Ratios, not pixels, so a poster and a website
built from the same DNA measure alike.

CLI:
  python visual_dna.py measure IMG.png [--json OUT]
  python visual_dna.py compare REF.png CAND.png [--json OUT] [--gate 82]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

MAX_SIDE = 1024
PALETTE_COLORS = 12
PALETTE_MERGE_DE = 6.0    # merge palette entries closer than this (CIEDE2000)
PALETTE_MATCH_DE = 10.0   # candidate ink counts as on-palette within this
BAND_MIN_RATIO = 0.012    # ignore ink bands thinner than this share of the axis
GUTTER_MIN_RATIO = 0.015  # ignore gutters thinner than this share of the axis
INK_BAND_RATIO = 0.003    # a row/column counts as inked at this share of its length

DIMENSIONS = ("palette", "color_discipline", "layout", "hierarchy", "density", "texture")
WEIGHTS = {
    "palette": 0.28,
    "color_discipline": 0.17,
    "layout": 0.20,
    "hierarchy": 0.15,
    "density": 0.12,
    "texture": 0.08,
}

# --- color science ---------------------------------------------------------


def _srgb_to_linear(c: np.ndarray) -> np.ndarray:
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """rgb: (..., 3) float in 0..1 -> CIE Lab (D65)."""
    lin = _srgb_to_linear(np.asarray(rgb, dtype=np.float64))
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = lin @ m.T
    xyz = xyz / np.array([0.95047, 1.0, 1.08883])
    e, k = 216 / 24389, 24389 / 27
    f = np.where(xyz > e, np.cbrt(np.maximum(xyz, 0)), (k * xyz + 16) / 116)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def ciede2000(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
    """Perceptual color distance. Broadcasting-friendly; returns dE00."""
    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]
    C1, C2 = np.hypot(a1, b1), np.hypot(a2, b2)
    Cbar = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(Cbar ** 7 / (Cbar ** 7 + 25.0 ** 7 + 1e-12)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    dLp = L2 - L1
    dCp = C2p - C1p
    dhp = h2p - h1p
    dhp = np.where(dhp > 180, dhp - 360, np.where(dhp < -180, dhp + 360, dhp))
    dhp = np.where(C1p * C2p == 0, 0.0, dhp)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dhp / 2))
    Lbar = (L1 + L2) / 2
    Cbarp = (C1p + C2p) / 2
    hsum = h1p + h2p
    hbarp = np.where(C1p * C2p == 0, hsum,
                     np.where(np.abs(h1p - h2p) <= 180, hsum / 2,
                              np.where(hsum < 360, (hsum + 360) / 2, (hsum - 360) / 2)))
    T = (1 - 0.17 * np.cos(np.radians(hbarp - 30))
         + 0.24 * np.cos(np.radians(2 * hbarp))
         + 0.32 * np.cos(np.radians(3 * hbarp + 6))
         - 0.20 * np.cos(np.radians(4 * hbarp - 63)))
    dTheta = 30 * np.exp(-(((hbarp - 275) / 25) ** 2))
    Rc = 2 * np.sqrt(Cbarp ** 7 / (Cbarp ** 7 + 25.0 ** 7 + 1e-12))
    Sl = 1 + (0.015 * (Lbar - 50) ** 2) / np.sqrt(20 + (Lbar - 50) ** 2)
    Sc = 1 + 0.045 * Cbarp
    Sh = 1 + 0.015 * Cbarp * T
    Rt = -np.sin(np.radians(2 * dTheta)) * Rc
    return np.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                   + Rt * (dCp / Sc) * (dHp / Sh))


def hexof(rgb01) -> str:
    r, g, b = (int(round(float(c) * 255)) for c in rgb01)
    return f"#{r:02X}{g:02X}{b:02X}"


# --- image loading ---------------------------------------------------------


def load_rgb(path: str | Path, max_side: int = MAX_SIDE) -> np.ndarray:
    """Load an image as float RGB in 0..1, downscaled so max(side) <= max_side.

    Alpha is flattened onto white so transparent PNG exports do not read as
    black ink and wreck every downstream ratio.
    """
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    im = im.convert("RGB")
    w, h = im.size
    scale = max_side / max(w, h)
    if scale < 1.0:
        im = im.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
    return np.asarray(im, dtype=np.float64) / 255.0


# --- feature extraction ----------------------------------------------------


def extract_palette(img: np.ndarray, colors: int = PALETTE_COLORS) -> list[dict]:
    """Adaptive-quantize to `colors`, then merge perceptual near-duplicates."""
    h, w, _ = img.shape
    pil = Image.fromarray((img * 255).astype(np.uint8))
    q = pil.convert("P", palette=Image.ADAPTIVE, colors=colors)
    pal = np.asarray(q.getpalette()[: colors * 3], dtype=np.float64).reshape(-1, 3) / 255.0
    idx = np.asarray(q, dtype=np.int32)
    counts = np.bincount(idx.ravel(), minlength=pal.shape[0]).astype(np.float64)
    total = float(h * w)

    order = np.argsort(-counts)
    entries: list[dict] = []
    for i in order:
        if counts[i] <= 0:
            continue
        lab = rgb_to_lab(pal[i])
        for e in entries:
            if float(ciede2000(lab, e["_lab"])) < PALETTE_MERGE_DE:
                e["coverage"] += counts[i] / total
                break
        else:
            entries.append({"hex": hexof(pal[i]), "rgb": [round(float(c), 4) for c in pal[i]],
                            "coverage": counts[i] / total, "_lab": lab})
    for e in entries:
        e["coverage"] = round(e["coverage"], 5)
    entries.sort(key=lambda e: -e["coverage"])
    return entries


def _bands(profile: np.ndarray, axis_len: int, thresh: float) -> list[tuple[int, int]]:
    """Contiguous runs of 'has ink' in a 1-D projection profile.

    `thresh` is an absolute ink count, not a fraction of the profile maximum: a
    body-copy line must stay detectable next to a display headline that carries
    fifty times its ink mass. Gutters thinner than GUTTER_MIN_RATIO are bridged
    first (so letter-spacing inside a headline does not read as ten columns),
    then bands thinner than BAND_MIN_RATIO are dropped as noise.
    """
    if profile.max() <= 0:
        return []
    on = profile >= thresh
    min_gut = max(1, int(GUTTER_MIN_RATIO * axis_len))
    min_band = max(1, int(BAND_MIN_RATIO * axis_len))

    filled = on.copy()
    run = 0
    for i, v in enumerate(on):
        if not v:
            run += 1
            continue
        if 0 < run < min_gut and i - run > 0:
            filled[i - run:i] = True
        run = 0

    out, start = [], None
    for i, v in enumerate(filled):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_band:
                out.append((start, i))
            start = None
    if start is not None and len(filled) - start >= min_band:
        out.append((start, len(filled)))
    return out


def measure(img: np.ndarray) -> dict:
    """Ratio-level visual DNA of one rendered design."""
    h, w, _ = img.shape
    palette = extract_palette(img)
    bg_rgb = np.array(palette[0]["rgb"]) if palette else np.array([1.0, 1.0, 1.0])

    lab = rgb_to_lab(img)
    bg_lab = rgb_to_lab(bg_rgb)
    de_bg = ciede2000(lab, bg_lab[None, None, :])
    ink = de_bg > 8.0
    ink_cov = float(ink.mean())

    lum = lab[..., 0] / 100.0
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    sat_ink = chroma[ink] if ink.any() else np.array([0.0])

    gy = np.abs(np.diff(lum, axis=0)).mean() if h > 1 else 0.0
    gx = np.abs(np.diff(lum, axis=1)).mean() if w > 1 else 0.0

    blur = np.asarray(Image.fromarray((img * 255).astype(np.uint8))
                      .filter(ImageFilter.BoxBlur(2)), dtype=np.float64) / 255.0
    texture = float(np.abs(img - blur).mean())

    col_prof = ink.sum(axis=0).astype(np.float64)
    row_prof = ink.sum(axis=1).astype(np.float64)
    col_bands = _bands(col_prof, w, max(1.0, INK_BAND_RATIO * h))
    row_bands = _bands(row_prof, h, max(1.0, INK_BAND_RATIO * w))

    if ink.any():
        ys, xs = np.nonzero(ink)
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()), int(ys.min()), int(ys.max())
        cx, cy = float(xs.mean()) / w, float(ys.mean()) / h
        ink_lum = lum[ink]
    else:
        x0, x1, y0, y1, cx, cy = 0, w - 1, 0, h - 1, 0.5, 0.5
        ink_lum = np.array([float(lum.mean())])

    bg_lum = float(bg_lab[0]) / 100.0
    ink_bg_contrast = abs(float(ink_lum.mean()) - bg_lum)
    ink_tonal_spread = float(np.percentile(ink_lum, 95) - np.percentile(ink_lum, 5))

    band_h = [b - a for a, b in row_bands] or [h]
    med_band = float(np.median(band_h))
    scale_ratio = float(max(band_h) / med_band) if med_band > 0 else 1.0
    areas = [float(row_prof[a:b].sum()) for a, b in row_bands] or [1.0]
    dominance = float(max(areas) / sum(areas))

    return {
        "size": [w, h],
        "aspect": round(w / h, 4),
        "palette": [{k: v for k, v in e.items() if not k.startswith("_")} for e in palette],
        "background": palette[0]["hex"] if palette else "#FFFFFF",
        "ink_coverage": round(ink_cov, 5),
        "luminance": {"mean": round(float(lum.mean()), 4),
                      "std": round(float(lum.std()), 4),
                      "background": round(bg_lum, 4),
                      "ink_mean": round(float(ink_lum.mean()), 4)},
        "ink_bg_contrast": round(ink_bg_contrast, 4),
        "ink_tonal_spread": round(ink_tonal_spread, 4),
        "chroma": {"mean_ink": round(float(sat_ink.mean()), 3),
                   "std_ink": round(float(sat_ink.std()), 3),
                   "max_ink": round(float(sat_ink.max()), 3)},
        "edge_density": round(float((gx + gy) / 2), 5),
        "edge_anisotropy": round(float(gx / (gy + 1e-9)), 4),
        "texture_energy": round(texture, 5),
        "grid": {"columns": len(col_bands), "rows": len(row_bands),
                 "col_bands": [[round(a / w, 4), round(b / w, 4)] for a, b in col_bands][:24],
                 "row_bands": [[round(a / h, 4), round(b / h, 4)] for a, b in row_bands][:24]},
        "margins": {"left": round(x0 / w, 4), "right": round((w - 1 - x1) / w, 4),
                    "top": round(y0 / h, 4), "bottom": round((h - 1 - y1) / h, 4)},
        "mass_centroid": [round(cx, 4), round(cy, 4)],
        "type_scale_proxy": round(scale_ratio, 3),
        "dominance": round(dominance, 4),
    }


def measure_file(path: str | Path) -> dict:
    m = measure(load_rgb(path))
    m["source"] = str(path)
    return m


# --- scoring ---------------------------------------------------------------


def _sim(a: float, b: float, tol: float) -> float:
    """100 when equal, 0 once the absolute gap reaches `tol`."""
    return float(round(max(0.0, 1.0 - abs(float(a) - float(b)) / float(tol)) * 100, 1))


def _ratio_sim(a: float, b: float, tol: float) -> float:
    """Like _sim but on log-ratio, for quantities where 2x matters, not +2."""
    a, b = max(float(a), 1e-6), max(float(b), 1e-6)
    gap = abs(float(np.log(a / b)))
    return float(round(max(0.0, 1.0 - gap / float(tol)) * 100, 1))


def _palette_scores(ref: dict, cand: dict) -> tuple[float, float, list[dict]]:
    """Palette fidelity + colour discipline.

    fidelity     - do the reference's load-bearing colours appear, at roughly
                   the same coverage?
    discipline   - how much of the candidate's area is colour the reference
                   never used? This is the single best slop detector.
    """
    ref_e = [e for e in ref["palette"] if e["coverage"] >= 0.005]
    cand_e = [e for e in cand["palette"] if e["coverage"] >= 0.005]
    if not ref_e or not cand_e:
        return 0.0, 0.0, []

    ref_lab = rgb_to_lab(np.array([e["rgb"] for e in ref_e]))
    cand_lab = rgb_to_lab(np.array([e["rgb"] for e in cand_e]))
    dmat = ciede2000(ref_lab[:, None, :], cand_lab[None, :, :])  # (ref, cand)

    detail, hits = [], []
    for i, e in enumerate(ref_e):
        j = int(np.argmin(dmat[i]))
        de = float(dmat[i, j])
        matched = de <= PALETTE_MATCH_DE
        got = cand_e[j]["coverage"] if matched else 0.0
        detail.append({"ref": e["hex"], "ref_coverage": e["coverage"],
                       "nearest": cand_e[j]["hex"], "delta_e": round(de, 2),
                       "matched": matched, "cand_coverage": round(got, 5)})
        if matched:
            hits.append(i)

    weights = np.array([e["coverage"] for e in ref_e])
    weights = weights / weights.sum()
    present = np.array([1.0 if d["matched"] else 0.0 for d in detail])
    cov_gap = np.array([abs(d["cand_coverage"] - d["ref_coverage"]) for d in detail])
    cov_term = np.clip(1.0 - cov_gap / 0.25, 0.0, 1.0)
    fidelity = round(float((weights * present * cov_term).sum()) * 100, 1)

    off = sum(e["coverage"] for j, e in enumerate(cand_e)
              if float(dmat[:, j].min()) > PALETTE_MATCH_DE)
    discipline = round(max(0.0, 1.0 - off / 0.20) * 100, 1)
    return fidelity, discipline, detail


def compare(ref: dict, cand: dict) -> dict:
    """Score a candidate's measurement against the reference measurement."""
    fidelity, discipline, pal_detail = _palette_scores(ref, cand)

    rm, cm = ref["margins"], cand["margins"]
    margin_score = float(np.mean([_sim(rm[k], cm[k], 0.12) for k in ("left", "right", "top", "bottom")]))
    centroid = float(np.mean([_sim(ref["mass_centroid"][i], cand["mass_centroid"][i], 0.20)
                              for i in (0, 1)]))
    cols = _sim(ref["grid"]["columns"], cand["grid"]["columns"],
                max(3.0, 0.5 * ref["grid"]["columns"]))
    rows = _sim(ref["grid"]["rows"], cand["grid"]["rows"],
                max(4.0, 0.6 * ref["grid"]["rows"]))
    layout = round(0.40 * margin_score + 0.25 * centroid + 0.20 * cols + 0.15 * rows, 1)

    # Hierarchy is deliberately colour-blind: size contrast between the biggest
    # block and a typical one, plus how much of the ink that block commands.
    # Tone lives in `palette`, so a failing dimension names one real fix.
    hierarchy = round(0.60 * _ratio_sim(ref["type_scale_proxy"], cand["type_scale_proxy"], 0.85)
                      + 0.40 * _sim(ref["dominance"], cand["dominance"], 0.30), 1)

    density = round(0.55 * _ratio_sim(max(ref["ink_coverage"], 1e-4),
                                     max(cand["ink_coverage"], 1e-4), 0.90)
                    + 0.45 * _ratio_sim(max(ref["edge_density"], 1e-5),
                                        max(cand["edge_density"], 1e-5), 1.10), 1)

    texture = round(_ratio_sim(max(ref["texture_energy"], 1e-5),
                               max(cand["texture_energy"], 1e-5), 1.20), 1)

    scores = {k: float(v) for k, v in
              {"palette": fidelity, "color_discipline": discipline, "layout": layout,
               "hierarchy": hierarchy, "density": density, "texture": texture}.items()}
    overall = float(round(sum(scores[d] * WEIGHTS[d] for d in DIMENSIONS), 1))
    return {"scores": scores, "overall": overall, "palette_detail": pal_detail,
            "weights": WEIGHTS}


def gate(cmp: dict, threshold: float = 82.0, floor: float = 65.0) -> dict:
    """Convergence gate. Overall must clear `threshold` AND no dimension may sit
    below `floor` - a design that nails colour but loses the grid is not done."""
    scores = cmp["scores"]
    below = [k for _, k in sorted((v, k) for k, v in scores.items() if v < floor)]
    passed = bool(cmp["overall"] >= threshold and not below)

    # Rank fixes by the overall points they would buy, not by raw score: a cheap
    # dimension sitting at 80 is never more urgent than a heavy one at 50. Sub-floor
    # dimensions jump the queue, because the gate cannot pass while one is down.
    def urgency(k: str) -> tuple[int, float]:
        return (0 if scores[k] < floor else 1, -(100.0 - scores[k]) * WEIGHTS[k])

    return {"passed": passed, "overall": float(cmp["overall"]),
            "threshold": float(threshold), "floor": float(floor),
            "below_floor": below,
            "fix_order": sorted((k for k in scores if scores[k] < threshold), key=urgency)}


# --- CLI -------------------------------------------------------------------


def _json_default(o):
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"{type(o).__name__} is not JSON serializable")


def _emit(payload: dict, out: str | None) -> None:
    text = json.dumps(payload, indent=2, default=_json_default)
    if out:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        Path(out).write_text(text, encoding="utf-8")
        print(f"[visual-dna] wrote {out}", file=sys.stderr)
    print(text)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Measure and compare visual DNA.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("measure", help="measure one image")
    m.add_argument("image")
    m.add_argument("--json", dest="out")

    c = sub.add_parser("compare", help="score candidate against reference")
    c.add_argument("reference")
    c.add_argument("candidate")
    c.add_argument("--json", dest="out")
    c.add_argument("--gate", type=float, default=82.0)
    c.add_argument("--floor", type=float, default=65.0)

    a = ap.parse_args(argv)
    if a.cmd == "measure":
        _emit(measure_file(a.image), a.out)
        return 0

    ref, cand = measure_file(a.reference), measure_file(a.candidate)
    cmp = compare(ref, cand)
    g = gate(cmp, a.gate, a.floor)
    _emit({"reference": ref, "candidate": cand, **cmp, "gate": g}, a.out)
    return 0 if g["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
