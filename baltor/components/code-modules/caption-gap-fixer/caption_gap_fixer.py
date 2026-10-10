"""Clean up caption timing: overlaps, flicker gaps and frame snapping.

* overlaps: the earlier cue ends at the later cue's start minus ``min_gap``;
* flicker gaps: gaps shorter than ``close_below`` are closed by extending the
  earlier cue (a blank flash between two captions looks like a glitch);
* ``min_gap`` (default 2 frames at 30 fps) keeps consecutive cues distinct;
* times snap to the frame grid so burned-in captions change on frame
  boundaries.

Usage::

    from caption_gap_fixer import fix_timing
    fixed = fix_timing(cues, fps=30, min_gap_frames=2, close_below=0.3)
"""

from __future__ import annotations

import math


def snap(t: float, fps: float) -> float:
    return round(t * fps) / fps


def fix_timing(cues, fps: float = 30.0, min_gap_frames: int = 2, close_below: float = 0.3,
               min_duration_frames: int = 6) -> list[dict]:
    if fps <= 0:
        raise ValueError("fps must be > 0")
    out = sorted((dict(c) for c in cues), key=lambda c: c["start"])
    gap = min_gap_frames / fps
    for c in out:
        c["start"], c["end"] = snap(c["start"], fps), snap(c["end"], fps)
    for a, b in zip(out, out[1:]):
        space = b["start"] - a["end"]
        if space < gap or space < close_below:
            a["end"] = b["start"] - gap
    min_d = min_duration_frames / fps
    for i, c in enumerate(out):
        if c["end"] - c["start"] < min_d:
            limit = out[i + 1]["start"] - gap if i + 1 < len(out) else math.inf
            c["end"] = min(c["start"] + min_d, limit)
        c["start"], c["end"] = round(c["start"], 6), round(c["end"], 6)
    return out


def problems(cues, fps: float = 30.0, min_gap_frames: int = 2) -> list[str]:
    gap = min_gap_frames / fps - 1e-9
    out = []
    for i, (a, b) in enumerate(zip(cues, cues[1:]), 1):
        if b["start"] < a["end"]:
            out.append(f"cue {i} overlaps cue {i + 1}")
        elif b["start"] - a["end"] < gap:
            out.append(f"cue {i} and {i + 1} are closer than {min_gap_frames} frames")
    for i, c in enumerate(cues, 1):
        if c["end"] <= c["start"]:
            out.append(f"cue {i} has no duration")
    return out
