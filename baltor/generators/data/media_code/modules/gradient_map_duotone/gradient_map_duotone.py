"""Gradient maps and duotones: recolour an image by its brightness (numpy).

Maps each pixel's Rec. 709 luma through a multi-stop colour gradient
(positions 0-1 with hex colours). Two stops make a duotone (shadows colour,
highlights colour); three or more make richer maps. ``amount`` mixes the
mapped image with the original, and ``contrast`` adjusts luma before
mapping. Useful for consistent branded looks across mismatched photos.

Usage::

    from gradient_map_duotone import gradient_map, DUOTONES
    out = gradient_map(img, DUOTONES["navy_yellow"], amount=0.85)
    out = gradient_map(img, [(0, "#0E1116"), (0.5, "#2A9D8F"), (1, "#FFD21F")])
"""

from __future__ import annotations

import numpy as np

DUOTONES = {
    "navy_yellow": [(0.0, "#0B1D3A"), (1.0, "#FFD21F")],
    "plum_peach": [(0.0, "#2B0F3A"), (1.0, "#FFB38A")],
    "teal_cream": [(0.0, "#04363D"), (1.0, "#F4EBD0")],
    "charcoal_mint": [(0.0, "#1F2421"), (1.0, "#A8E6CF")],
}


def _rgb(h):
    s = h.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float64) / 255.0


def gradient_lut(stops) -> np.ndarray:
    stops = sorted((float(p), c) for p, c in stops)
    if len(stops) < 2 or stops[0][0] > 0 or stops[-1][0] < 1:
        raise ValueError("need at least two stops covering 0 and 1")
    pos = np.array([p for p, _ in stops])
    cols = np.array([_rgb(c) for _, c in stops])
    x = np.linspace(0, 1, 256)
    return np.stack([np.interp(x, pos, cols[:, k]) for k in range(3)], -1)


def gradient_map(img: np.ndarray, stops, amount: float = 1.0, contrast: float = 1.0) -> np.ndarray:
    if not 0 <= amount <= 1:
        raise ValueError("amount must be within [0, 1]")
    a = np.asarray(img)
    rgb = a[..., :3].astype(np.float64) / 255.0
    luma = rgb @ np.array([0.2126, 0.7152, 0.0722])
    luma = np.clip(0.5 + (luma - 0.5) * contrast, 0, 1)
    mapped = gradient_lut(stops)[(luma * 255 + 0.5).astype(int)]
    out = rgb * (1 - amount) + mapped * amount
    out = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    return np.concatenate([out, a[..., 3:4]], -1) if a.shape[-1] == 4 else out
