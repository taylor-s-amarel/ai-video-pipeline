"""Porter-Duff alpha compositing in numpy (straight and premultiplied).

* ``premultiply`` / ``unpremultiply`` convert RGBA float arrays;
* ``over(src, dst)`` composites straight-alpha RGBA (float 0-1) correctly,
  including transparent backdrops;
* ``place(canvas, layer, x, y, opacity)`` composites a smaller layer at a
  position with clipping at the canvas edges;
* ``stack(size, layers)`` builds a frame from a list of layers bottom-up
  with per-layer opacity (capped at 0.98 by default).

Usage::

    from alpha_compositing import stack, to_float, to_uint8
    frame = stack((1080, 1920), [(bg, 0, 0, 0.92), (photo, 54, 300, 0.98), (title, 90, 320, 0.98)])
"""

from __future__ import annotations

import numpy as np


def to_float(img) -> np.ndarray:
    a = np.asarray(img)
    if a.ndim == 2:
        a = np.stack([a, a, a, np.full_like(a, 255)], -1)
    if a.shape[2] == 3:
        a = np.concatenate([a, np.full(a.shape[:2] + (1,), 255, a.dtype)], -1)
    return a.astype(np.float32) / 255.0 if a.dtype == np.uint8 else a.astype(np.float32)


def to_uint8(a: np.ndarray) -> np.ndarray:
    return np.clip(a * 255.0 + 0.5, 0, 255).astype(np.uint8)


def premultiply(a: np.ndarray) -> np.ndarray:
    out = a.copy()
    out[..., :3] *= a[..., 3:4]
    return out


def unpremultiply(a: np.ndarray) -> np.ndarray:
    out = a.copy()
    alpha = a[..., 3:4]
    out[..., :3] = np.where(alpha > 0, a[..., :3] / np.maximum(alpha, 1e-12), 0.0)
    return out


def over(src: np.ndarray, dst: np.ndarray) -> np.ndarray:
    """Straight-alpha src OVER straight-alpha dst (same shape, float 0-1)."""
    ps, pd = premultiply(src), premultiply(dst)
    a_s = src[..., 3:4]
    out = ps + pd * (1 - a_s)
    return unpremultiply(out)


def place(canvas: np.ndarray, layer: np.ndarray, x: int, y: int, opacity: float = 1.0) -> np.ndarray:
    H, W = canvas.shape[:2]
    h, w = layer.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return canvas
    src = layer[y0 - y:y1 - y, x0 - x:x1 - x].copy()
    src[..., 3] *= opacity
    out = canvas.copy()
    out[y0:y1, x0:x1] = over(src, canvas[y0:y1, x0:x1])
    return out


def stack(size, layers, background=(0, 0, 0, 1), max_opacity: float = 0.98) -> np.ndarray:
    W, H = size
    canvas = np.empty((H, W, 4), np.float32)
    canvas[:] = background
    for i, item in enumerate(layers):
        img, x, y, op = item
        if op > max_opacity:
            raise ValueError(f"layer {i}: opacity {op} > {max_opacity}")
        canvas = place(canvas, to_float(img), int(x), int(y), op)
    return canvas
