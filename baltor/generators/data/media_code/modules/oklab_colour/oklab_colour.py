"""OKLab / OKLCH colour: perceptual palettes, ramps and gamut-safe tints.

Uses the OKLab transform published by Bjorn Ottosson (2020). Equal steps in
OKLab lightness look evenly spaced, so ramps (tints and shades of a brand
colour) and hue rotations stay balanced. Out-of-gamut colours are brought
back by reducing chroma at constant lightness and hue, not by clipping
channels (which shifts hue).

Usage::

    from oklab_colour import hex_to_oklch, oklch_to_hex, ramp, rotate_hue
    ramp("#FFD21F", steps=7)          # light to dark tints/shades with the same hue
    rotate_hue("#FFD21F", 180)        # perceptual complement
"""

from __future__ import annotations

import math

M1 = [[0.4122214708, 0.5363325363, 0.0514459929], [0.2119034982, 0.6806995451, 0.1073969566],
      [0.0883024619, 0.2817188376, 0.6299787005]]
M2 = [[0.2104542553, 0.7936177850, -0.0040720468], [1.9779984951, -2.4285922050, 0.4505937099],
      [0.0259040371, 0.7827717662, -0.8086757660]]
M2_INV = [[1.0, 0.3963377774, 0.2158037573], [1.0, -0.1055613458, -0.0638541728], [1.0, -0.0894841775, -1.2914855480]]
M1_INV = [[4.0767416621, -3.3077115913, 0.2309699292], [-1.2684380046, 2.6097574011, -0.3413193965],
          [-0.0041960863, -0.7034186147, 1.7076147010]]


def _mul(m, v):
    return [m[i][0] * v[0] + m[i][1] * v[1] + m[i][2] * v[2] for i in range(3)]


def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def srgb_to_oklab(rgb):
    lms = _mul(M1, [_lin(c) for c in rgb])
    return tuple(_mul(M2, [math.copysign(abs(x) ** (1 / 3), x) for x in lms]))


def oklab_to_srgb(lab, clip: bool = False):
    lms_ = _mul(M2_INV, lab)
    rgb_lin = _mul(M1_INV, [x ** 3 for x in lms_])
    out = [_gam(c) if c >= 0 else -_gam(-c) for c in rgb_lin]
    return tuple(min(1.0, max(0.0, c)) for c in out) if clip else tuple(out)


def to_lch(lab):
    L, a, b = lab
    return L, math.hypot(a, b), math.degrees(math.atan2(b, a)) % 360


def from_lch(L, C, h):
    return L, C * math.cos(math.radians(h)), C * math.sin(math.radians(h))


def in_gamut(rgb, eps: float = 1e-6) -> bool:
    return all(-eps <= c <= 1 + eps for c in rgb)


def gamut_map(L, C, h):
    """Largest chroma <= C that is inside sRGB at this lightness and hue (bisection)."""
    if in_gamut(oklab_to_srgb(from_lch(L, C, h))):
        return C
    lo, hi = 0.0, C
    for _ in range(40):
        mid = (lo + hi) / 2
        if in_gamut(oklab_to_srgb(from_lch(L, mid, h))):
            lo = mid
        else:
            hi = mid
    return lo


def _hex_rgb(h):
    s = h.lstrip("#")
    return [int(s[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def _rgb_hex(rgb):
    return "#" + "".join(f"{int(round(min(1, max(0, c)) * 255)):02X}" for c in rgb)


def hex_to_oklch(h):
    return to_lch(srgb_to_oklab(_hex_rgb(h)))


def oklch_to_hex(L, C, h):
    L = min(1.0, max(0.0, L))
    return _rgb_hex(oklab_to_srgb(from_lch(L, gamut_map(L, C, h), h), clip=True))


def ramp(base: str, steps: int = 7, l_min: float = 0.25, l_max: float = 0.95) -> list[str]:
    _, C, h = hex_to_oklch(base)
    return [oklch_to_hex(l_max - (l_max - l_min) * i / (steps - 1), C, h) for i in range(steps)]


def rotate_hue(base: str, degrees: float) -> str:
    L, C, h = hex_to_oklch(base)
    return oklch_to_hex(L, C, (h + degrees) % 360)


def delta_e(a: str, b: str) -> float:
    """Euclidean distance in OKLab (about 0.02 is a just-noticeable difference)."""
    return math.dist(srgb_to_oklab(_hex_rgb(a)), srgb_to_oklab(_hex_rgb(b)))
