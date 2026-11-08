#!/usr/bin/env python3
"""Render any design artefact to a PNG the loop can measure and an agent can Read.

Handles the four things a design actually ships as: a local HTML/SVG file, a live
URL, a still image, or a video. Everything lands as a normalised PNG (plus a
contact sheet for video) so one comparison path serves every format.

CLI:
  python capture.py SOURCE --out shot.png [--width 1200] [--full-page]
  python capture.py clip.mp4 --out-dir frames/ [--frames 9]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

HTML_EXT = {".html", ".htm"}
SVG_EXT = {".svg"}
IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
MAX_EDGE = 1998  # Claude's Read ceiling for image height


def kind(source: str) -> str:
    if urlparse(source).scheme in ("http", "https"):
        return "url"
    ext = Path(source).suffix.lower()
    if ext in HTML_EXT:
        return "html"
    if ext in SVG_EXT:
        return "svg"
    if ext in IMG_EXT:
        return "image"
    if ext in VIDEO_EXT:
        return "video"
    raise SystemExit(f"[capture] unsupported source: {source}")


def normalise(path: Path) -> Path:
    """Flatten alpha onto white and clamp height so Read never rejects the file."""
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im)
    im = im.convert("RGB")
    if im.height > MAX_EDGE:
        im = im.resize((max(1, round(im.width * MAX_EDGE / im.height)), MAX_EDGE),
                       Image.LANCZOS)
    im.save(path, "PNG")
    return path


def shoot_web(target: str, out: Path, width: int, height: int, full_page: bool,
              wait_ms: int, scale: float, dark: bool) -> Path:
    """Screenshot an HTML file, SVG file, or URL with headless Chromium."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("[capture] playwright is required for html/svg/url sources.\n"
                         "  pip install playwright && python -m playwright install chromium")

    url = target if urlparse(target).scheme in ("http", "https") \
        else Path(target).resolve().as_uri()
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale,
            color_scheme="dark" if dark else "light",
        )
        page.goto(url, wait_until="load", timeout=60_000)
        try:  # webfonts and CSS transitions settle after load, not on it
            page.wait_for_load_state("networkidle", timeout=8_000)
        except Exception:
            pass
        page.wait_for_timeout(wait_ms)
        page.screenshot(path=str(out), full_page=full_page)
        browser.close()
    return normalise(out)


def _ffprobe_duration(src: str) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", src],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        raise SystemExit(f"[capture] ffprobe could not read a duration from {src}")


def shoot_video(src: str, out_dir: Path, n: int) -> dict:
    """Sample n evenly spaced stills plus a contact sheet.

    Motion DNA is judged on held frames, not on a scrub bar: each still is
    measurable by visual_dna, and the sheet gives an agent the whole arc in one
    Read. Timestamps are passed as separate argv items - never interpolated into
    a shell string - so Windows paths survive.
    """
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise SystemExit("[capture] ffmpeg and ffprobe are required for video sources.")
    out_dir.mkdir(parents=True, exist_ok=True)
    dur = _ffprobe_duration(src)
    # Skip the first and last 4%: fades in and out are not the design.
    times = [dur * (0.04 + 0.92 * i / max(1, n - 1)) for i in range(n)]

    frames = []
    for i, t in enumerate(times, 1):
        dst = out_dir / f"frame_{i:02d}.png"
        subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error",
                        "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1",
                        "-vf", "scale=1280:-2:flags=lanczos", str(dst)], check=True)
        if dst.exists():
            frames.append(normalise(dst))

    if not frames:
        raise SystemExit(f"[capture] no frames extracted from {src}")
    cols = 3
    rows = (len(frames) + cols - 1) // cols
    tw, th = Image.open(frames[0]).size
    cw, ch = 420, max(1, round(th * 420 / tw))
    sheet = Image.new("RGB", (cols * cw, rows * ch), (255, 255, 255))
    for i, f in enumerate(frames):
        sheet.paste(Image.open(f).resize((cw, ch), Image.LANCZOS), ((i % cols) * cw,
                                                                    (i // cols) * ch))
    sheet_path = out_dir / "contact_sheet.png"
    sheet.save(sheet_path, "PNG")
    normalise(sheet_path)
    return {"duration": round(dur, 3),
            "frames": [str(f) for f in frames],
            "timestamps": [round(t, 3) for t in times][:len(frames)],
            "contact_sheet": str(sheet_path)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Capture a design artefact as PNG.")
    ap.add_argument("source", help="html/svg file, http(s) URL, image, or video")
    ap.add_argument("--out", help="output PNG (non-video sources)")
    ap.add_argument("--out-dir", help="output directory (video sources)")
    ap.add_argument("--width", type=int, default=1440)
    ap.add_argument("--height", type=int, default=1800)
    ap.add_argument("--full-page", action="store_true",
                    help="capture the whole scroll height, not just the viewport")
    ap.add_argument("--wait", type=int, default=900, help="settle time in ms after load")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--frames", type=int, default=9, help="stills to sample from a video")
    a = ap.parse_args(argv)

    k = kind(a.source)
    if k == "video":
        out_dir = Path(a.out_dir or (Path(a.source).parent / "capture"))
        print(json.dumps({"kind": k, **shoot_video(a.source, out_dir, a.frames)}, indent=2))
        return 0

    if not a.out:
        raise SystemExit("[capture] --out is required for non-video sources")
    out = Path(a.out)
    if k == "image":
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.open(a.source).save(out, "PNG")
        normalise(out)
    else:
        shoot_web(a.source, out, a.width, a.height, a.full_page, a.wait, a.scale, a.dark)

    w, h = Image.open(out).size
    print(json.dumps({"kind": k, "path": str(out), "size": [w, h]}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
