"""Bloom / glow on bright areas (numpy + Pillow Gaussian blur).

Extracts highlights above ``threshold`` with a soft knee (no hard edge in
what glows), blurs them at one or more radii, and adds them back with
``screen`` (default) or ``add`` at ``intensity``. Works on uint8 RGB(A);
alpha is preserved. Good for light leaks, neon titles and dreamy looks.

Usage::

    from bloom_effect import bloom
    out = bloom(img, threshold=0.75, knee=0.1, radii=(8, 24), intensity=0.6)
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter


def highlights(rgb01: np.ndarray, threshold: float, knee: float) -> np.ndarray:
    luma = rgb01 @ np.array([0.2126, 0.7152, 0.0722])
    lo, hi = threshold - knee, threshold + knee
    w = np.clip((luma - lo) / max(hi - lo, 1e-6), 0, 1)
    w = w * w * (3 - 2 * w)
    return rgb01 * w[..., None]


def _blur(a: np.ndarray, radius: float) -> np.ndarray:
    img = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float64) / 255.0


def bloom(img: np.ndarray, threshold: float = 0.75, knee: float = 0.1, radii=(8, 24), intensity: float = 0.6,
          mode: str = "screen") -> np.ndarray:
    if mode not in ("screen", "add"):
        raise ValueError("mode must be screen or add")
    a = np.asarray(img)
    rgb = a[..., :3].astype(np.float64) / 255.0
    hl = highlights(rgb, threshold, knee)
    glow = sum(_blur(hl, r) for r in radii) / len(radii) * intensity
    out = 1 - (1 - rgb) * (1 - glow) if mode == "screen" else rgb + glow
    out = (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
    return np.concatenate([out, a[..., 3:4]], -1) if a.shape[-1] == 4 else out
