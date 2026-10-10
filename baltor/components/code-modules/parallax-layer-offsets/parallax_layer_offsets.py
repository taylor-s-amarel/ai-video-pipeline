"""2.5D parallax: per-layer screen offsets and scales from a pinhole camera.

Each layer is a flat card at distance ``depth`` from the camera at rest. When
the camera trucks by ``cam_x``/``cam_y`` (world units) and dollies forward by
``cam_z``, a layer moves on screen by ``-cam * focal / (depth - cam_z)`` pixels
and scales by ``depth / (depth - cam_z)``. Near layers move more than far
ones, which sells depth from flat photos and cut-outs.

``focal`` is in pixels per world unit at distance 1; ``focal_for`` picks it so
the focus layer moves a chosen number of pixels.

Usage::

    from parallax_layer_offsets import layer_transforms, focal_for, overscan_px
    f = focal_for(focus_depth=10, cam_travel=1.0, focus_shift_px=60)
    layer_transforms([2, 5, 10, 40], cam=(1.0, 0, 0.5), focal=f)
"""

from __future__ import annotations

import math


def layer_transform(depth: float, cam=(0.0, 0.0, 0.0), focal: float = 600.0) -> dict:
    cx, cy, cz = cam
    if depth <= 0:
        raise ValueError("depth must be > 0")
    if math.isinf(depth):
        return {"depth": depth, "dx": 0.0, "dy": 0.0, "scale": 1.0}
    dist = depth - cz
    if dist <= 0:
        raise ValueError(f"camera passed through the layer at depth {depth}")
    return {"depth": depth, "dx": -cx * focal / dist, "dy": -cy * focal / dist, "scale": depth / dist}


def layer_transforms(depths, cam=(0.0, 0.0, 0.0), focal: float = 600.0) -> list[dict]:
    return [layer_transform(d, cam, focal) for d in depths]


def focal_for(focus_depth: float, cam_travel: float, focus_shift_px: float) -> float:
    """Focal so the layer at ``focus_depth`` shifts ``focus_shift_px`` for ``cam_travel`` units."""
    if cam_travel == 0:
        raise ValueError("cam_travel must be non-zero")
    return abs(focus_shift_px) * focus_depth / abs(cam_travel)


def overscan_px(depth: float, path, focal: float, width: int, height: int) -> tuple[int, int]:
    """Extra pixels each side a layer image needs so no edge shows along a camera ``path``."""
    need_x = need_y = 0.0
    for cam in path:
        t = layer_transform(depth, cam, focal)
        # scaling about the centre also needs margin when scale < 1 (dolly out)
        sx = max(0.0, (1 - t["scale"]) * width / 2)
        sy = max(0.0, (1 - t["scale"]) * height / 2)
        need_x = max(need_x, abs(t["dx"]) + sx)
        need_y = max(need_y, abs(t["dy"]) + sy)
    return math.ceil(need_x), math.ceil(need_y)


def linear_path(start, end, frames: int) -> list[tuple]:
    if frames < 2:
        return [tuple(end)]
    return [tuple(a + (b - a) * i / (frames - 1) for a, b in zip(start, end)) for i in range(frames)]
