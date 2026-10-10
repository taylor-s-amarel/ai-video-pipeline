"""WebVTT (.vtt) writer and reader.

Writes the ``WEBVTT`` header, optional cue identifiers and cue settings
(``line``, ``position``, ``size``, ``align``), escaping ``&``, ``<`` and
``>`` in text. Reads cues while skipping NOTE, STYLE and REGION blocks,
accepting both ``mm:ss.ttt`` and ``hh:mm:ss.ttt`` timestamps, and can strip
inline tags (``<b>``, ``<c.yellow>``, ``<00:00:01.000>``).

Usage::

    from webvtt_format import Cue, dumps, parse
    vtt = dumps([Cue(1.0, 2.0, "Fish & chips", settings={"line": "80%", "align": "center"})])
    cues = parse(vtt)
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field

_TS = r"(?:(\d{1,}):)?(\d{2}):(\d{2})\.(\d{3})"
_TIMING = re.compile(rf"^{_TS}\s+-->\s+{_TS}(.*)$")
_TAG = re.compile(r"<[^>]*>")
ALLOWED_SETTINGS = {"vertical", "line", "position", "size", "align", "region"}


@dataclass
class Cue:
    start: float
    end: float
    text: str
    identifier: str | None = None
    settings: dict = field(default_factory=dict)


def format_time(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("negative timestamp")
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def dumps(cues: list[Cue], header_note: str | None = None) -> str:
    out = ["WEBVTT", ""]
    if header_note:
        if "-->" in header_note:
            raise ValueError("a NOTE may not contain '-->'")
        out += [f"NOTE {header_note}", ""]
    for c in cues:
        if c.identifier:
            if "-->" in c.identifier or "\n" in c.identifier:
                raise ValueError("cue identifier may not contain '-->' or newlines")
            out.append(c.identifier)
        bad = set(c.settings) - ALLOWED_SETTINGS
        if bad:
            raise ValueError(f"unknown cue settings {sorted(bad)}")
        settings = "".join(f" {k}:{v}" for k, v in c.settings.items())
        out.append(f"{format_time(c.start)} --> {format_time(c.end)}{settings}")
        body = escape(c.text.strip())
        if not body or "\n\n" in body:
            raise ValueError("cue text must be non-empty and contain no blank lines")
        out += [body, ""]
    return "\n".join(out)


def _secs(h, m, s, ms) -> float:
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def parse(text: str, strip_tags: bool = True) -> list[Cue]:
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("WEBVTT"):
        raise ValueError("missing WEBVTT header")
    blocks = re.split(r"\n{2,}", text.strip("\n"))
    cues = []
    for block in blocks[1:]:
        lines = block.split("\n")
        if lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue
        ident = None
        if not _TIMING.match(lines[0]):
            ident, lines = lines[0], lines[1:]
        if not lines:
            continue
        m = _TIMING.match(lines[0])
        if not m:
            continue
        g = m.groups()
        settings = dict(s.split(":", 1) for s in g[8].split() if ":" in s)
        body = "\n".join(lines[1:])
        if strip_tags:
            body = _TAG.sub("", body)
        cues.append(Cue(_secs(*g[0:4]), _secs(*g[4:8]), html.unescape(body), ident, settings))
    return cues
