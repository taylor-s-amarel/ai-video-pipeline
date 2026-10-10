"""Validated ffmpeg colour filters: eq, colorbalance, hue and curves presets.

Range-checks every value before it reaches ffmpeg (a wrong sign or scale is
the usual reason a grade looks broken) and composes a single filter chain.

* ``eq``: brightness [-1, 1], contrast [-1000, 1000] (1 = unchanged),
  saturation [0, 3], gamma [0.1, 10]
* ``colorbalance``: shadows/midtones/highlights per channel in [-1, 1]
* ``hue``: hue shift in degrees and saturation [-10, 10]
* ``curves``: one of ffmpeg's built-in presets

Usage::

    from eq_colour_filter_builder import grade
    vf = grade(eq={"contrast": 1.08, "saturation": 1.15}, balance={"rs": 0.04, "bs": -0.03},
               curves="medium_contrast")
"""

from __future__ import annotations

EQ_RANGES = {"brightness": (-1.0, 1.0), "contrast": (-1000.0, 1000.0), "saturation": (0.0, 3.0),
             "gamma": (0.1, 10.0), "gamma_r": (0.1, 10.0), "gamma_g": (0.1, 10.0), "gamma_b": (0.1, 10.0)}
BALANCE_KEYS = {f"{c}{z}" for c in "rgb" for z in "smh"}
CURVE_PRESETS = {"none", "color_negative", "cross_process", "darker", "increase_contrast", "lighter",
                 "linear_contrast", "medium_contrast", "negative", "strong_contrast", "vintage"}


def eq(**values) -> str:
    parts = []
    for k, v in values.items():
        if k not in EQ_RANGES:
            raise ValueError(f"unknown eq option {k!r}")
        lo, hi = EQ_RANGES[k]
        if not lo <= v <= hi:
            raise ValueError(f"eq {k}={v} outside [{lo}, {hi}]")
        parts.append(f"{k}={v:g}")
    return "eq=" + ":".join(parts) if parts else ""


def colorbalance(preserve_lightness: bool = False, **values) -> str:
    parts = []
    for k, v in values.items():
        if k not in BALANCE_KEYS:
            raise ValueError(f"unknown colorbalance option {k!r} (use rs, gm, bh, ...)")
        if not -1 <= v <= 1:
            raise ValueError(f"colorbalance {k}={v} outside [-1, 1]")
        parts.append(f"{k}={v:g}")
    if preserve_lightness:
        parts.append("pl=1")
    return "colorbalance=" + ":".join(parts) if parts else ""


def hue(degrees: float = 0.0, saturation: float = 1.0) -> str:
    if not -10 <= saturation <= 10:
        raise ValueError("hue saturation must be within [-10, 10]")
    return f"hue=h={degrees:g}:s={saturation:g}"


def curves(preset: str) -> str:
    if preset not in CURVE_PRESETS:
        raise ValueError(f"unknown curves preset {preset!r}")
    return f"curves=preset={preset}"


def grade(eq: dict | None = None, balance: dict | None = None, hue_shift: float | None = None,
          curves: str | None = None) -> str:
    chain = []
    if curves:
        chain.append(globals()["curves"](curves))
    if balance:
        chain.append(colorbalance(**balance))
    if eq:
        chain.append(globals()["eq"](**eq))
    if hue_shift is not None:
        chain.append(hue(hue_shift))
    return ",".join(c for c in chain if c) or "null"
