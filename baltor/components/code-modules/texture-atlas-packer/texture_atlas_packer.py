"""Pack many small images into one texture atlas (MaxRects, best-short-side-fit).

Why: one atlas means one texture for a Godot TileSet, a particle sheet or a
caption icon strip, fewer draw calls and no per-file import settings.

Features:

* MaxRects best-short-side-fit with free-rectangle pruning; deterministic for
  the same inputs (sorted by max side, then area, then name).
* ``padding`` pixels between regions and ``extrude`` pixels of edge
  duplication around each region so bilinear filtering never bleeds a
  neighbour into a sprite.
* Smallest power-of-two (or exact) atlas that fits, up to ``max_size``.
* Writes ``atlas.png``, ``atlas.json`` (TexturePacker-style "hash" frames) and
  optionally one Godot 4 ``AtlasTexture`` ``.tres`` per region.

Usage::

    python texture_atlas_packer.py icons/*.png --out build/icons_atlas [--padding 2] [--extrude 1]
                                   [--max-size 4096] [--no-pot] [--godot-res res://ui/icons_atlas.png]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    w: int
    h: int

    def contains(self, o: "Rect") -> bool:
        return o.x >= self.x and o.y >= self.y and o.x + o.w <= self.x + self.w and o.y + o.h <= self.y + self.h

    def intersects(self, o: "Rect") -> bool:
        return not (o.x >= self.x + self.w or o.x + o.w <= self.x or o.y >= self.y + self.h or o.y + o.h <= self.y)


class MaxRects:
    def __init__(self, width: int, height: int):
        self.width, self.height = width, height
        self.free = [Rect(0, 0, width, height)]

    def insert(self, w: int, h: int) -> Rect | None:
        best, best_short, best_long = None, None, None
        for fr in self.free:
            if w <= fr.w and h <= fr.h:
                short, long_ = min(fr.w - w, fr.h - h), max(fr.w - w, fr.h - h)
                if best is None or (short, long_, fr.y, fr.x) < (best_short, best_long, best.y, best.x):
                    best, best_short, best_long = Rect(fr.x, fr.y, w, h), short, long_
        if best is None:
            return None
        self._split(best)
        return best

    def _split(self, used: Rect) -> None:
        new_free = []
        for fr in self.free:
            if not fr.intersects(used):
                new_free.append(fr)
                continue
            if used.x > fr.x:
                new_free.append(Rect(fr.x, fr.y, used.x - fr.x, fr.h))
            if used.x + used.w < fr.x + fr.w:
                new_free.append(Rect(used.x + used.w, fr.y, fr.x + fr.w - used.x - used.w, fr.h))
            if used.y > fr.y:
                new_free.append(Rect(fr.x, fr.y, fr.w, used.y - fr.y))
            if used.y + used.h < fr.y + fr.h:
                new_free.append(Rect(fr.x, used.y + used.h, fr.w, fr.y + fr.h - used.y - used.h))
        # prune rectangles contained in others
        pruned = []
        for i, a in enumerate(new_free):
            if a.w <= 0 or a.h <= 0:
                continue
            if any(j != i and b.contains(a) and (b != a or j < i) for j, b in enumerate(new_free)):
                continue
            pruned.append(a)
        self.free = pruned


def _candidate_sizes(min_w: int, min_h: int, max_size: int, pot: bool) -> list[tuple[int, int]]:
    if not pot:
        sizes, side = [], max(min_w, min_h)
        while side <= max_size:
            sizes.append((max(side, min_w), max(side, min_h)))
            side = int(side * 1.25) + 1
        return sizes
    p = 1
    while p < max(min_w, min_h, 1):
        p *= 2
    sizes = []
    while p <= max_size:
        sizes += [(p, p // 2), (p // 2, p), (p, p)] if p >= 2 else [(p, p)]
        p *= 2
    return [(w, h) for w, h in sizes if w >= min_w and h >= min_h]


def pack_sizes(sizes: dict[str, tuple[int, int]], padding: int = 2, extrude: int = 0, max_size: int = 4096,
               power_of_two: bool = True) -> tuple[tuple[int, int], dict[str, Rect]]:
    """Place each (w, h); returns atlas size and the inner (content) rectangle per name."""
    if not sizes:
        raise ValueError("nothing to pack")
    border = padding + 2 * extrude
    order = sorted(sizes, key=lambda n: (-max(sizes[n]), -(sizes[n][0] * sizes[n][1]), n))
    need_w = max(w for w, _ in sizes.values()) + border
    need_h = max(h for _, h in sizes.values()) + border
    area = sum((w + border) * (h + border) for w, h in sizes.values())
    for aw, ah in sorted(_candidate_sizes(need_w, need_h, max_size, power_of_two), key=lambda s: (s[0] * s[1], s)):
        if aw * ah < area:
            continue
        packer = MaxRects(aw, ah)
        placed: dict[str, Rect] = {}
        for name in order:
            w, h = sizes[name]
            r = packer.insert(w + border, h + border)
            if r is None:
                break
            placed[name] = Rect(r.x + extrude, r.y + extrude, w, h)
        else:
            return (aw, ah), placed
    raise ValueError(f"images do not fit in {max_size}x{max_size}; raise max_size or split the atlas")


def _extrude(atlas: Image.Image, r: Rect, n: int) -> None:
    if n <= 0:
        return
    top = atlas.crop((r.x, r.y, r.x + r.w, r.y + 1))
    bottom = atlas.crop((r.x, r.y + r.h - 1, r.x + r.w, r.y + r.h))
    for i in range(1, n + 1):
        atlas.paste(top, (r.x, r.y - i))
        atlas.paste(bottom, (r.x, r.y + r.h - 1 + i))
    left = atlas.crop((r.x, r.y - n, r.x + 1, r.y + r.h + n))
    right = atlas.crop((r.x + r.w - 1, r.y - n, r.x + r.w, r.y + r.h + n))
    for i in range(1, n + 1):
        atlas.paste(left, (r.x - i, r.y - n))
        atlas.paste(right, (r.x + r.w - 1 + i, r.y - n))


def build_atlas(images: dict[str, Image.Image], padding: int = 2, extrude: int = 1, max_size: int = 4096,
                power_of_two: bool = True) -> tuple[Image.Image, dict[str, Rect]]:
    sizes = {n: im.size for n, im in images.items()}
    (aw, ah), placed = pack_sizes(sizes, padding, extrude, max_size, power_of_two)
    atlas = Image.new("RGBA", (aw, ah), (0, 0, 0, 0))
    for name, r in placed.items():
        atlas.paste(images[name].convert("RGBA"), (r.x, r.y))
        _extrude(atlas, r, extrude)
    return atlas, placed


def atlas_json(placed: dict[str, Rect], size: tuple[int, int], image_name: str) -> dict:
    return {
        "frames": {n: {"frame": {"x": r.x, "y": r.y, "w": r.w, "h": r.h}, "rotated": False, "trimmed": False,
                       "spriteSourceSize": {"x": 0, "y": 0, "w": r.w, "h": r.h},
                       "sourceSize": {"w": r.w, "h": r.h}} for n, r in sorted(placed.items())},
        "meta": {"app": "baltor texture_atlas_packer", "version": "1.0", "image": image_name,
                 "format": "RGBA8888", "size": {"w": size[0], "h": size[1]}, "scale": "1"},
    }


def atlastexture_tres(atlas_res_path: str, r: Rect, filter_clip: bool = True) -> str:
    """Godot 4 AtlasTexture resource for one region of the atlas."""
    return "\n".join([
        '[gd_resource type="AtlasTexture" format=3]', "",
        f'[ext_resource type="Texture2D" path={json.dumps(atlas_res_path)} id="1_atlas"]', "",
        "[resource]", 'atlas = ExtResource("1_atlas")', f"region = Rect2({r.x}, {r.y}, {r.w}, {r.h})",
        f"filter_clip = {'true' if filter_clip else 'false'}", ""])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="+")
    ap.add_argument("--out", required=True, help="output path stem, e.g. build/icons_atlas")
    ap.add_argument("--padding", type=int, default=2)
    ap.add_argument("--extrude", type=int, default=1)
    ap.add_argument("--max-size", type=int, default=4096)
    ap.add_argument("--no-pot", action="store_true", help="allow non power-of-two atlas sizes")
    ap.add_argument("--godot-res", help="res:// path of the atlas PNG; writes one AtlasTexture .tres per image")
    a = ap.parse_args(argv)
    images = {}
    for p in a.images:
        name = Path(p).stem
        if name in images:
            ap.error(f"duplicate image name {name}")
        images[name] = Image.open(p)
    atlas, placed = build_atlas(images, a.padding, a.extrude, a.max_size, not a.no_pot)
    stem = Path(a.out)
    stem.parent.mkdir(parents=True, exist_ok=True)
    png = stem.with_suffix(".png")
    atlas.save(png)
    stem.with_suffix(".json").write_text(json.dumps(atlas_json(placed, atlas.size, png.name), indent=2) + "\n")
    if a.godot_res:
        tres_dir = stem.parent / (stem.name + "_regions")
        tres_dir.mkdir(exist_ok=True)
        for name, r in placed.items():
            (tres_dir / f"{name}.tres").write_text(atlastexture_tres(a.godot_res, r), encoding="utf-8")
    print(f"{len(placed)} region(s) -> {png} ({atlas.size[0]}x{atlas.size[1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
