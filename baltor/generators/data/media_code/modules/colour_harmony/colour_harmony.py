"""Colour harmony schemes from one base colour (HSL colour wheel).

Generates complementary, analogous, triadic, split-complementary, tetradic
and square schemes by rotating hue on the HSL wheel, keeping saturation and
lightness, plus monochrome sets that vary lightness. Every scheme returns
hex colours with the base first, ready for backgrounds, accents and lower
thirds. ``accent_for`` picks the scheme colour with the most contrast
against a background for small accents.

Usage::

    from colour_harmony import scheme, accent_for
    scheme("#FFD21F", "triadic")          # ['#FFD21F', '#1FFFD2', '#D21FFF']
    accent_for("#0E1116", scheme("#FFD21F", "split_complementary"))
"""

from __future__ import annotations

import colorsys

OFFSETS = {
    "complementary": (0, 180),
    "analogous": (0, -30, 30),
    "triadic": (0, 120, 240),
    "split_complementary": (0, 150, 210),
    "tetradic": (0, 60, 180, 240),
    "square": (0, 90, 180, 270),
}


def _hex_to_hls(h: str):
    s = h.lstrip("#")
    if len(s) != 6:
        raise ValueError(f"bad hex colour {h!r}")
    r, g, b = (int(s[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return colorsys.rgb_to_hls(r, g, b)


def _hls_to_hex(h, l, s) -> str:
    r, g, b = colorsys.hls_to_rgb(h % 1.0, min(1, max(0, l)), min(1, max(0, s)))
    return "#" + "".join(f"{int(round(c * 255)):02X}" for c in (r, g, b))


def scheme(base: str, kind: str) -> list[str]:
    if kind == "monochrome":
        h, l, s = _hex_to_hls(base)
        return [_hls_to_hex(h, l, s)] + [_hls_to_hex(h, v, s) for v in (0.2, 0.35, 0.65, 0.85) if abs(v - l) > 0.05]
    if kind not in OFFSETS:
        raise ValueError(f"unknown scheme {kind!r}; known: {', '.join(list(OFFSETS) + ['monochrome'])}")
    h, l, s = _hex_to_hls(base)
    return [_hls_to_hex(h + off / 360.0, l, s) for off in OFFSETS[kind]]


def _lum(hexcol: str) -> float:
    s = hexcol.lstrip("#")
    out = 0.0
    for i, w in zip((0, 2, 4), (0.2126, 0.7152, 0.0722)):
        c = int(s[i:i + 2], 16) / 255
        out += w * (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def contrast(a: str, b: str) -> float:
    la, lb = _lum(a), _lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def accent_for(background: str, candidates: list[str]) -> tuple[str, float]:
    best = max(candidates, key=lambda c: contrast(c, background))
    return best, round(contrast(best, background), 2)
