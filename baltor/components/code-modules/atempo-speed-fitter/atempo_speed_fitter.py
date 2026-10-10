"""Fit narration to a target length with ffmpeg ``atempo`` (pitch preserved).

``fit_factor`` computes the tempo factor and refuses changes beyond
``max_change`` (default 12%), because larger stretches audibly degrade speech;
re-synthesize at a different speed instead. ``atempo_chain`` splits any
factor into stages inside [0.5, 2.0], which every ffmpeg version accepts.

Usage::

    from atempo_speed_fitter import fit_factor, atempo_chain, command
    f = fit_factor(current_s=66.2, target_s=62.0)          # 1.0677...
    af = atempo_chain(f)                                    # 'atempo=1.067742'
    argv = command("narration.wav", "fitted.wav", f)
"""

from __future__ import annotations

import math


def fit_factor(current_s: float, target_s: float, max_change: float = 0.12) -> float:
    if current_s <= 0 or target_s <= 0:
        raise ValueError("durations must be > 0")
    f = current_s / target_s
    if abs(f - 1.0) > max_change:
        raise ValueError(f"tempo change {f:.3f}x exceeds +/-{max_change:.0%}; re-synthesize at a different speed")
    return f


def atempo_chain(factor: float) -> str:
    if factor <= 0:
        raise ValueError("factor must be > 0")
    stages = []
    f = factor
    while f > 2.0:
        stages.append(2.0)
        f /= 2.0
    while f < 0.5:
        stages.append(0.5)
        f /= 0.5
    stages.append(f)
    if math.isclose(stages[-1], 1.0, abs_tol=1e-9) and len(stages) > 1:
        stages.pop()
    return ",".join(f"atempo={s:.6f}".rstrip("0").rstrip(".") for s in stages)


def command(src: str, dst: str, factor: float) -> list[str]:
    return ["ffmpeg", "-nostdin", "-y", "-i", src, "-filter:a", atempo_chain(factor), dst]
