"""Reframe video or stills to another aspect ratio with ffmpeg.

Three strategies, each returning a filter (``-vf``) or graph
(``-filter_complex``) string:

* ``cover``: scale up until the frame is filled, then crop (focus point
  selectable, e.g. keep the upper third for faces);
* ``contain``: scale down to fit and pad with a colour;
* ``blur_pad``: the ``contain`` foreground over a blurred, darkened,
  cover-scaled copy of itself, which avoids flat bars (a common vertical
  video treatment for landscape footage).

All outputs use even dimensions and square pixels (``setsar=1``).

Usage::

    from aspect_reframe_filters import cover, contain, blur_pad
    vf = cover(1080, 1920, focus=(0.5, 0.35))
    graph, out = blur_pad(1080, 1920, sigma=30, darken=0.25)
"""

from __future__ import annotations

import re


def _even(n: int) -> int:
    if n <= 0:
        raise ValueError("size must be positive")
    return n - n % 2


def cover(w: int, h: int, focus=(0.5, 0.5)) -> str:
    w, h = _even(w), _even(h)
    fx, fy = focus
    if not (0 <= fx <= 1 and 0 <= fy <= 1):
        raise ValueError("focus must be within [0, 1]")
    return (f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h}:x='(iw-{w})*{fx:g}':y='(ih-{h})*{fy:g}',setsar=1")


def contain(w: int, h: int, color: str = "black") -> str:
    w, h = _even(w), _even(h)
    if not re.fullmatch(r"[A-Za-z]+|#?[0-9A-Fa-f]{6}(@[0-9.]+)?|0x[0-9A-Fa-f]{6}", color):
        raise ValueError(f"bad colour {color!r}")
    return (f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
            f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={color},setsar=1")


def blur_pad(w: int, h: int, sigma: float = 30.0, darken: float = 0.25, in_label: str = "[0:v]",
             out_label: str = "[reframed]") -> tuple[str, str]:
    w, h = _even(w), _even(h)
    if not 0 <= darken < 1:
        raise ValueError("darken must be within [0, 1)")
    bg = (f"[rf_bg]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
          f"gblur=sigma={sigma:g},eq=brightness={-darken:g}[rf_bgb]")
    fg = f"[rf_fg]scale={w}:{h}:force_original_aspect_ratio=decrease[rf_fgs]"
    graph = (f"{in_label}split=2[rf_bg][rf_fg];{bg};{fg};"
             f"[rf_bgb][rf_fgs]overlay=(W-w)/2:(H-h)/2,setsar=1{out_label}")
    return graph, out_label


def output_size(src_w: int, src_h: int, w: int, h: int, mode: str) -> tuple[int, int, float]:
    """(scaled_w, scaled_h, scale) of the source inside the target for 'cover' or 'contain'."""
    sx, sy = w / src_w, h / src_h
    s = max(sx, sy) if mode == "cover" else min(sx, sy)
    return round(src_w * s), round(src_h * s), s
