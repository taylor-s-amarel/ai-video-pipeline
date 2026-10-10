"""Frame image sequences: patterns, gap detection and ffmpeg input arguments.

Rendered frames usually live as ``frame_%05d.png``. This module:

* parses names into (prefix, number, padding, extension) and groups a folder
  listing into sequences;
* finds missing frame numbers (a crashed render leaves gaps that ffmpeg
  would silently skip or stop at) and duplicate paddings;
* builds the ffmpeg input arguments (``-framerate``, ``-start_number``,
  ``-i pattern``) for a sequence.

Usage::

    from image_sequence_tools import group, gaps, ffmpeg_input
    seqs = group(os.listdir("frames"))
    gaps(seqs["frame_%05d.png"])           # [(start, end)] missing ranges
    ffmpeg_input("frames/frame_%05d.png", seqs["frame_%05d.png"], fps=30)
"""

from __future__ import annotations

import re

_NAME = re.compile(r"^(.*?)(\d+)(\.[A-Za-z0-9]+)$")


def parse(name: str):
    m = _NAME.match(name)
    if not m:
        return None
    prefix, digits, ext = m.groups()
    return prefix, int(digits), len(digits), ext


def pattern(prefix: str, padding: int, ext: str) -> str:
    return f"{prefix.replace('%', '%%')}%0{padding}d{ext}"


def group(names) -> dict[str, list[int]]:
    seqs: dict[str, list[int]] = {}
    for n in names:
        p = parse(n)
        if not p:
            continue
        prefix, num, pad, ext = p
        seqs.setdefault(pattern(prefix, pad, ext), []).append(num)
    return {k: sorted(v) for k, v in seqs.items()}


def gaps(numbers: list[int]) -> list[tuple[int, int]]:
    out = []
    nums = sorted(set(numbers))
    for a, b in zip(nums, nums[1:]):
        if b - a > 1:
            out.append((a + 1, b - 1))
    return out


def ffmpeg_input(pattern_path: str, numbers: list[int], fps: float = 30) -> list[str]:
    if gaps(numbers):
        raise ValueError(f"sequence has missing frames: {gaps(numbers)[:5]}")
    return ["-framerate", f"{fps:g}", "-start_number", str(min(numbers)), "-i", pattern_path]


def frame_name(prefix: str, n: int, padding: int = 5, ext: str = ".png") -> str:
    if n < 0 or len(str(n)) > padding:
        raise ValueError("frame number does not fit the padding")
    return f"{prefix}{n:0{padding}d}{ext}"
