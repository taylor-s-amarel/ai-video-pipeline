"""LRC lyric/caption files, including enhanced per-word timestamps.

Line form: ``[mm:ss.xx]text``; several time tags may share one line. Header
tags such as ``[ti:Title]``, ``[ar:Artist]`` and ``[offset:+250]`` (ms,
positive shifts lyrics earlier) are kept in ``meta``. Enhanced LRC puts
``<mm:ss.xx>`` before words. Useful for music videos and karaoke captions.

Usage::

    from lrc_lyrics_format import parse, dumps
    doc = parse(text)        # {'meta': {...}, 'lines': [(time_s, text, [(word_time, word), ...]), ...]}
    dumps(doc["lines"], meta={"ti": "With These Hands"})
"""

from __future__ import annotations

import re

_TIME_TAG = re.compile(r"\[(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?\]")
_META = re.compile(r"^\[([a-z]+):(.*)\]$", re.I)
_WORD = re.compile(r"<(\d{1,3}):(\d{2})(?:[.:](\d{1,3}))?>([^<]*)")


def _secs(m, s, frac) -> float:
    f = (frac or "0")
    return int(m) * 60 + int(s) + int(f) / (10 ** len(f))


def fmt(t: float) -> str:
    if t < 0:
        raise ValueError("negative time")
    cs = int(round(t * 100))
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{m:02d}:{s:02d}.{cs:02d}"


def parse(text: str, apply_offset: bool = True) -> dict:
    meta: dict[str, str] = {}
    lines = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        times = list(_TIME_TAG.finditer(line))
        if not times:
            m = _META.match(line)
            if m:
                meta[m[1].lower()] = m[2].strip()
            continue
        body = line[times[-1].end():]
        words = [(_secs(*w.groups()[:3]), w[4].strip()) for w in _WORD.finditer(body)]
        plain = _WORD.sub(lambda w: w[4], body).strip() if words else body.strip()
        for t in times:
            lines.append([_secs(*t.groups()), plain, [list(w) for w in words]])
    offset = 0.0
    if apply_offset and "offset" in meta:
        offset = int(meta["offset"]) / 1000.0
    out = []
    for t, plain, words in sorted(lines, key=lambda x: x[0]):
        out.append((max(0.0, t - offset), plain, [(max(0.0, wt - offset), w) for wt, w in words]))
    return {"meta": meta, "lines": out}


def dumps(lines, meta: dict | None = None) -> str:
    out = [f"[{k}:{v}]" for k, v in (meta or {}).items()]
    for item in lines:
        t, text = item[0], item[1]
        words = item[2] if len(item) > 2 else []
        if words:
            body = " ".join(f"<{fmt(wt)}>{w}" for wt, w in words)
        else:
            body = text
        out.append(f"[{fmt(t)}]{body}")
    return "\n".join(out) + "\n"


def line_at(doc: dict, t: float) -> str:
    current = ""
    for lt, text, _ in doc["lines"]:
        if lt <= t:
            current = text
        else:
            break
    return current
