"""Sharpness and noise estimates for photos and frames (numpy).

* ``laplacian_variance``: variance of the 3x3 Laplacian response, the common
  blur measure (low values mean soft or out-of-focus images; compare within
  the same resolution and content type);
* ``noise_sigma``: Immerkaer's fast noise estimate (1996), which filters with
  a mask that cancels image structure to second order and estimates the
  standard deviation of additive Gaussian noise;
* ``check``: flags images below a sharpness floor or above a noise ceiling,
  after resizing to a fixed width so results are comparable.

Usage::

    from sharpness_noise_check import check
    check(gray_array)    # {'sharpness': 412.3, 'noise_sigma': 2.1, 'flags': []}
"""

from __future__ import annotations

import math

import numpy as np


def _gray(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    return a[..., :3] @ np.array([0.2126, 0.7152, 0.0722]) if a.ndim == 3 else a


def _conv3(img: np.ndarray, k: np.ndarray) -> np.ndarray:
    H, W = img.shape
    out = np.zeros((H - 2, W - 2))
    for dy in range(3):
        for dx in range(3):
            if k[dy, dx]:
                out += k[dy, dx] * img[dy:dy + H - 2, dx:dx + W - 2]
    return out


LAPLACE = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], float)
IMMERKAER = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], float)


def laplacian_variance(img) -> float:
    return float(_conv3(_gray(img), LAPLACE).var())


def noise_sigma(img) -> float:
    g = _gray(img)
    H, W = g.shape
    if H < 3 or W < 3:
        raise ValueError("image too small")
    s = np.abs(_conv3(g, IMMERKAER)).sum()
    return float(s * math.sqrt(0.5 * math.pi) / (6 * (W - 2) * (H - 2)))


def _resize_width(g: np.ndarray, width: int) -> np.ndarray:
    H, W = g.shape
    if W <= width:
        return g
    ys = (np.arange(int(H * width / W)) * W / width).astype(int)
    xs = (np.arange(width) * W / width).astype(int)
    return g[ys][:, xs]


def check(img, width: int = 540, min_sharpness: float = 60.0, max_noise: float = 8.0) -> dict:
    g = _resize_width(_gray(img), width)
    s, n = laplacian_variance(g), noise_sigma(g)
    flags = []
    if s < min_sharpness:
        flags.append("soft")
    if n > max_noise:
        flags.append("noisy")
    return {"sharpness": round(s, 2), "noise_sigma": round(n, 3), "flags": flags}
