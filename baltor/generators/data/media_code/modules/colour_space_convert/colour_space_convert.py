"""Colour conversions for numpy arrays: sRGB/linear, HSV, HSL, hex, luma.

Vectorised versions of the conversions video tools need all the time:

* ``srgb_to_linear`` / ``linear_to_srgb`` (IEC 61966-2-1 transfer curve),
  so blurs, blends and resizes can be done in linear light;
* ``rgb_to_hsv`` / ``hsv_to_rgb`` and ``rgb_to_hsl`` / ``hsl_to_rgb`` with
  hue in degrees [0, 360) and the rest in [0, 1];
* ``hex_to_rgb`` / ``rgb_to_hex`` and Rec. 709 luma.

Usage::

    from colour_space_convert import srgb_to_linear, rgb_to_hsv, hex_to_rgb
    lin = srgb_to_linear(img / 255.0)
"""

from __future__ import annotations

import numpy as np


def srgb_to_linear(c):
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(np.asarray(c, dtype=np.float64), 0, None)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


def luma709(rgb):
    rgb = np.asarray(rgb, dtype=np.float64)
    return rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722


def rgb_to_hsv(rgb):
    rgb = np.asarray(rgb, dtype=np.float64)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn
    h = np.zeros_like(mx)
    with np.errstate(divide="ignore", invalid="ignore"):
        h = np.where(mx == r, ((g - b) / d) % 6, h)
        h = np.where(mx == g, (b - r) / d + 2, h)
        h = np.where(mx == b, (r - g) / d + 4, h)
        h = np.where(d == 0, 0, h) * 60.0
        s = np.where(mx == 0, 0, d / mx)
    return np.stack([h % 360, s, mx], -1)


def hsv_to_rgb(hsv):
    hsv = np.asarray(hsv, dtype=np.float64)
    h, s, v = hsv[..., 0] % 360, hsv[..., 1], hsv[..., 2]
    c = v * s
    x = c * (1 - np.abs((h / 60) % 2 - 1))
    m = v - c
    k = (h // 60).astype(int)
    zeros = np.zeros_like(h)
    table = [(c, x, zeros), (x, c, zeros), (zeros, c, x), (zeros, x, c), (x, zeros, c), (c, zeros, x)]
    r = np.choose(k % 6, [t[0] for t in table])
    g = np.choose(k % 6, [t[1] for t in table])
    b = np.choose(k % 6, [t[2] for t in table])
    return np.stack([r + m, g + m, b + m], -1)


def rgb_to_hsl(rgb):
    hsv = rgb_to_hsv(rgb)
    v, s_v = hsv[..., 2], hsv[..., 1]
    l = v * (1 - s_v / 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where((l == 0) | (l == 1), 0, (v - l) / np.minimum(l, 1 - l))
    return np.stack([hsv[..., 0], s, l], -1)


def hsl_to_rgb(hsl):
    hsl = np.asarray(hsl, dtype=np.float64)
    h, s, l = hsl[..., 0], hsl[..., 1], hsl[..., 2]
    v = l + s * np.minimum(l, 1 - l)
    with np.errstate(divide="ignore", invalid="ignore"):
        sv = np.where(v == 0, 0, 2 * (1 - l / v))
    return hsv_to_rgb(np.stack([h, sv, v], -1))


def hex_to_rgb(h: str) -> tuple:
    s = h.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise ValueError(f"bad hex colour {h!r}")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb) -> str:
    r, g, b = (int(round(max(0, min(255, v)))) for v in rgb[:3])
    return f"#{r:02X}{g:02X}{b:02X}"
