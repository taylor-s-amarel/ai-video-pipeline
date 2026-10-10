"""SubRip (.srt) reader and writer.

The parser is tolerant of what real files contain: a UTF-8 BOM, CRLF line
endings, '.' instead of ',' before milliseconds, missing or wrong index lines,
extra blank lines and a missing final newline. The writer always produces
the strict form: index from 1, ``HH:MM:SS,mmm --> HH:MM:SS,mmm``, text, blank
line.

Usage::

    from srt_format import Cue, parse, dumps, validate
    cues = parse(open("in.srt", encoding="utf-8-sig").read())
    text = dumps([Cue(1.0, 2.5, "Hello")])
    problems = validate(cues)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_TIME = r"(\d{1,3}):(\d{2}):(\d{2})[,.](\d{1,3})"
_LINE = re.compile(rf"^\s*{_TIME}\s*-->\s*{_TIME}")


@dataclass
class Cue:
    start: float
    end: float
    text: str


def format_time(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("negative timestamp")
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _to_seconds(h, m, s, frac) -> float:
    return int(h) * 3600 + int(m) * 60 + int(s) + int(frac.ljust(3, "0")[:3]) / 1000


def parse(text: str) -> list[Cue]:
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    cues: list[Cue] = []
    i = 0
    while i < len(lines):
        m = _LINE.match(lines[i])
        if not m:
            i += 1
            continue
        start = _to_seconds(*m.groups()[:4])
        end = _to_seconds(*m.groups()[4:])
        i += 1
        body = []
        while i < len(lines) and lines[i].strip() != "":
            # a following cue without a blank line: index line then timing line
            if _LINE.match(lines[i]) or (lines[i].strip().isdigit() and i + 1 < len(lines) and _LINE.match(lines[i + 1])):
                break
            body.append(lines[i])
            i += 1
        cues.append(Cue(start, end, "\n".join(body).strip()))
    return cues


def dumps(cues: list[Cue]) -> str:
    blocks = []
    for n, c in enumerate(cues, 1):
        blocks.append(f"{n}\n{format_time(c.start)} --> {format_time(c.end)}\n{c.text.strip()}\n")
    return "\n".join(blocks)


def validate(cues: list[Cue], min_duration: float = 0.3) -> list[str]:
    problems = []
    for n, c in enumerate(cues, 1):
        if c.end <= c.start:
            problems.append(f"cue {n}: end {c.end:.3f} is not after start {c.start:.3f}")
        elif c.end - c.start < min_duration:
            problems.append(f"cue {n}: only {c.end - c.start:.3f}s on screen")
        if not c.text.strip():
            problems.append(f"cue {n}: empty text")
    for n, (a, b) in enumerate(zip(cues, cues[1:]), 1):
        if b.start < a.end - 1e-9:
            problems.append(f"cues {n} and {n + 1} overlap by {a.end - b.start:.3f}s")
    return problems
