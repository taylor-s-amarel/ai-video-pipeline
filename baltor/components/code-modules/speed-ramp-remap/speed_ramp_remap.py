"""Speed ramps: map output time to source time from speed keyframes.

Speed keyframes ``[(out_time, speed), ...]`` are linearly interpolated;
source time is the integral of speed over output time. The module returns
source times per output frame (to pick or blend frames), the total output
duration for a source clip, and an ffmpeg ``setpts`` expression for a single
constant-speed section.

Usage::

    from speed_ramp_remap import SpeedRamp
    ramp = SpeedRamp([(0, 1.0), (1.0, 0.25), (2.0, 0.25), (2.5, 1.0)])
    ramp.source_time(1.5)
    ramp.frame_map(fps=30, out_duration=4)    # source frame index per output frame
    ramp.output_duration_for(source_len=3.0)
"""

from __future__ import annotations

import bisect


class SpeedRamp:
    def __init__(self, keys):
        keys = sorted((float(t), float(s)) for t, s in keys)
        if not keys or keys[0][0] != 0.0:
            raise ValueError("first speed keyframe must be at output time 0")
        if any(s <= 0 for _, s in keys):
            raise ValueError("speeds must be > 0 (use a freeze-frame for 0)")
        self.keys = keys
        self._t = [k[0] for k in keys]
        # cumulative source time at each key (trapezoid integral of linear speed)
        self._src = [0.0]
        for (t0, s0), (t1, s1) in zip(keys, keys[1:]):
            self._src.append(self._src[-1] + (t1 - t0) * (s0 + s1) / 2)

    def speed(self, t: float) -> float:
        if t >= self._t[-1]:
            return self.keys[-1][1]
        i = bisect.bisect_right(self._t, t) - 1
        (t0, s0), (t1, s1) = self.keys[i], self.keys[i + 1]
        return s0 + (s1 - s0) * (t - t0) / (t1 - t0)

    def source_time(self, t: float) -> float:
        if t <= 0:
            return 0.0
        if t >= self._t[-1]:
            return self._src[-1] + (t - self._t[-1]) * self.keys[-1][1]
        i = bisect.bisect_right(self._t, t) - 1
        t0, s0 = self.keys[i]
        dt = t - t0
        return self._src[i] + dt * (s0 + self.speed(t)) / 2

    def output_duration_for(self, source_len: float, tol: float = 1e-6) -> float:
        lo, hi = 0.0, 1.0
        while self.source_time(hi) < source_len:
            hi *= 2
        while hi - lo > tol:
            mid = (lo + hi) / 2
            if self.source_time(mid) < source_len:
                lo = mid
            else:
                hi = mid
        return hi

    def frame_map(self, fps: float, out_duration: float, source_fps: float | None = None) -> list[int]:
        sfps = source_fps or fps
        n = int(round(out_duration * fps))
        return [int(self.source_time(i / fps) * sfps + 1e-9) for i in range(n)]


def setpts_for_speed(speed: float) -> str:
    """``setpts`` filter for a constant speed (2.0 = twice as fast); pair with atempo for audio."""
    if speed <= 0:
        raise ValueError("speed must be > 0")
    return f"setpts=PTS/{speed:g}"
