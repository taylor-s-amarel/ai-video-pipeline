"""Quantise images to a fixed pixel-art palette (Lospec-style) and check palette compliance.

Reads the palette formats Lospec offers for download (.hex, GIMP .gpl, JASC
.pal, Paint.NET .txt and a palette .png strip), maps every pixel to the
nearest palette colour in OKLab (perceptual) or sRGB space, with optional
ordered (Bayer 4x4 / 8x8) or Floyd-Steinberg dithering, and thresholds alpha
so sprites keep hard edges. ``check`` reports pixels that are off-palette, which
is how a style guard keeps mixed packs (Kenney + itch.io + generated art)
looking like one game.

Palettes are not bundled: download the file from the palette's Lospec page
(credit the palette author) or pass your own.

Usage::

    python lospec_palette_quantiser.py quantise in.png --palette endesga-32.hex --out out.png [--dither bayer4]
    python lospec_palette_quantiser.py check sprite.png --palette endesga-32.hex
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HEX6 = re.compile(r"^#?([0-9a-fA-F]{6})$")
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float64) / 16.0


def _bayer(n: int) -> np.ndarray:
    m = np.array([[0.0]])
    while m.shape[0] < n:
        m = np.block([[4 * m, 4 * m + 2], [4 * m + 3, 4 * m + 1]])
    return m / (m.shape[0] ** 2)


def parse_palette(text: str, fmt: str) -> list[tuple[int, int, int]]:
    """Parse palette text. ``fmt`` is one of hex, gpl, pal, txt."""
    colours: list[tuple[int, int, int]] = []
    lines = [ln.strip() for ln in text.splitlines()]
    if fmt == "hex":
        for ln in lines:
            m = HEX6.match(ln)
            if m:
                v = m.group(1)
                colours.append((int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)))
    elif fmt == "gpl":
        if not lines or not lines[0].startswith("GIMP Palette"):
            raise ValueError("not a GIMP palette (missing 'GIMP Palette' header)")
        for ln in lines[1:]:
            if not ln or ln.startswith("#") or ":" in ln.split()[0]:
                continue
            parts = ln.split()
            if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
                colours.append(tuple(int(p) for p in parts[:3]))  # type: ignore[arg-type]
    elif fmt == "pal":
        if len(lines) < 3 or lines[0] != "JASC-PAL":
            raise ValueError("not a JASC-PAL palette")
        count = int(lines[2])
        for ln in lines[3:3 + count]:
            r, g, b = (int(p) for p in ln.split()[:3])
            colours.append((r, g, b))
    elif fmt == "txt":
        for ln in lines:
            if not ln or ln.startswith(";"):
                continue
            v = ln[-6:]
            if re.fullmatch(r"[0-9a-fA-F]{6}", v):
                colours.append((int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)))
    else:
        raise ValueError(f"unknown palette format {fmt!r}")
    if not colours:
        raise ValueError("palette has no colours")
    for c in colours:
        if any(not 0 <= v <= 255 for v in c):
            raise ValueError(f"colour out of range: {c}")
    return colours


def load_palette(path: str | Path) -> list[tuple[int, int, int]]:
    path = Path(path)
    suffix = path.suffix.lower().lstrip(".")
    if suffix == "png":
        arr = np.asarray(Image.open(path).convert("RGBA")).reshape(-1, 4)
        seen, colours = set(), []
        for r, g, b, a in arr.tolist():
            if a and (r, g, b) not in seen:
                seen.add((r, g, b))
                colours.append((r, g, b))
        return colours
    return parse_palette(path.read_text(encoding="utf-8", errors="replace"), suffix)


def srgb_to_oklab(rgb: np.ndarray) -> np.ndarray:
    """(..., 3) sRGB in 0..255 -> OKLab."""
    c = np.clip(rgb.astype(np.float64), 0.0, 255.0) / 255.0
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
                   [0.2119034982, 0.6806995451, 0.1073969566],
                   [0.0883024619, 0.2817188376, 0.6299787005]])
    lms = lin @ m1.T
    lms_ = np.cbrt(lms)
    m2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
                   [1.9779984951, -2.4285922050, 0.4505937099],
                   [0.0259040371, 0.7827717662, -0.8086757660]])
    return lms_ @ m2.T


def nearest_indices(rgb: np.ndarray, palette: np.ndarray, space: str = "oklab", chunk: int = 65536) -> np.ndarray:
    """Index of the nearest palette colour for each pixel of an (N, 3) array."""
    pal = srgb_to_oklab(palette) if space == "oklab" else palette.astype(np.float64)
    out = np.empty(len(rgb), dtype=np.int32)
    for s in range(0, len(rgb), chunk):
        block = rgb[s:s + chunk]
        pts = srgb_to_oklab(block) if space == "oklab" else block.astype(np.float64)
        d = ((pts[:, None, :] - pal[None, :, :]) ** 2).sum(axis=2)
        out[s:s + chunk] = d.argmin(axis=1)
    return out


def quantise(img: Image.Image, palette: list[tuple[int, int, int]], dither: str = "none", space: str = "oklab",
             alpha_threshold: int = 128, strength: float = 0.5) -> Image.Image:
    """Return an RGBA image that uses only palette colours (alpha becomes 0 or 255)."""
    pal = np.array(palette, dtype=np.float64)
    rgba = np.asarray(img.convert("RGBA")).astype(np.float64)
    h, w = rgba.shape[:2]
    rgb = rgba[:, :, :3].copy()
    alpha = np.where(rgba[:, :, 3] >= alpha_threshold, 255, 0).astype(np.uint8)
    if dither in {"bayer4", "bayer8"}:
        n = 4 if dither == "bayer4" else 8
        m = BAYER4 if n == 4 else _bayer(8)
        tile = np.tile(m, (h // n + 1, w // n + 1))[:h, :w] - 0.5
        spread = 255.0 * strength / max(2, round(len(palette) ** (1 / 3)))
        rgb = np.clip(rgb + tile[:, :, None] * spread, 0, 255)
        idx = nearest_indices(rgb.reshape(-1, 3), pal, space).reshape(h, w)
    elif dither == "floyd":
        idx = np.zeros((h, w), dtype=np.int32)
        work = rgb.copy()
        for y in range(h):
            for x in range(w):
                old = np.clip(work[y, x], 0.0, 255.0)
                i = int(nearest_indices(old[None, :], pal, space)[0])
                idx[y, x] = i
                err = (old - pal[i]) * strength * 2
                if x + 1 < w:
                    work[y, x + 1] += err * 7 / 16
                if y + 1 < h:
                    if x > 0:
                        work[y + 1, x - 1] += err * 3 / 16
                    work[y + 1, x] += err * 5 / 16
                    if x + 1 < w:
                        work[y + 1, x + 1] += err * 1 / 16
            np.clip(work, 0, 255, out=work)
    elif dither == "none":
        idx = nearest_indices(rgb.reshape(-1, 3), pal, space).reshape(h, w)
    else:
        raise ValueError(f"unknown dither {dither!r}")
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[:, :, :3] = pal[idx].astype(np.uint8)
    out[:, :, 3] = alpha
    return Image.fromarray(out, "RGBA")


def palette_report(img: Image.Image, palette: list[tuple[int, int, int]], alpha_threshold: int = 1) -> dict:
    """Usage count per palette colour and the number of visible pixels that are off-palette."""
    rgba = np.asarray(img.convert("RGBA"))
    visible = rgba[:, :, 3] >= alpha_threshold
    px = rgba[:, :, :3][visible]
    keys = (px[:, 0].astype(np.int64) << 16) | (px[:, 1].astype(np.int64) << 8) | px[:, 2].astype(np.int64)
    pal_keys = {(r << 16) | (g << 8) | b: i for i, (r, g, b) in enumerate(palette)}
    uniq, counts = np.unique(keys, return_counts=True)
    usage = [0] * len(palette)
    off = 0
    off_colours = []
    for k, c in zip(uniq.tolist(), counts.tolist()):
        if k in pal_keys:
            usage[pal_keys[k]] += c
        else:
            off += c
            if len(off_colours) < 10:
                off_colours.append(f"#{k:06x}")
    return {"visible_pixels": int(visible.sum()), "off_palette_pixels": off, "off_palette_examples": off_colours,
            "usage": usage, "colours_used": sum(1 for u in usage if u)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("quantise")
    q.add_argument("image")
    q.add_argument("--palette", required=True)
    q.add_argument("--out", required=True)
    q.add_argument("--dither", choices=["none", "bayer4", "bayer8", "floyd"], default="none")
    q.add_argument("--space", choices=["oklab", "rgb"], default="oklab")
    q.add_argument("--alpha-threshold", type=int, default=128)
    q.add_argument("--strength", type=float, default=0.5)
    c = sub.add_parser("check")
    c.add_argument("image")
    c.add_argument("--palette", required=True)
    a = ap.parse_args(argv)
    palette = load_palette(a.palette)
    img = Image.open(a.image)
    if a.cmd == "quantise":
        out = quantise(img, palette, a.dither, a.space, a.alpha_threshold, a.strength)
        out.save(a.out)
        rep = palette_report(out, palette)
        print(f"{a.out}: {rep['colours_used']}/{len(palette)} palette colours used")
        return 0
    rep = palette_report(img, palette)
    print(f"{a.image}: {rep['off_palette_pixels']} off-palette pixel(s) of {rep['visible_pixels']}"
          + (f", e.g. {', '.join(rep['off_palette_examples'])}" if rep["off_palette_examples"] else ""))
    return 1 if rep["off_palette_pixels"] else 0


if __name__ == "__main__":
    sys.exit(main())
