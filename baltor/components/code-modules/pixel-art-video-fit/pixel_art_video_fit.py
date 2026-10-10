"""Fit pixel art into a video frame with whole-number nearest-neighbour scaling.

Pixel art blurs or shimmers when scaled by 2.37x with bilinear filtering. This
module picks the largest integer scale that fits the target frame inside a
safe area, scales with nearest neighbour, and places the result on a solid or
tiled background, so every source pixel becomes an exact NxN block.

``fit_sequence`` uses one scale for a whole animation so the frames never
jump between sizes. Presets cover the common delivery formats; the default is
1080x1920 (9:16 vertical shorts) with a 6% side and 12% top/bottom safe margin
so captions and platform UI do not cover the art.

Usage::

    python pixel_art_video_fit.py frame.png --out out.png [--preset vertical-9x16] [--bg "#1a1c2c"]
    python pixel_art_video_fit.py frames/*.png --out-dir fitted/ [--tile bg_tile.png]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

PRESETS = {
    "vertical-9x16": {"size": [1080, 1920], "margin": [0.06, 0.12]},
    "landscape-16x9": {"size": [1920, 1080], "margin": [0.06, 0.08]},
    "square-1x1": {"size": [1080, 1080], "margin": [0.06, 0.06]},
    "portrait-4x5": {"size": [1080, 1350], "margin": [0.06, 0.08]},
}


@dataclass
class Fit:
    scale: int
    offset: tuple[int, int]
    size: tuple[int, int]


def integer_scale(src: tuple[int, int], target: tuple[int, int], margin: tuple[float, float] = (0.0, 0.0)) -> int:
    """Largest whole-number scale so ``src`` fits inside ``target`` minus the safe margins (at least 1)."""
    sw, sh = src
    tw, th = target
    avail_w = int(tw * (1 - 2 * margin[0]))
    avail_h = int(th * (1 - 2 * margin[1]))
    if sw <= 0 or sh <= 0:
        raise ValueError("source size must be positive")
    return max(1, min(avail_w // sw, avail_h // sh))


def _parse_colour(c: str | tuple) -> tuple[int, int, int, int]:
    if isinstance(c, tuple):
        return tuple(c) + (255,) * (4 - len(c))  # type: ignore[return-value]
    c = c.lstrip("#")
    if len(c) == 6:
        c += "ff"
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4, 6))  # type: ignore[return-value]


def fit(img: Image.Image, target: tuple[int, int] = (1080, 1920), margin: tuple[float, float] = (0.06, 0.12),
        bg: str | tuple = "#000000", tile: Image.Image | None = None, scale: int | None = None,
        anchor: str = "center") -> tuple[Image.Image, Fit]:
    """Scale ``img`` by an integer factor with nearest neighbour and place it on a ``target``-sized canvas."""
    s = scale or integer_scale(img.size, target, margin)
    scaled = img.convert("RGBA").resize((img.width * s, img.height * s), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", target, _parse_colour(bg))
    if tile is not None:
        t = tile.convert("RGBA").resize((tile.width * s, tile.height * s), Image.Resampling.NEAREST)
        for y in range(0, target[1], t.height):
            for x in range(0, target[0], t.width):
                canvas.paste(t, (x, y))
    x = (target[0] - scaled.width) // 2
    if anchor == "center":
        y = (target[1] - scaled.height) // 2
    elif anchor == "upper-third":
        y = max(int(target[1] * margin[1]), int(target[1] / 3 - scaled.height / 2))
    else:
        raise ValueError("anchor must be center or upper-third")
    canvas.alpha_composite(scaled, (x, y))
    return canvas, Fit(s, (x, y), scaled.size)


def fit_sequence(paths: list[str | Path], out_dir: str | Path, target=(1080, 1920), margin=(0.06, 0.12),
                 bg="#000000", tile: Image.Image | None = None) -> Fit:
    """Fit every frame with the same scale (computed from the largest frame)."""
    imgs = [Image.open(p) for p in paths]
    w = max(i.width for i in imgs)
    h = max(i.height for i in imgs)
    s = integer_scale((w, h), target, margin)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    last = None
    for p, im in zip(paths, imgs):
        frame, last = fit(im, target, margin, bg, tile, scale=s)
        frame.convert("RGB").save(out / (Path(p).stem + ".png"))
    return last  # type: ignore[return-value]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("--out", help="output file for a single image")
    ap.add_argument("--out-dir", help="output directory for a sequence")
    ap.add_argument("--preset", choices=sorted(PRESETS), default="vertical-9x16")
    ap.add_argument("--preset-file", help="JSON with size and margin (overrides --preset)")
    ap.add_argument("--bg", default="#000000")
    ap.add_argument("--tile", help="background tile image, scaled by the same integer factor")
    ap.add_argument("--anchor", choices=["center", "upper-third"], default="center")
    a = ap.parse_args(argv)
    p = json.loads(Path(a.preset_file).read_text()) if a.preset_file else PRESETS[a.preset]
    target, margin = tuple(p["size"]), tuple(p["margin"])
    tile = Image.open(a.tile) if a.tile else None
    if len(a.images) == 1 and a.out:
        frame, info = fit(Image.open(a.images[0]), target, margin, a.bg, tile, anchor=a.anchor)
        frame.convert("RGB").save(a.out)
    elif a.out_dir:
        info = fit_sequence(a.images, a.out_dir, target, margin, a.bg, tile)
    else:
        ap.error("use --out for one image or --out-dir for several")
    print(f"scale x{info.scale}, art {info.size[0]}x{info.size[1]} at {info.offset} in {target[0]}x{target[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
