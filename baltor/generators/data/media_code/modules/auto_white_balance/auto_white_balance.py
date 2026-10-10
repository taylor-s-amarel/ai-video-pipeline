"""Automatic white balance for photos and frames (numpy).

Estimates the illuminant colour and applies diagonal (von Kries style)
channel gains in linear light, with the green channel fixed:

* ``gray_world``: average scene colour is assumed neutral;
* ``white_patch``: the brightest pixels (a high percentile) are neutral;
* ``shades_of_gray``: Minkowski p-norm mean (Finlayson and Trezzi, 2004),
  between the two (p=6 is a common choice).

Gains are clamped (default 0.5-2.0) so a frame dominated by one colour (a
red wall, a blue sky) is not overcorrected; ``strength`` blends toward no
correction.

Usage::

    from auto_white_balance import correct
    fixed = correct(img_uint8, method="shades_of_gray", strength=0.8)
"""

from __future__ import annotations

import numpy as np


def _lin(a):
    return np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)


def _enc(a):
    a = np.clip(a, 0, 1)
    return np.where(a <= 0.0031308, a * 12.92, 1.055 * np.power(a, 1 / 2.4) - 0.055)


def estimate(lin: np.ndarray, method: str = "shades_of_gray", p: float = 6.0, percentile: float = 99.0) -> np.ndarray:
    px = lin.reshape(-1, 3)
    if method == "gray_world":
        est = px.mean(axis=0)
    elif method == "white_patch":
        lum = px @ np.array([0.2126, 0.7152, 0.0722])
        sel = px[lum >= np.percentile(lum, percentile)]
        est = sel.mean(axis=0)
    elif method == "shades_of_gray":
        est = np.power(np.mean(np.power(px, p), axis=0), 1 / p)
    else:
        raise ValueError("method must be gray_world, white_patch or shades_of_gray")
    return est


def gains(img: np.ndarray, method: str = "shades_of_gray", clamp=(0.5, 2.0), **kw) -> np.ndarray:
    lin = _lin(np.asarray(img, dtype=np.float64)[..., :3] / 255.0)
    est = np.maximum(estimate(lin, method, **kw), 1e-6)
    g = est[1] / est
    return np.clip(g, *clamp)


def correct(img: np.ndarray, method: str = "shades_of_gray", strength: float = 1.0, **kw) -> np.ndarray:
    if not 0 <= strength <= 1:
        raise ValueError("strength must be within [0, 1]")
    a = np.asarray(img)
    g = gains(a, method, **kw)
    g = 1 + (g - 1) * strength
    lin = _lin(a[..., :3].astype(np.float64) / 255.0) * g
    out = (_enc(lin) * 255.0 + 0.5).astype(np.uint8)
    if a.shape[-1] == 4:
        out = np.concatenate([out, a[..., 3:4]], -1)
    return out
