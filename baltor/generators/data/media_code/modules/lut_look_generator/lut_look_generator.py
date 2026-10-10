"""Generate colour-grade looks as 3D LUTs (.cube) from named recipes.

Each look is a small, documented function of RGB (0-1 floats) baked into a
LUT of size N (default 17) and written as .cube text for ffmpeg ``lut3d`` or
any editor:

* ``warm`` / ``cool``: white-balance style channel gains;
* ``teal_orange``: shadows pushed toward teal, highlights toward orange, by
  luma, with saturation kept in check;
* ``bleach_bypass``: partial desaturation with extra contrast;
* ``matte``: lifted blacks and softened highlights (a faded film feel);
* ``mono_contrast``: Rec. 709 luma black-and-white with an S-curve;
* ``vintage_fade``: matte plus reduced saturation and a slight yellow cast.

``strength`` blends each look with identity.

Usage::

    from lut_look_generator import make_lut, cube_text, LOOKS
    open("teal_orange.cube", "w").write(cube_text("teal_orange", size=17, strength=0.8))
"""

from __future__ import annotations

import numpy as np

W709 = np.array([0.2126, 0.7152, 0.0722])


def _luma(c):
    return (c @ W709)[..., None]


def _sat(c, s):
    l = _luma(c)
    return np.clip(l + (c - l) * s, 0, 1)


def warm(c):
    return np.clip(c * np.array([1.06, 1.0, 0.90]), 0, 1)


def cool(c):
    return np.clip(c * np.array([0.92, 1.0, 1.08]), 0, 1)


def teal_orange(c):
    l = _luma(c)
    teal, orange = np.array([0.0, 0.5, 0.55]), np.array([1.0, 0.62, 0.35])
    shadow_w = np.clip(1 - l / 0.5, 0, 1) * 0.25
    high_w = np.clip((l - 0.5) / 0.5, 0, 1) * 0.22
    out = c * (1 - shadow_w - high_w) + teal * shadow_w * (l + 0.2) + orange * high_w * l
    return _sat(np.clip(out, 0, 1), 0.95)


def bleach_bypass(c):
    l = _luma(c)
    mixed = c * 0.45 + l * 0.55
    return np.clip(0.5 + (mixed - 0.5) * 1.25, 0, 1)


def matte(c):
    return 0.06 + c * (0.92 - 0.06)


def mono_contrast(c):
    l = _luma(c)
    l = np.clip(0.5 + (l - 0.5) * 1.2, 0, 1)
    return np.repeat(l, 3, axis=-1)


def vintage_fade(c):
    out = _sat(matte(c), 0.75)
    return np.clip(out * np.array([1.04, 1.01, 0.90]) + np.array([0.01, 0.01, 0.0]), 0, 1)


LOOKS = {"warm": warm, "cool": cool, "teal_orange": teal_orange, "bleach_bypass": bleach_bypass,
         "matte": matte, "mono_contrast": mono_contrast, "vintage_fade": vintage_fade}


def identity(n: int) -> np.ndarray:
    g = np.linspace(0, 1, n)
    b, gg, r = np.meshgrid(g, g, g, indexing="ij")
    return np.stack([r, gg, b], -1)


def make_lut(look: str, size: int = 17, strength: float = 1.0) -> np.ndarray:
    if look not in LOOKS:
        raise ValueError(f"unknown look {look!r}; known: {', '.join(LOOKS)}")
    if not 0 <= strength <= 1:
        raise ValueError("strength must be within [0, 1]")
    base = identity(size)
    graded = LOOKS[look](base.reshape(-1, 3)).reshape(base.shape)
    return np.clip(base + (graded - base) * strength, 0, 1)


def cube_text(look: str, size: int = 17, strength: float = 1.0) -> str:
    lut = make_lut(look, size, strength)
    lines = [f'TITLE "{look} {strength:g}"', f"LUT_3D_SIZE {size}", "DOMAIN_MIN 0.0 0.0 0.0", "DOMAIN_MAX 1.0 1.0 1.0"]
    lines += [f"{r:.6f} {g:.6f} {b:.6f}" for r, g, b in lut.reshape(-1, 3)]
    return "\n".join(lines) + "\n"
