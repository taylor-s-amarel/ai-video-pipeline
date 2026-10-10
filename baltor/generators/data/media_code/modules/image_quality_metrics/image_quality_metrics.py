"""Full-reference image quality: MSE, PSNR and SSIM (numpy only).

Compare a rendered or re-encoded frame with its reference to catch heavy
compression, wrong scaling or a broken filter.

* ``psnr``: 10*log10(peak^2 / MSE), infinite for identical images;
* ``ssim``: structural similarity (Wang et al. 2004) with an 11x11 Gaussian
  window (sigma 1.5), K1 = 0.01, K2 = 0.03, computed on luma for colour
  images; returns the mean SSIM and optionally the map.

Usage::

    from image_quality_metrics import psnr, ssim
    psnr(ref, test)          # dB
    ssim(ref, test)          # 0..1 (1 = identical)
"""

from __future__ import annotations

import math

import numpy as np


def _luma(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.float64)
    if a.ndim == 3:
        a = a[..., :3] @ np.array([0.299, 0.587, 0.114])
    return a


def mse(a: np.ndarray, b: np.ndarray) -> float:
    if a.shape != b.shape:
        raise ValueError("images must have the same shape")
    return float(np.mean((a.astype(np.float64) - b.astype(np.float64)) ** 2))


def psnr(a: np.ndarray, b: np.ndarray, peak: float = 255.0) -> float:
    m = mse(a, b)
    return math.inf if m == 0 else 10 * math.log10(peak * peak / m)


def _gauss_kernel(size: int = 11, sigma: float = 1.5) -> np.ndarray:
    x = np.arange(size) - size // 2
    g = np.exp(-(x ** 2) / (2 * sigma ** 2))
    return g / g.sum()


def _filter(img: np.ndarray, k: np.ndarray) -> np.ndarray:
    # separable 'valid' convolution
    r = len(k)
    tmp = np.apply_along_axis(lambda row: np.convolve(row, k, mode="valid"), 1, img)
    return np.apply_along_axis(lambda col: np.convolve(col, k, mode="valid"), 0, tmp) if tmp.shape[0] >= r else tmp


def ssim(a: np.ndarray, b: np.ndarray, peak: float = 255.0, return_map: bool = False):
    if a.shape != b.shape:
        raise ValueError("images must have the same shape")
    x, y = _luma(a), _luma(b)
    if min(x.shape) < 11:
        raise ValueError("images must be at least 11x11")
    k = _gauss_kernel()
    c1, c2 = (0.01 * peak) ** 2, (0.03 * peak) ** 2
    mx, my = _filter(x, k), _filter(y, k)
    sxx = _filter(x * x, k) - mx * mx
    syy = _filter(y * y, k) - my * my
    sxy = _filter(x * y, k) - mx * my
    smap = ((2 * mx * my + c1) * (2 * sxy + c2)) / ((mx * mx + my * my + c1) * (sxx + syy + c2))
    m = float(smap.mean())
    return (m, smap) if return_map else m
