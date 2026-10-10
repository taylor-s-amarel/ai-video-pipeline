"""Auto levels: stretch black and white points from percentiles, set midtones.

Computes black/white input points from low/high percentiles (per channel or
from luma so colours do not shift), an optional gamma that moves the median
toward a target midtone, and returns a 256-entry lookup table per channel.
``apply`` uses it on uint8 images; ``ffmpeg_colorlevels`` produces the same
correction as an ffmpeg ``colorlevels`` filter for video.

Usage::

    from auto_levels import compute, apply, ffmpeg_colorlevels
    params = compute(img, low=0.5, high=99.5, mode="luma", target_mid=0.45)
    out = apply(img, params)
"""

from __future__ import annotations

import math

import numpy as np


def compute(img: np.ndarray, low: float = 0.5, high: float = 99.5, mode: str = "luma",
            target_mid: float | None = None, max_gamma: float = 2.0) -> dict:
    a = np.asarray(img, dtype=np.float64)[..., :3]
    if mode == "luma":
        luma = a @ np.array([0.2126, 0.7152, 0.0722])
        lo, hi = np.percentile(luma, [low, high])
        lows, highs = [lo] * 3, [hi] * 3
        med = float(np.median(luma))
    elif mode == "channels":
        lows = [float(np.percentile(a[..., c], low)) for c in range(3)]
        highs = [float(np.percentile(a[..., c], high)) for c in range(3)]
        med = float(np.median(a.mean(axis=2)))
        lo, hi = float(np.mean(lows)), float(np.mean(highs))
    else:
        raise ValueError("mode must be luma or channels")
    if any(h - l < 1 for l, h in zip(lows, highs)):
        return {"low": [0.0] * 3, "high": [255.0] * 3, "gamma": 1.0}
    gamma = 1.0
    if target_mid is not None:
        m = min(max((med - lo) / max(hi - lo, 1e-9), 1e-3), 1 - 1e-3)
        gamma = math.log(target_mid) / math.log(m)
        gamma = min(max(gamma, 1 / max_gamma), max_gamma)
    return {"low": [round(float(x), 3) for x in lows], "high": [round(float(x), 3) for x in highs],
            "gamma": round(gamma, 4)}


def lut(params: dict) -> np.ndarray:
    x = np.arange(256, dtype=np.float64)
    out = np.zeros((3, 256))
    for c in range(3):
        t = np.clip((x - params["low"][c]) / (params["high"][c] - params["low"][c]), 0, 1)
        out[c] = np.power(t, params["gamma"]) * 255
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def apply(img: np.ndarray, params: dict) -> np.ndarray:
    a = np.asarray(img)
    table = lut(params)
    out = a.copy()
    for c in range(3):
        out[..., c] = table[c][a[..., c]]
    return out


def ffmpeg_colorlevels(params: dict) -> str:
    """colorlevels filter (input points as 0-1); gamma is not part of colorlevels and is added with eq."""
    lo, hi = params["low"], params["high"]
    s = (f"colorlevels=rimin={lo[0] / 255:.4f}:gimin={lo[1] / 255:.4f}:bimin={lo[2] / 255:.4f}:"
         f"rimax={hi[0] / 255:.4f}:gimax={hi[1] / 255:.4f}:bimax={hi[2] / 255:.4f}")
    if abs(params["gamma"] - 1) > 1e-6:
        s += f",eq=gamma={1 / params['gamma']:.4f}"
    return s
