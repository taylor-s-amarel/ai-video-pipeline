"""SMPTE timecode: frames <-> HH:MM:SS:FF, including 29.97/59.94 drop-frame.

Drop-frame timecode skips frame numbers 00 and 01 (04 and 05 at 59.94) at
the start of every minute except every tenth minute, so the label stays close
to wall-clock time. Separator ';' marks drop-frame.

Usage::

    from smpte_timecode import frames_to_tc, tc_to_frames, seconds_to_frames
    frames_to_tc(1800, 30000/1001, drop=True)   # '00:01:00;02'
    tc_to_frames('00:01:00;02', 30000/1001)      # 1800
"""

from __future__ import annotations

import re
from fractions import Fraction

_TC = re.compile(r"^(\d{1,2}):(\d{2}):(\d{2})([:;.,])(\d{2,3})$")


def nominal_fps(fps) -> int:
    return int(round(float(fps)))


def is_drop_rate(fps) -> bool:
    f = Fraction(fps).limit_denominator(1001)
    return f.denominator == 1001 and nominal_fps(fps) in (30, 60)


def frames_to_tc(frames: int, fps, drop: bool | None = None) -> str:
    if frames < 0:
        raise ValueError("frames must be >= 0")
    nom = nominal_fps(fps)
    drop = is_drop_rate(fps) if drop is None else drop
    if drop:
        if nom not in (30, 60):
            raise ValueError("drop-frame applies only to 29.97 and 59.94 fps")
        d = 2 if nom == 30 else 4
        per_10min = nom * 600 - d * 9
        per_min = nom * 60 - d
        tens, rem = divmod(frames, per_10min)
        frames += d * 9 * tens
        if rem > d:
            frames += d * ((rem - d) // per_min)
    ff = frames % nom
    ss = (frames // nom) % 60
    mm = (frames // (nom * 60)) % 60
    hh = frames // (nom * 3600)
    return f"{hh:02d}:{mm:02d}:{ss:02d}{';' if drop else ':'}{ff:02d}"


def tc_to_frames(tc: str, fps, drop: bool | None = None) -> int:
    m = _TC.match(tc.strip())
    if not m:
        raise ValueError(f"not a timecode: {tc!r}")
    hh, mm, ss, sep, ff = int(m[1]), int(m[2]), int(m[3]), m[4], int(m[5])
    nom = nominal_fps(fps)
    if mm > 59 or ss > 59 or ff >= nom:
        raise ValueError(f"field out of range in {tc!r}")
    drop = (sep in ";," and is_drop_rate(fps)) if drop is None else drop
    total_min = hh * 60 + mm
    frames = ((hh * 3600 + mm * 60 + ss) * nom) + ff
    if drop:
        d = 2 if nom == 30 else 4
        if ss == 0 and ff < d and mm % 10 != 0:
            raise ValueError(f"{tc} does not exist in drop-frame timecode")
        frames -= d * (total_min - total_min // 10)
    return frames


def seconds_to_frames(seconds: float, fps) -> int:
    return int(round(Fraction(str(seconds)) * Fraction(fps).limit_denominator(1001)))


def frames_to_seconds(frames: int, fps) -> float:
    return float(Fraction(frames) / Fraction(fps).limit_denominator(1001))
