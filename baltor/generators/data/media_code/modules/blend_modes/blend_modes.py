"""Separable blend modes from the W3C Compositing and Blending spec (numpy).

Implements multiply, screen, overlay, darken, lighten, color-dodge,
color-burn, hard-light, soft-light, difference and exclusion with the spec's
formulas on float RGB in [0, 1], plus ``add`` (linear dodge, clipped).
``blend(backdrop, source, mode, opacity, source_alpha)`` mixes the blended
result with the backdrop by opacity, which is how editors apply a layer's
blend mode.

Usage::

    from blend_modes import blend
    out = blend(frame_rgb, light_leak_rgb, "screen", opacity=0.35)    # float 0-1 arrays
"""

from __future__ import annotations

import numpy as np


def _hard_light(cb, cs):
    return np.where(cs <= 0.5, cb * 2 * cs, cb + (2 * cs - 1) - cb * (2 * cs - 1))


def _soft_light(cb, cs):
    d = np.where(cb <= 0.25, ((16 * cb - 12) * cb + 4) * cb, np.sqrt(cb))
    return np.where(cs <= 0.5, cb - (1 - 2 * cs) * cb * (1 - cb), cb + (2 * cs - 1) * (d - cb))


def _dodge(cb, cs):
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.minimum(1.0, cb / np.maximum(1 - cs, 1e-12))
    return np.where(cb == 0, 0.0, np.where(cs >= 1, 1.0, r))


def _burn(cb, cs):
    with np.errstate(divide="ignore", invalid="ignore"):
        r = 1 - np.minimum(1.0, (1 - cb) / np.maximum(cs, 1e-12))
    return np.where(cb >= 1, 1.0, np.where(cs <= 0, 0.0, r))


MODES = {
    "normal": lambda cb, cs: cs,
    "multiply": lambda cb, cs: cb * cs,
    "screen": lambda cb, cs: cb + cs - cb * cs,
    "overlay": lambda cb, cs: _hard_light(cs, cb),
    "darken": np.minimum,
    "lighten": np.maximum,
    "color-dodge": _dodge,
    "color-burn": _burn,
    "hard-light": _hard_light,
    "soft-light": _soft_light,
    "difference": lambda cb, cs: np.abs(cb - cs),
    "exclusion": lambda cb, cs: cb + cs - 2 * cb * cs,
    "add": lambda cb, cs: np.minimum(1.0, cb + cs),
}


def blend(backdrop: np.ndarray, source: np.ndarray, mode: str = "normal", opacity: float = 1.0,
          source_alpha: np.ndarray | None = None) -> np.ndarray:
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; known: {', '.join(MODES)}")
    if backdrop.shape != source.shape:
        raise ValueError("backdrop and source must have the same shape")
    cb = np.clip(backdrop.astype(np.float64), 0, 1)
    cs = np.clip(source.astype(np.float64), 0, 1)
    mixed = MODES[mode](cb, cs)
    a = opacity if source_alpha is None else opacity * source_alpha[..., None]
    return (1 - a) * cb + a * mixed
