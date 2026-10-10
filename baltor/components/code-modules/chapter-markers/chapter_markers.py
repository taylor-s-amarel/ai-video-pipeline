"""Chapter markers: YouTube description timestamps and FFMETADATA chapters.

``youtube_chapters`` renders ``00:00 Title`` lines and checks the rules from
YouTube's chapters help page (first timestamp 00:00, at least three
timestamps in ascending order) plus a minimum chapter length (default 10 s,
the commonly reported minimum; adjust if YouTube changes it).
``ffmetadata`` writes an FFMETADATA1 file with ``[CHAPTER]`` blocks (1 ms
time base) that ffmpeg can mux into MP4/MKV with ``-i chapters.txt
-map_metadata 1``, escaping ``=``, ``;``, ``#``, ``\\`` and newlines.

Usage::

    from chapter_markers import youtube_chapters, ffmetadata
    text, problems = youtube_chapters([(0, "Hook"), (12, "FACT 1"), (31, "FACT 2")], duration=64)
    open("chapters.txt", "w").write(ffmetadata([(0, "Hook"), (12, "FACT 1")], duration=64, title="Sylvia Earle"))
"""

from __future__ import annotations

import re


def _stamp(t: float, with_hours: bool) -> str:
    t = int(t)
    h, rem = divmod(t, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if with_hours else f"{m:02d}:{s:02d}"


def youtube_chapters(chapters, duration: float, min_chapter_s: float = 10.0) -> tuple[str, list[str]]:
    chapters = list(chapters)
    problems = []
    if not chapters or chapters[0][0] != 0:
        problems.append("first chapter must start at 00:00")
    if len(chapters) < 3:
        problems.append("YouTube needs at least three chapters")
    for (a, _), (b, _) in zip(chapters, chapters[1:]):
        if b <= a:
            problems.append("chapter times must be ascending")
            break
    ends = [c[0] for c in chapters[1:]] + [duration]
    for (start, title), end in zip(chapters, ends):
        if end - start < min_chapter_s:
            problems.append(f"chapter '{title}' is {end - start:.1f}s (< {min_chapter_s:g}s)")
    hours = duration >= 3600
    text = "\n".join(f"{_stamp(t, hours)} {title.strip()}" for t, title in chapters)
    return text + "\n", problems


def _meta_escape(v: str) -> str:
    return re.sub(r"([=;#\\\n])", r"\\\1", v)


def ffmetadata(chapters, duration: float, title: str | None = None, **tags) -> str:
    lines = [";FFMETADATA1"]
    if title:
        lines.append(f"title={_meta_escape(title)}")
    for k, v in tags.items():
        lines.append(f"{k}={_meta_escape(str(v))}")
    ends = [c[0] for c in chapters[1:]] + [duration]
    for (start, name), end in zip(chapters, ends):
        if end <= start:
            raise ValueError("chapters must be ascending and inside the duration")
        lines += ["[CHAPTER]", "TIMEBASE=1/1000", f"START={int(round(start * 1000))}",
                  f"END={int(round(end * 1000))}", f"title={_meta_escape(name)}"]
    return "\n".join(lines) + "\n"


def mux_argv(video: str, metadata_file: str, out: str) -> list[str]:
    return ["ffmpeg", "-nostdin", "-y", "-i", video, "-i", metadata_file, "-map_metadata", "1",
            "-map_chapters", "1", "-c", "copy", out]
