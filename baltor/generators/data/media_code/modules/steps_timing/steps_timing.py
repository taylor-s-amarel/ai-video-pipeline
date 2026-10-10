"""Stepped timing: CSS steps() and stop-motion "on twos" holds.

``steps_value`` follows the CSS Easing Functions Level 1 step algorithm with
the jump-start, jump-end, jump-none and jump-both positions (start/end are
aliases). ``hold_frames`` gives the source frame shown at each output frame
when animating on twos, threes, etc., which is how a choppy hand-made look is
produced from smooth motion.

Usage::

    from steps_timing import steps_value, hold_frames
    steps_value(0.5, 4, "jump-end")   # 0.5
    hold_frames(8, hold=2)            # [0, 0, 2, 2, 4, 4, 6, 6]
"""

from __future__ import annotations

import math

POSITIONS = {"jump-start", "jump-end", "jump-none", "jump-both", "start", "end"}


def steps_value(t: float, steps: int, position: str = "jump-end") -> float:
    if steps < 1:
        raise ValueError("steps must be >= 1")
    if position not in POSITIONS:
        raise ValueError(f"position must be one of {sorted(POSITIONS)}")
    position = {"start": "jump-start", "end": "jump-end"}.get(position, position)
    if position == "jump-none" and steps < 2:
        raise ValueError("jump-none needs at least 2 steps")
    current = math.floor(t * steps)
    if position in ("jump-start", "jump-both"):
        current += 1
    if t >= 0 and current < 0:
        current = 0
    jumps = {"jump-start": steps, "jump-end": steps, "jump-both": steps + 1, "jump-none": steps - 1}[position]
    if t <= 1 and current > jumps:
        current = jumps
    return current / jumps


def hold_frames(n_frames: int, hold: int = 2, offset: int = 0) -> list[int]:
    """Source frame index for each output frame when holding every pose for ``hold`` frames."""
    if hold < 1:
        raise ValueError("hold must be >= 1")
    out = []
    for i in range(n_frames):
        src = ((i + offset) // hold) * hold - offset
        out.append(max(0, src))
    return out


def stepped_times(duration: float, fps: float, hold: int = 2) -> list[float]:
    """Timestamps (s) to evaluate an animation at, one per output frame, quantised to holds."""
    n = int(round(duration * fps))
    return [f / fps for f in hold_frames(n, hold)]


def ffmpeg_hold_filter(hold: int, fps: float) -> str:
    """ffmpeg filter that gives an 'on N' look to smooth footage: drop to fps/N then duplicate back."""
    if hold < 1:
        raise ValueError("hold must be >= 1")
    return f"fps={fps / hold:g},fps={fps:g}"
