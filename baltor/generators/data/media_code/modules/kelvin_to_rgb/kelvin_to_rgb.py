"""Colour temperature (kelvin) to sRGB, and white-balance gains.

Computes the colour of a black body at temperature T: Planck's law weighted
by CIE 1931 colour-matching functions, using the analytic multi-lobe
Gaussian fit of Wyman, Sloan and Shirley (JCGT 2013) so no data tables are
needed, then XYZ -> linear sRGB. Results are normalised so the largest
channel is 1.

``wb_gains(from_k, to_k)`` gives per-channel multipliers that shift footage
lit at ``from_k`` to look as if lit at ``to_k`` (warm up or cool down a
grade); ``ffmpeg_colorchannelmixer`` turns gains into an ffmpeg filter.

Usage::

    from kelvin_to_rgb import kelvin_rgb, wb_gains, ffmpeg_colorchannelmixer
    kelvin_rgb(3200)                  # warm tungsten-like (r > g > b)
    ffmpeg_colorchannelmixer(wb_gains(6500, 5000))
"""

from __future__ import annotations

import math

H, C, KB = 6.62607015e-34, 2.99792458e8, 1.380649e-23
XYZ_TO_SRGB = ((3.2406, -1.5372, -0.4986), (-0.9689, 1.8758, 0.0415), (0.0557, -0.2040, 1.0570))


def _g(x, mu, s1, s2):
    t = (x - mu) / (s1 if x < mu else s2)
    return math.exp(-0.5 * t * t)


def cmf(wl_nm: float) -> tuple[float, float, float]:
    """CIE 1931 2-degree colour matching functions, Wyman et al. 2013 multi-lobe fit."""
    x = 1.056 * _g(wl_nm, 599.8, 37.9, 31.0) + 0.362 * _g(wl_nm, 442.0, 16.0, 26.7) - 0.065 * _g(wl_nm, 501.1, 20.4, 26.2)
    y = 0.821 * _g(wl_nm, 568.8, 46.9, 40.5) + 0.286 * _g(wl_nm, 530.9, 16.3, 31.1)
    z = 1.217 * _g(wl_nm, 437.0, 11.8, 36.0) + 0.681 * _g(wl_nm, 459.0, 26.0, 13.8)
    return x, y, z


def planck(wl_nm: float, kelvin: float) -> float:
    lam = wl_nm * 1e-9
    return (2 * H * C * C) / (lam ** 5 * (math.exp(H * C / (lam * KB * kelvin)) - 1))


def kelvin_xyz(kelvin: float) -> tuple[float, float, float]:
    if not 1000 <= kelvin <= 40000:
        raise ValueError("kelvin must be within 1000-40000")
    X = Y = Z = 0.0
    for wl in range(380, 781, 5):
        p = planck(wl, kelvin)
        x, y, z = cmf(wl)
        X, Y, Z = X + p * x, Y + p * y, Z + p * z
    return X / Y, 1.0, Z / Y


def kelvin_linear_rgb(kelvin: float) -> tuple[float, float, float]:
    xyz = kelvin_xyz(kelvin)
    rgb = [max(0.0, sum(m * v for m, v in zip(row, xyz))) for row in XYZ_TO_SRGB]
    mx = max(rgb)
    return tuple(c / mx for c in rgb)


def kelvin_rgb(kelvin: float) -> tuple[float, float, float]:
    """Gamma-encoded sRGB in [0, 1], brightest channel = 1."""
    def enc(c):
        return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return tuple(enc(c) for c in kelvin_linear_rgb(kelvin))


def wb_gains(from_k: float, to_k: float) -> tuple[float, float, float]:
    """Linear-light channel gains that re-light ``from_k`` footage as ``to_k`` (green kept at 1)."""
    a, b = kelvin_linear_rgb(from_k), kelvin_linear_rgb(to_k)
    g = [bb / aa for aa, bb in zip(a, b)]
    return tuple(x / g[1] for x in g)


def ffmpeg_colorchannelmixer(gains) -> str:
    r, g, b = gains
    return f"colorchannelmixer=rr={r:.4f}:gg={g:.4f}:bb={b:.4f}"
