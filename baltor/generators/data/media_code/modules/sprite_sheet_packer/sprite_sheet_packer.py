"""Pack animation frames into a sprite sheet with a JSON atlas (Pillow).

Uses shelf packing (frames sorted by height, placed left to right in rows)
with padding, optional trimming of transparent borders, and power-of-two
sheet sizes when requested. The atlas records each frame's rectangle, the
trim offset and the original size, so a game engine or web player can draw
frames at the right place.

Usage::

    from sprite_sheet_packer import pack
    sheet, atlas = pack({"walk_0": img0, "walk_1": img1}, max_width=1024, padding=2, trim=True)
    sheet.save("walk.png"); json.dump(atlas, open("walk.json", "w"))
"""

from __future__ import annotations

from PIL import Image


def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def pack(frames: dict, max_width: int = 2048, padding: int = 2, trim: bool = True, pow2: bool = False):
    if not frames:
        raise ValueError("no frames")
    items = []
    for name, img in frames.items():
        rgba = img.convert("RGBA")
        bbox = rgba.getbbox() if trim else (0, 0, rgba.width, rgba.height)
        if bbox is None:
            bbox = (0, 0, 1, 1)
        cropped = rgba.crop(bbox)
        if cropped.width + 2 * padding > max_width:
            raise ValueError(f"frame {name} is wider than max_width")
        items.append((name, cropped, bbox, rgba.size))
    items.sort(key=lambda it: (-it[1].height, it[0]))
    x = y = padding
    row_h = 0
    placed = []
    for name, im, bbox, size in items:
        if x + im.width + padding > max_width:
            x = padding
            y += row_h + padding
            row_h = 0
        placed.append((name, im, bbox, size, x, y))
        x += im.width + padding
        row_h = max(row_h, im.height)
    W = max(px + im.width for _, im, _, _, px, _ in placed) + padding
    H = y + row_h + padding
    if pow2:
        W, H = _next_pow2(W), _next_pow2(H)
    sheet = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    atlas = {"meta": {"size": [W, H], "padding": padding, "trimmed": trim}, "frames": {}}
    for name, im, bbox, size, px, py in placed:
        sheet.paste(im, (px, py))
        atlas["frames"][name] = {"x": px, "y": py, "w": im.width, "h": im.height,
                                 "offset": [bbox[0], bbox[1]], "source_size": list(size)}
    atlas["frames"] = dict(sorted(atlas["frames"].items()))
    return sheet, atlas


def unpack(sheet: Image.Image, atlas: dict, name: str) -> Image.Image:
    """Rebuild one original-size frame from the sheet and atlas."""
    f = atlas["frames"][name]
    out = Image.new("RGBA", tuple(f["source_size"]), (0, 0, 0, 0))
    out.paste(sheet.crop((f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])), tuple(f["offset"]))
    return out
