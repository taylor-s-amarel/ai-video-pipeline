"""Write ffmpeg concat-demuxer lists safely and join clips without re-encoding.

The concat demuxer reads a text file of ``file '<path>'`` lines. Paths with
quotes or unusual characters must be escaped: a single quote inside a quoted
path is written as ``'\\''``. Optional ``inpoint``/``outpoint``/``duration``
directives trim clips. Paths that are not "safe" for the demuxer (absolute,
or with characters outside letters, digits, '.', '_' and '-') need
``-safe 0``; ``argv`` adds it only when required.

Stream-copy concatenation only works when every clip has the same codecs,
resolution, frame rate and timebase; ``compatible`` checks summaries from
ffprobe first.

Usage::

    from concat_demuxer_list import list_text, argv
    open("list.txt", "w").write(list_text(["a.mp4", "it's b.mp4"]))
    cmd = argv("list.txt", "joined.mp4", paths=["a.mp4", "it's b.mp4"])
"""

from __future__ import annotations

import re
from pathlib import PurePosixPath


def quote(path: str) -> str:
    if "\n" in path or "\r" in path or "\x00" in path:
        raise ValueError("paths may not contain newlines or NUL")
    return "'" + path.replace("'", "'\\''") + "'"


def list_text(items) -> str:
    lines = ["ffconcat version 1.0"]
    for it in items:
        if isinstance(it, str):
            it = {"path": it}
        lines.append(f"file {quote(it['path'])}")
        for k in ("inpoint", "outpoint", "duration"):
            if k in it and it[k] is not None:
                if float(it[k]) < 0:
                    raise ValueError(f"{k} must be >= 0")
                lines.append(f"{k} {float(it[k]):.6f}")
    return "\n".join(lines) + "\n"


_PORTABLE = re.compile(r"^[A-Za-z0-9_.-]+$")


def needs_unsafe(paths) -> bool:
    """True unless every path is 'safe' for the concat demuxer: relative, no protocol, and every
    component made of letters, digits, '.', '_' or '-' and not starting with '.'."""
    for p in paths:
        pp = PurePosixPath(p)
        if pp.is_absolute() or ":" in p or "\\" in p:
            return True
        for part in pp.parts:
            if part.startswith(".") or not _PORTABLE.match(part):
                return True
    return False


def argv(list_file: str, out: str, paths=(), copy: bool = True) -> list[str]:
    a = ["ffmpeg", "-nostdin", "-y", "-f", "concat"]
    if needs_unsafe(paths):
        a += ["-safe", "0"]
    a += ["-i", list_file]
    a += ["-c", "copy"] if copy else ["-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac"]
    return a + [out]


def compatible(summaries: list[dict], keys=("codec", "width", "height", "pix_fmt", "fps")) -> list[str]:
    """Problems that would break stream-copy concat, from per-clip video summaries."""
    if not summaries:
        return []
    ref = summaries[0]
    probs = []
    for i, s in enumerate(summaries[1:], 2):
        for k in keys:
            if s.get(k) != ref.get(k):
                probs.append(f"clip {i}: {k} {s.get(k)!r} differs from clip 1 {ref.get(k)!r}")
    return probs
