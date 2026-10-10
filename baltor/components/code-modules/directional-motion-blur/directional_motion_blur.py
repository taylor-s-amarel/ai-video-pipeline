"""Directional (linear) motion blur for whip pans and fast moves (numpy).

``motion_blur`` averages ``samples`` copies of the frame shifted along a line
of ``length`` pixels at ``angle_deg`` (bilinear sub-pixel shifts, edge pixels
repeated), which is what a camera shutter records during fast motion.
``whip_pan_profile`` gives the blur length per frame for a whip-pan cut: it
ramps up to ``peak_px`` at the cut and back down.

Usage::

    from directional_motion_blur import motion_blur, whip_pan_profile
    blurred = motion_blur(frame, length=60, angle_deg=0)
    lengths = whip_pan_profile(frames=12, peak_px=120)
"""

from __future__ import annotations

import math

import numpy as np


def _shift(img: np.ndarray, dx: float, dy: float) -> np.ndarray:
    h, w = img.shape[:2]
    ys = np.clip(np.arange(h, dtype=np.float32) - dy, 0, h - 1)
    xs = np.clip(np.arange(w, dtype=np.float32) - dx, 0, w - 1)
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    y1 = np.minimum(y0 + 1, h - 1)
    x1 = np.minimum(x0 + 1, w - 1)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    if img.ndim == 3:
        fy, fx = fy[..., None], fx[..., None]
    top = img[y0][:, x0] * (1 - fx) + img[y0][:, x1] * fx
    bot = img[y1][:, x0] * (1 - fx) + img[y1][:, x1] * fx
    return top * (1 - fy) + bot * fy


def motion_blur(img: np.ndarray, length: float, angle_deg: float = 0.0, samples: int | None = None) -> np.ndarray:
    if length <= 0:
        return img.copy()
    src = img.astype(np.float32)
    n = samples or max(2, int(math.ceil(length)) + 1)
    a = math.radians(angle_deg)
    acc = np.zeros_like(src)
    for i in range(n):
        s = (i / (n - 1) - 0.5) * length
        acc += _shift(src, s * math.cos(a), s * math.sin(a))
    out = acc / n
    if img.dtype == np.uint8:
        return np.clip(out + 0.5, 0, 255).astype(np.uint8)
    return out.astype(img.dtype)


def whip_pan_profile(frames: int, peak_px: float = 100.0) -> list[float]:
    """Blur lengths for ``frames`` frames centred on the cut (sin^2 bell)."""
    if frames < 1:
        raise ValueError("frames must be >= 1")
    return [peak_px * math.sin(math.pi * (i + 0.5) / frames) ** 2 for i in range(frames)]


def blur_kernel(length: int, angle_deg: float, size: int | None = None) -> np.ndarray:
    """Normalised line kernel (for use with any convolution routine)."""
    size = size or (length | 1)
    k = np.zeros((size, size), np.float32)
    c = size // 2
    a = math.radians(angle_deg)
    steps = max(2, length * 4)
    for i in range(steps):
        s = (i / (steps - 1) - 0.5) * (length - 1)
        x, y = int(round(c + s * math.cos(a))), int(round(c + s * math.sin(a)))
        if 0 <= x < size and 0 <= y < size:
            k[y, x] = 1.0
    return k / k.sum()
