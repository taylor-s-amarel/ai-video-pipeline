"""Keyframe tracks with per-segment easing, for any scalar or vector property.

A track is a list of keyframes ``(time, value, easing)``. The easing on a
keyframe shapes the segment that *leaves* it. Values may be numbers or
equal-length sequences (positions, colours). Supported easings: hold, linear,
in/out/in_out for quad, cubic and sine, and out_back.

Usage::

    from keyframe_track import Track
    tr = Track([(0, (540, 2100), "out_cubic"), (0.6, (540, 960), "hold"), (2.0, (540, 960))])
    tr.at(0.3)
    tr.frames(fps=30)
"""

from __future__ import annotations

import bisect
import math
from dataclasses import dataclass
from typing import Sequence, Union

Value = Union[float, Sequence[float]]

EASE = {
    "linear": lambda x: x,
    "in_quad": lambda x: x * x,
    "out_quad": lambda x: 1 - (1 - x) ** 2,
    "in_out_quad": lambda x: 2 * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 2 / 2,
    "in_cubic": lambda x: x ** 3,
    "out_cubic": lambda x: 1 - (1 - x) ** 3,
    "in_out_cubic": lambda x: 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2,
    "in_sine": lambda x: 1 - math.cos(x * math.pi / 2),
    "out_sine": lambda x: math.sin(x * math.pi / 2),
    "in_out_sine": lambda x: -(math.cos(math.pi * x) - 1) / 2,
    "out_back": lambda x: 1 + 2.70158 * (x - 1) ** 3 + 1.70158 * (x - 1) ** 2,
    "hold": lambda x: 0.0,
}


@dataclass(frozen=True)
class Keyframe:
    time: float
    value: Value
    easing: str = "linear"


def _lerp(a: Value, b: Value, u: float) -> Value:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a + (b - a) * u
    if len(a) != len(b):
        raise ValueError("vector keyframes must have the same length")
    return tuple(x + (y - x) * u for x, y in zip(a, b))


class Track:
    def __init__(self, keys: Sequence):
        kfs = [k if isinstance(k, Keyframe) else Keyframe(*k) for k in keys]
        if not kfs:
            raise ValueError("a track needs at least one keyframe")
        kfs.sort(key=lambda k: k.time)
        for k in kfs:
            if k.easing not in EASE:
                raise ValueError(f"unknown easing {k.easing!r}")
        times = [k.time for k in kfs]
        if len(set(times)) != len(times):
            raise ValueError("two keyframes share a time")
        self.keys = kfs
        self._times = times

    @property
    def duration(self) -> float:
        return self.keys[-1].time

    def at(self, t: float) -> Value:
        if t <= self.keys[0].time:
            return self.keys[0].value
        if t >= self.keys[-1].time:
            return self.keys[-1].value
        i = bisect.bisect_right(self._times, t) - 1
        a, b = self.keys[i], self.keys[i + 1]
        u = (t - a.time) / (b.time - a.time)
        return _lerp(a.value, b.value, EASE[a.easing](u))

    def frames(self, fps: float, start: float | None = None, end: float | None = None) -> list[Value]:
        start = self.keys[0].time if start is None else start
        end = self.duration if end is None else end
        n = int(round((end - start) * fps)) + 1
        return [self.at(start + i / fps) for i in range(n)]

    def to_json(self) -> list[dict]:
        return [{"time": k.time, "value": list(k.value) if not isinstance(k.value, (int, float)) else k.value,
                 "easing": k.easing} for k in self.keys]

    @classmethod
    def from_json(cls, data: list[dict]) -> "Track":
        return cls([Keyframe(d["time"], tuple(d["value"]) if isinstance(d["value"], list) else d["value"],
                             d.get("easing", "linear")) for d in data])
