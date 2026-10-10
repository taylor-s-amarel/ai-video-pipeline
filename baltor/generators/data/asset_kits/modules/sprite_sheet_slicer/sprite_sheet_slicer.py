"""Slice sprite sheets into frames and write Godot 4 SpriteFrames resources.

Three ways in:

* ``grid``: fixed frame size with optional margin and spacing (Kenney, LPC,
  most itch.io sheets). Fully transparent cells are skipped by default.
* ``detect``: find sprites on a packed or irregular sheet by connected
  components of the alpha channel (run-length union-find, numpy only).
* ``aseprite``: read an Aseprite ``--data`` JSON export (hash or array form)
  including frame durations and tags, without Aseprite installed.

Outputs: one PNG per frame, ``frames.json`` (rectangles, durations, tags) and,
optionally, a Godot 4 ``SpriteFrames`` ``.tres`` that references the original
sheet through ``AtlasTexture`` regions, so the sheet stays one texture.

Usage::

    python sprite_sheet_slicer.py grid sheet.png --size 16x16 [--margin 0] [--spacing 0] --out frames/
    python sprite_sheet_slicer.py detect sheet.png --out frames/ [--min-area 4]
    python sprite_sheet_slicer.py aseprite sheet.json --out frames/
    ... [--tres res://art/hero.tres --res-path res://art/sheet.png --fps 10]
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class Frame:
    index: int
    x: int
    y: int
    w: int
    h: int
    name: str = ""
    duration_ms: int | None = None


@dataclass
class Tag:
    name: str
    start: int
    end: int
    direction: str = "forward"
    frames: list[int] = field(default_factory=list)


def _alpha(img: Image.Image) -> np.ndarray:
    rgba = img.convert("RGBA")
    return np.asarray(rgba)[:, :, 3]


def slice_grid(img: Image.Image, frame_w: int, frame_h: int, margin: int = 0, spacing: int = 0,
               count: int | None = None, skip_empty: bool = True) -> list[Frame]:
    """Frames of a regular grid, row-major. ``margin`` is the outer border, ``spacing`` the gap between cells."""
    if frame_w <= 0 or frame_h <= 0:
        raise ValueError("frame size must be positive")
    alpha = _alpha(img)
    W, H = img.size
    frames: list[Frame] = []
    y = margin
    while y + frame_h <= H:
        x = margin
        while x + frame_w <= W:
            cell = alpha[y:y + frame_h, x:x + frame_w]
            if not (skip_empty and not cell.any()):
                frames.append(Frame(len(frames), x, y, frame_w, frame_h, name=f"frame_{len(frames):03d}"))
                if count is not None and len(frames) >= count:
                    return frames
            x += frame_w + spacing
        y += frame_h + spacing
    return frames


def _runs(row: np.ndarray) -> list[tuple[int, int]]:
    """Half-open [start, end) runs of True in a 1-D bool array."""
    if not row.any():
        return []
    padded = np.concatenate(([False], row, [False])).astype(np.int8)
    d = np.diff(padded)
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    return list(zip(starts.tolist(), ends.tolist()))


def detect_sprites(img: Image.Image, alpha_threshold: int = 1, min_area: int = 4,
                   connectivity: int = 8, pad: int = 0) -> list[Frame]:
    """Bounding boxes of 4- or 8-connected opaque regions, sorted top-to-bottom then left-to-right."""
    mask = _alpha(img) >= alpha_threshold
    H, W = mask.shape
    parent: list[int] = []

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    run_rows: list[list[tuple[int, int, int]]] = []  # per row: (start, end, run_id)
    runs_meta: list[tuple[int, int, int]] = []  # run_id -> (y, start, end)
    grow = 1 if connectivity == 8 else 0
    prev: list[tuple[int, int, int]] = []
    for y in range(H):
        cur = []
        for s, e in _runs(mask[y]):
            rid = len(parent)
            parent.append(rid)
            runs_meta.append((y, s, e))
            for ps, pe, pid in prev:
                if ps < e + grow and s < pe + grow:
                    union(rid, pid)
            cur.append((s, e, rid))
        run_rows.append(cur)
        prev = cur
    boxes: dict[int, list[int]] = {}
    areas: dict[int, int] = {}
    for rid, (y, s, e) in enumerate(runs_meta):
        root = find(rid)
        b = boxes.get(root)
        if b is None:
            boxes[root] = [s, y, e, y + 1]
            areas[root] = e - s
        else:
            b[0], b[1], b[2], b[3] = min(b[0], s), min(b[1], y), max(b[2], e), max(b[3], y + 1)
            areas[root] += e - s
    rects = []
    for root, (x0, y0, x1, y1) in boxes.items():
        if areas[root] < min_area:
            continue
        x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
        x1, y1 = min(W, x1 + pad), min(H, y1 + pad)
        rects.append((y0, x0, x1 - x0, y1 - y0))
    rects.sort()
    return [Frame(i, x, y, w, h, name=f"sprite_{i:03d}") for i, (y, x, w, h) in enumerate(rects)]


def parse_aseprite_json(data: dict) -> tuple[list[Frame], list[Tag], dict]:
    """Frames, tags and meta from an Aseprite JSON export (``frames`` as hash or array)."""
    raw = data.get("frames", [])
    items = list(raw.items()) if isinstance(raw, dict) else [(f.get("filename", str(i)), f) for i, f in enumerate(raw)]
    frames = []
    for i, (name, f) in enumerate(items):
        r = f["frame"]
        frames.append(Frame(i, int(r["x"]), int(r["y"]), int(r["w"]), int(r["h"]), name=str(name),
                            duration_ms=int(f.get("duration", 100))))
    meta = data.get("meta", {})
    tags = []
    for t in meta.get("frameTags", []):
        start, end = int(t["from"]), int(t["to"])
        direction = t.get("direction", "forward")
        idx = list(range(start, end + 1))
        if direction == "reverse":
            idx.reverse()
        elif direction == "pingpong":
            idx = idx + idx[-2:0:-1]
        tags.append(Tag(t["name"], start, end, direction, idx))
    return frames, tags, meta


def export_frames(img: Image.Image, frames: list[Frame], out_dir: str | Path, prefix: str = "") -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rgba = img.convert("RGBA")
    paths = []
    for f in frames:
        p = out / f"{prefix}{f.index:03d}.png"
        rgba.crop((f.x, f.y, f.x + f.w, f.y + f.h)).save(p)
        paths.append(p)
    return paths


def _gd_str(s: str) -> str:
    return json.dumps(s)


def spriteframes_tres(sheet_res_path: str, frames: list[Frame], animations: dict[str, list[int]] | None = None,
                      fps: float = 10.0, loop: bool = True) -> str:
    """Godot 4 ``SpriteFrames`` text resource using ``AtlasTexture`` regions of one sheet.

    ``animations`` maps animation name -> frame indices (default: one ``default`` animation with all frames).
    Frame durations from Aseprite (ms) become Godot relative durations: duration_ms * fps / 1000.
    """
    if not sheet_res_path.startswith("res://"):
        raise ValueError("sheet_res_path must be a res:// path")
    animations = animations or {"default": [f.index for f in frames]}
    by_index = {f.index: f for f in frames}
    used = sorted({i for idx in animations.values() for i in idx})
    lines = ['[gd_resource type="SpriteFrames" format=3]', "",
             f'[ext_resource type="Texture2D" path={_gd_str(sheet_res_path)} id="1_sheet"]', ""]
    for i in used:
        f = by_index[i]
        lines += [f'[sub_resource type="AtlasTexture" id="AtlasTexture_{i}"]', 'atlas = ExtResource("1_sheet")',
                  f"region = Rect2({f.x}, {f.y}, {f.w}, {f.h})", ""]
    anim_dicts = []
    for name, idx in animations.items():
        frame_dicts = []
        for i in idx:
            f = by_index[i]
            rel = 1.0 if f.duration_ms is None else max(0.01, round(f.duration_ms * fps / 1000.0, 4))
            frame_dicts.append('{\n"duration": %s,\n"texture": SubResource("AtlasTexture_%d")\n}' % (rel, i))
        anim_dicts.append('{\n"frames": [%s],\n"loop": %s,\n"name": &%s,\n"speed": %s\n}'
                          % (", ".join(frame_dicts), "true" if loop else "false", _gd_str(name), float(fps)))
    lines += ["[resource]", "animations = [%s]" % ", ".join(anim_dicts)]
    return "\n".join(lines) + "\n"


def frames_json(frames: list[Frame], tags: list[Tag] | None = None, source: str = "") -> dict:
    return {"source": source, "frames": [asdict(f) for f in frames], "tags": [asdict(t) for t in (tags or [])]}


def _size(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("grid")
    g.add_argument("sheet")
    g.add_argument("--size", required=True, type=_size)
    g.add_argument("--margin", type=int, default=0)
    g.add_argument("--spacing", type=int, default=0)
    g.add_argument("--count", type=int)
    g.add_argument("--keep-empty", action="store_true")
    d = sub.add_parser("detect")
    d.add_argument("sheet")
    d.add_argument("--min-area", type=int, default=4)
    d.add_argument("--connectivity", type=int, choices=(4, 8), default=8)
    d.add_argument("--pad", type=int, default=0)
    a_ = sub.add_parser("aseprite")
    a_.add_argument("json")
    a_.add_argument("--sheet", help="sheet PNG (default: meta.image next to the JSON)")
    for p in (g, d, a_):
        p.add_argument("--out", required=True)
        p.add_argument("--tres", help="write a Godot SpriteFrames .tres to this file path")
        p.add_argument("--res-path", help="res:// path of the sheet inside the Godot project")
        p.add_argument("--fps", type=float, default=10.0)
    a = ap.parse_args(argv)
    tags: list[Tag] = []
    if a.cmd == "grid":
        img = Image.open(a.sheet)
        frames = slice_grid(img, *a.size, margin=a.margin, spacing=a.spacing, count=a.count,
                            skip_empty=not a.keep_empty)
        source = a.sheet
    elif a.cmd == "detect":
        img = Image.open(a.sheet)
        frames = detect_sprites(img, min_area=a.min_area, connectivity=a.connectivity, pad=a.pad)
        source = a.sheet
    else:
        data = json.loads(Path(a.json).read_text(encoding="utf-8"))
        frames, tags, meta = parse_aseprite_json(data)
        source = a.sheet or str(Path(a.json).with_name(meta.get("image", Path(a.json).stem + ".png")))
        img = Image.open(source)
    export_frames(img, frames, a.out)
    Path(a.out, "frames.json").write_text(json.dumps(frames_json(frames, tags, source), indent=2) + "\n")
    if a.tres:
        if not a.res_path:
            ap.error("--tres needs --res-path res://...")
        anims = {t.name: t.frames for t in tags} or None
        Path(a.tres).write_text(spriteframes_tres(a.res_path, frames, anims, fps=a.fps), encoding="utf-8")
    print(f"{len(frames)} frame(s) -> {a.out}")
    return 0 if frames else 1


if __name__ == "__main__":
    sys.exit(main())
