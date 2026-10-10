"""Validated builders for ASS override tags.

Each function returns one tag string (without braces); ``block`` joins tags
into an override block. Values are range-checked so a typo cannot silently
produce a broken line: alignment 1-9, alpha 0-255, colours as #RRGGBB.

Usage::

    from ass_override_tags import block, pos, fad, color, alpha, blur, move, transform, fs
    block(pos(540, 1500), fad(80, 120), color("#FFD21F"), blur(1.5))
    # '{\\pos(540,1500)\\fad(80,120)\\1c&H1FD2FF&\\blur1.5}'
"""

from __future__ import annotations

import re


def _num(v: float) -> str:
    return f"{v:g}"


def _hex(h: str) -> str:
    s = h.lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", s):
        raise ValueError(f"colour must be #RRGGBB, got {h!r}")
    return f"&H{s[4:6]}{s[2:4]}{s[0:2]}&".upper()


def color(hex_rgb: str, which: int = 1) -> str:
    """which: 1 primary (fill), 2 secondary (karaoke), 3 outline, 4 shadow."""
    if which not in (1, 2, 3, 4):
        raise ValueError("which must be 1-4")
    return f"\\{which}c{_hex(hex_rgb)}"


def alpha(opacity: float, which: int | None = None) -> str:
    """opacity 1.0 = opaque. ASS alpha is inverted (00 opaque, FF transparent)."""
    if not 0 <= opacity <= 1:
        raise ValueError("opacity must be within [0, 1]")
    a = round((1 - opacity) * 255)
    if which is None:
        return f"\\alpha&H{a:02X}&"
    if which not in (1, 2, 3, 4):
        raise ValueError("which must be 1-4")
    return f"\\{which}a&H{a:02X}&"


def pos(x: float, y: float) -> str:
    return f"\\pos({_num(x)},{_num(y)})"


def move(x1, y1, x2, y2, t1: int | None = None, t2: int | None = None) -> str:
    if (t1 is None) != (t2 is None):
        raise ValueError("give both t1 and t2 or neither")
    times = f",{t1},{t2}" if t1 is not None else ""
    return f"\\move({_num(x1)},{_num(y1)},{_num(x2)},{_num(y2)}{times})"


def fad(fade_in_ms: int, fade_out_ms: int) -> str:
    if fade_in_ms < 0 or fade_out_ms < 0:
        raise ValueError("fade times must be >= 0")
    return f"\\fad({fade_in_ms},{fade_out_ms})"


def an(alignment: int) -> str:
    if alignment not in range(1, 10):
        raise ValueError("alignment must be 1-9")
    return f"\\an{alignment}"


def fs(size: float) -> str:
    if size <= 0:
        raise ValueError("font size must be > 0")
    return f"\\fs{_num(size)}"


def scale(x_percent: float, y_percent: float | None = None) -> str:
    return f"\\fscx{_num(x_percent)}\\fscy{_num(x_percent if y_percent is None else y_percent)}"


def rotate(deg: float, axis: str = "z") -> str:
    if axis not in ("x", "y", "z"):
        raise ValueError("axis must be x, y or z")
    return f"\\fr{axis}{_num(deg)}"


def blur(strength: float) -> str:
    if strength < 0:
        raise ValueError("blur must be >= 0")
    return f"\\blur{_num(strength)}"


def border(width: float) -> str:
    return f"\\bord{_num(max(0.0, width))}"


def shadow(depth: float) -> str:
    return f"\\shad{_num(max(0.0, depth))}"


def bold(on: bool = True) -> str:
    return f"\\b{1 if on else 0}"


def clip_rect(x1, y1, x2, y2, inverse: bool = False) -> str:
    return f"\\{'i' if inverse else ''}clip({_num(x1)},{_num(y1)},{_num(x2)},{_num(y2)})"


def transform(*tags: str, t1: int | None = None, t2: int | None = None, accel: float | None = None) -> str:
    if not tags:
        raise ValueError("transform needs at least one tag")
    if (t1 is None) != (t2 is None):
        raise ValueError("give both t1 and t2 or neither")
    head = []
    if t1 is not None:
        head += [str(t1), str(t2)]
    if accel is not None:
        head.append(_num(accel))
    prefix = ",".join(head) + ("," if head else "")
    return f"\\t({prefix}{''.join(tags)})"


def reset(style: str = "") -> str:
    return f"\\r{style}"


def block(*tags: str) -> str:
    for t in tags:
        if not t.startswith("\\") or "{" in t or "}" in t:
            raise ValueError(f"not an override tag: {t!r}")
    return "{" + "".join(tags) + "}"
