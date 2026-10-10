"""Animated number count-ups ("0 -> 1,000 dogs", "14 days", "86.5%").

``counter_frames`` returns the formatted string for every frame, easing from
``start`` to ``end`` and always landing exactly on ``end``. ``drawtext_text``
returns a drawtext ``text`` value that ffmpeg evaluates itself with
``%{eif:...}`` (integers only), with the colons escaped for a filtergraph.

Usage::

    from number_counter_animation import counter_frames, format_number, drawtext_text
    counter_frames(0, 1000, duration=1.2, fps=30, suffix=" dogs")
    format_number(86.5, decimals=1, suffix="%")
    drawtext_text(0, 1000, start=2.0, duration=1.0)
"""

from __future__ import annotations

import math


def _out_expo(x: float) -> float:
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def _out_cubic(x: float) -> float:
    return 1 - (1 - x) ** 3


EASINGS = {"linear": lambda x: x, "out_cubic": _out_cubic, "out_expo": _out_expo}


def format_number(value: float, decimals: int = 0, thousands: str = ",", prefix: str = "",
                  suffix: str = "", decimal_point: str = ".") -> str:
    neg = value < 0
    text = f"{abs(value):,.{decimals}f}"
    text = text.replace(",", "\x00").replace(".", decimal_point).replace("\x00", thousands)
    return f"{'-' if neg else ''}{prefix}{text}{suffix}"


def value_at(start: float, end: float, t: float, duration: float, easing: str = "out_cubic") -> float:
    if duration <= 0:
        return end
    p = min(1.0, max(0.0, t / duration))
    return start + (end - start) * EASINGS[easing](p)


def counter_frames(start: float, end: float, duration: float, fps: float = 30, decimals: int = 0,
                   easing: str = "out_cubic", hold: float = 0.0, **fmt) -> list[str]:
    if easing not in EASINGS:
        raise ValueError(f"easing must be one of {sorted(EASINGS)}")
    n = int(math.ceil((duration + hold) * fps)) + 1
    out = []
    for i in range(n):
        v = value_at(start, end, i / fps, duration, easing)
        if i / fps >= duration:
            v = end
        # truncate toward the start so the display never passes the end early
        q = 10 ** decimals
        v = math.floor(v * q) / q if end >= start else math.ceil(v * q) / q
        out.append(format_number(v, decimals, **fmt))
    return out


def drawtext_text(start: int, end: int, at: float = 0.0, duration: float = 1.0, start_time: float | None = None) -> str:
    """drawtext ``text=`` value counting integers with an out-cubic ease (filtergraph-escaped)."""
    t0 = at if start_time is None else start_time
    p = f"min(1,max(0,(t-{t0:g})/{duration:g}))"
    expr = f"{start}+({end - start})*(1-pow(1-{p},3))"
    return "%{eif\\:trunc(" + expr.replace(",", "\\,") + ")\\:d}"
