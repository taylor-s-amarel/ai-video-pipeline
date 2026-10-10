"""Feathered alpha masks (numpy, Pillow output): no hard rectangular cutouts.

Masks are float32 arrays in [0, 1] built from signed distance fields, so the
feather is an even soft edge of ``feather`` pixels:

* ``rounded_rect``: panel or photo mask with corner radius and feather;
* ``ellipse``: soft oval vignette-style cut-out;
* ``edge_fade``: linear fades on any of the four edges (fade a photo's bottom
  into the background);
* ``combine`` (multiply) and ``to_image`` (8-bit L-mode Pillow image, for
  ffmpeg ``alphamerge`` or Pillow ``putalpha``).

``max_alpha`` caps opacity (default 0.98, so no layer is fully opaque).

Usage::

    from feathered_alpha_mask import rounded_rect, edge_fade, combine, to_image
    m = combine(rounded_rect(1000, 1400, radius=48, feather=40), edge_fade(1000, 1400, bottom=220))
    to_image(m).save("photo_mask.png")
"""

from __future__ import annotations

import numpy as np
from PIL import Image


def _smooth(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def rounded_rect(w: int, h: int, radius: float = 32, feather: float = 24, inset: float = 0,
                 max_alpha: float = 0.98) -> np.ndarray:
    if w <= 0 or h <= 0:
        raise ValueError("size must be positive")
    if feather < 0 or radius < 0:
        raise ValueError("radius and feather must be >= 0")
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    hx = w / 2 - inset - feather / 2
    hy = h / 2 - inset - feather / 2
    r = min(radius, hx, hy)
    qx = np.abs(xs - cx) - (hx - r)
    qy = np.abs(ys - cy) - (hy - r)
    outside = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    if feather == 0:
        a = (outside <= 0).astype(np.float32)
    else:
        a = _smooth(0.5 - outside / feather)
    return (a * max_alpha).astype(np.float32)


def ellipse(w: int, h: int, feather: float = 40, scale: float = 1.0, max_alpha: float = 0.98) -> np.ndarray:
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    rx, ry = (w / 2) * scale, (h / 2) * scale
    nx, ny = (xs - (w - 1) / 2) / rx, (ys - (h - 1) / 2) / ry
    d = (np.hypot(nx, ny) - 1.0) * min(rx, ry)   # approx distance in px
    a = _smooth(0.5 - d / max(feather, 1e-6)) if feather > 0 else (d <= 0).astype(np.float32)
    return (a * max_alpha).astype(np.float32)


def edge_fade(w: int, h: int, top: float = 0, bottom: float = 0, left: float = 0, right: float = 0) -> np.ndarray:
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    a = np.ones((h, w), np.float32)
    for size, dist in ((top, ys), (bottom, h - 1 - ys), (left, xs), (right, w - 1 - xs)):
        if size > 0:
            a *= _smooth(dist / size)
    return a


def combine(*masks: np.ndarray) -> np.ndarray:
    out = np.ones_like(masks[0])
    for m in masks:
        if m.shape != out.shape:
            raise ValueError("masks must have the same shape")
        out *= m
    return out


def to_image(mask: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(mask * 255.0 + 0.5, 0, 255).astype(np.uint8), mode="L")


def apply_to(img: Image.Image, mask: np.ndarray) -> Image.Image:
    """Return an RGBA copy of ``img`` whose alpha is (existing alpha x mask)."""
    rgba = img.convert("RGBA")
    if (rgba.width, rgba.height) != (mask.shape[1], mask.shape[0]):
        raise ValueError("mask size must match the image")
    a = np.asarray(rgba)[..., 3].astype(np.float32) / 255.0 * mask
    rgba.putalpha(to_image(a))
    return rgba
