"""Escape values for ffmpeg filter options and filtergraphs (injection-safe).

A value inside a filtergraph passes through two parsers (see "Quoting and
escaping" in the ffmpeg-utils and ffmpeg-filters documentation):

1. the filter's option parser, where ``\\``, ``'`` and ``:`` are special;
2. the filtergraph parser, where ``\\``, ``'``, ``[``, ``]``, ``,`` and ``;``
   are special.

``filter_value`` applies both levels, so a file name or text containing
``,drawbox=...`` or ``;[out]`` stays a literal value instead of becoming a new
filter. Pass the resulting graph to ffmpeg as one argv element (never through
a shell string). ``option`` and ``chain`` assemble filters from escaped parts.

Usage::

    from ffmpeg_filter_escaping import filter_value, option, chain
    vf = chain(option("subtitles", filename="/tmp/My: subs, final.srt"), "format=yuv420p")
"""

from __future__ import annotations

import re

_LEVEL1 = re.compile(r"([\\':])")
_LEVEL2 = re.compile(r"([\\'\[\],;])")
_NAME = re.compile(r"^[a-z0-9_]+$")


def escape_option_value(value: str) -> str:
    """Level 1: the filter option parser."""
    return _LEVEL1.sub(r"\\\1", value)


def escape_graph(text: str) -> str:
    """Level 2: the filtergraph parser."""
    return _LEVEL2.sub(r"\\\1", text)


def filter_value(value) -> str:
    """Both levels; use for any user-controlled filter option value."""
    s = str(value)
    if "\x00" in s or "\n" in s or "\r" in s:
        raise ValueError("filter values may not contain NUL or newlines")
    return escape_graph(escape_option_value(s))


def option(filter_name: str, *positional, **named) -> str:
    """``name=v1:v2:key=value`` with every value escaped."""
    if not _NAME.match(filter_name):
        raise ValueError(f"bad filter name {filter_name!r}")
    parts = [filter_value(p) for p in positional]
    for k, v in named.items():
        if not _NAME.match(k):
            raise ValueError(f"bad option name {k!r}")
        parts.append(f"{k}={filter_value(v)}")
    return filter_name + ("=" + ":".join(parts) if parts else "")


def chain(*filters: str) -> str:
    return ",".join(f for f in filters if f)


def label(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(f"bad pad label {name!r}")
    return f"[{name}]"
