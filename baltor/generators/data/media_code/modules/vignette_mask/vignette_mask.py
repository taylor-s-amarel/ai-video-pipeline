"""Vignettes: numpy darkening masks and ffmpeg ``vignette`` parameters.

``vignette`` returns a multiplier array in [1 - strength, 1]: 1 in the
centre, darker towards the corners, with an aspect-aware ellipse, an inner
radius where darkening starts and a smoothstep falloff. ``apply`` multiplies
an RGB frame by it. ``ffmpeg_vignette`` builds the ffmpeg filter, whose
``angle`` (lens angle in radians, default PI/5 in ffmpeg) controls strength.

Usage::

    from vignette_mask import vignette, apply, ffmpeg_vignette
    frame = apply(frame, vignette(1080, 1920, strength=0.35, inner=0.55))
    vf = ffmpeg_vignette(angle_deg=30)
"""

from __future__ import annotations

import math

import numpy as np


def vignette(w: int, h: int, strength: float = 0.35, inner: float = 0.5, outer: float = 1.15,
             center=(0.5, 0.5)) -> np.ndarray:
    if not 0 <= strength <= 1:
        raise ValueError("strength must be within [0, 1]")
    if not 0 <= inner < outer:
        raise ValueError("need 0 <= inner < outer")
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xs + 0.5) / w - center[0]
    ny = (ys + 0.5) / h - center[1]
    r = np.hypot(nx * 2, ny * 2) / math.sqrt(2)  # 1.0 at the corners of a centred frame
    t = np.clip((r - inner) / (outer - inner), 0, 1)
    t = t * t * (3 - 2 * t)
    return (1.0 - strength * t).astype(np.float32)


def apply(frame: np.ndarray, mask: np.ndarray) -> np.ndarray:
    if frame.shape[:2] != mask.shape:
        raise ValueError("mask must match the frame size")
    out = frame.astype(np.float32) * (mask[..., None] if frame.ndim == 3 else mask)
    return np.clip(out + 0.5, 0, 255).astype(np.uint8) if frame.dtype == np.uint8 else out


def ffmpeg_vignette(angle_deg: float = 36.0, x0: str | None = None, y0: str | None = None,
                    eval_per_frame: bool = False) -> str:
    if not 0 < angle_deg < 90:
        raise ValueError("angle must be within (0, 90) degrees")
    s = f"vignette=angle={math.radians(angle_deg):.5f}"
    if x0 is not None:
        s += f":x0='{x0}'"
    if y0 is not None:
        s += f":y0='{y0}'"
    if eval_per_frame:
        s += ":eval=frame"
    return s
