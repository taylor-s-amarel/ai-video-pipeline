"""YouTube SBV caption format reader and writer.

SBV blocks are ``H:MM:SS.mmm,H:MM:SS.mmm`` on one line, then text lines,
then a blank line. YouTube Studio exports this format for uploaded captions.

Usage::

    from sbv_format import parse, dumps
    cues = parse(open("captions.sbv", encoding="utf-8").read())   # [(start, end, text), ...]
    text = dumps([(0.0, 1.5, "Hello")])
"""

from __future__ import annotations

import re

_LINE = re.compile(r"^(\d+):(\d{2}):(\d{2})\.(\d{3}),(\d+):(\d{2}):(\d{2})\.(\d{3})\s*$")


def format_time(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("negative timestamp")
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h}:{m:02d}:{s:02d}.{ms:03d}"


def parse(text: str) -> list[tuple[float, float, str]]:
    lines = text.lstrip("﻿").replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    while i < len(lines):
        m = _LINE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        g = [int(x) for x in m.groups()]
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        i += 1
        body = []
        while i < len(lines) and lines[i].strip():
            body.append(lines[i])
            i += 1
        out.append((start, end, "\n".join(body)))
    return out


def dumps(cues) -> str:
    blocks = []
    for start, end, text in cues:
        if end <= start:
            raise ValueError(f"cue at {start} ends before it starts")
        blocks.append(f"{format_time(start)},{format_time(end)}\n{text.strip()}\n")
    return "\n".join(blocks)
