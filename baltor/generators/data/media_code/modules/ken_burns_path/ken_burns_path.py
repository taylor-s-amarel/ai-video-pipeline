"""Ken Burns pan/zoom paths: per-frame crop rectangles inside a still image.

A *view* is ``(cx, cy, zoom)`` in normalised image coordinates: (0.5, 0.5) is
the centre and zoom 1.0 is the largest crop with the output aspect ratio that
fits in the image. Crops are always kept inside the image (no black edges).
Zoom is interpolated in log space so the apparent zoom speed is constant.

Usage::

    from ken_burns_path import plan, preset
    start, end = preset("zoom_in", focus=(0.5, 0.35), strength=1.2)
    rects = plan((4000, 3000), (1080, 1920), start, end, frames=150)
    # each rect is (x, y, w, h) in source pixels, floats; crop then resize to 1080x1920
"""

from __future__ import annotations

import math
from typing import Sequence


def _ease(name: str, x: float) -> float:
    if name == "linear":
        return x
    if name == "in_out_sine":
        return -(math.cos(math.pi * x) - 1) / 2
    if name == "in_out_cubic":
        return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2
    if name == "out_quad":
        return 1 - (1 - x) ** 2
    raise ValueError(f"unknown easing {name!r}")


def base_crop(image_size: Sequence[float], out_size: Sequence[float]) -> tuple[float, float]:
    """Largest (w, h) with the output aspect that fits in the image."""
    iw, ih = image_size
    aspect = out_size[0] / out_size[1]
    if iw / ih > aspect:
        return ih * aspect, float(ih)
    return float(iw), iw / aspect


def view_rect(image_size, out_size, view) -> tuple[float, float, float, float]:
    cx, cy, zoom = view
    if zoom < 1.0:
        raise ValueError("zoom must be >= 1.0 (1.0 is the largest crop that fits)")
    iw, ih = image_size
    bw, bh = base_crop(image_size, out_size)
    w, h = bw / zoom, bh / zoom
    x = min(max(cx * iw - w / 2, 0.0), iw - w)
    y = min(max(cy * ih - h / 2, 0.0), ih - h)
    return x, y, w, h


def plan(image_size, out_size, start, end, frames: int, easing: str = "in_out_sine") -> list[tuple]:
    """Crop rectangles for ``frames`` frames moving from view ``start`` to view ``end``."""
    if frames < 1:
        raise ValueError("frames must be >= 1")
    out = []
    lz0, lz1 = math.log(start[2]), math.log(end[2])
    for i in range(frames):
        u = _ease(easing, i / (frames - 1) if frames > 1 else 1.0)
        view = (start[0] + (end[0] - start[0]) * u,
                start[1] + (end[1] - start[1]) * u,
                math.exp(lz0 + (lz1 - lz0) * u))
        out.append(view_rect(image_size, out_size, view))
    return out


PRESETS = ("zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up", "pan_down", "zoom_in_pan_right")


def preset(name: str, focus: tuple[float, float] = (0.5, 0.5), strength: float = 1.15):
    """Start and end views for a named move. ``strength`` is the zoom factor or pan zoom."""
    fx, fy = focus
    s = max(1.0, strength)
    pan = 0.5 - 0.5 / s  # how far the centre can travel at zoom s while staying inside
    moves = {
        "zoom_in": ((fx, fy, 1.0), (fx, fy, s)),
        "zoom_out": ((fx, fy, s), (fx, fy, 1.0)),
        "pan_left": ((0.5 + pan, fy, s), (0.5 - pan, fy, s)),
        "pan_right": ((0.5 - pan, fy, s), (0.5 + pan, fy, s)),
        "pan_up": ((fx, 0.5 + pan, s), (fx, 0.5 - pan, s)),
        "pan_down": ((fx, 0.5 - pan, s), (fx, 0.5 + pan, s)),
        "zoom_in_pan_right": ((0.5 - pan / 2, fy, 1.0 + (s - 1) / 2), (0.5 + pan / 2, fy, s)),
    }
    if name not in moves:
        raise KeyError(f"unknown preset {name!r}; known: {', '.join(PRESETS)}")
    return moves[name]


def min_source_scale(rects, out_size) -> float:
    """Smallest source-pixels-per-output-pixel ratio over the path (< 1 means upscaling)."""
    return min(r[2] / out_size[0] for r in rects)
