"""Run and parse ffmpeg's detector filters: black, freeze, silence, crop.

Each ``*_argv`` builds an analysis command (``-f null -``) and each parser
turns ffmpeg's log lines into events:

* ``blackdetect``: ``black_start:… black_end:… black_duration:…``
* ``freezedetect``: ``lavfi.freezedetect.freeze_start/end/duration`` lines
* ``silencedetect``: ``silence_start:`` / ``silence_end: … | silence_duration:``
* ``cropdetect``: the most frequent ``crop=w:h:x:y`` suggestion

``analyse(path)`` runs black, freeze and silence detection in one pass and
returns all events (useful QA: no black gaps, no frozen video, no dead air).

Usage::

    from ffmpeg_detect_log_parser import analyse
    report = analyse("render.mp4")   # {'black': [...], 'freeze': [...], 'silence': [...]}
"""

from __future__ import annotations

import re
import shutil
import subprocess
from collections import Counter

_BLACK = re.compile(r"black_start:\s*([\d.]+)\s+black_end:\s*([\d.]+)\s+black_duration:\s*([\d.]+)")
_FREEZE = re.compile(r"lavfi\.freezedetect\.freeze_(start|end|duration):\s*([\d.]+)")
_SIL_START = re.compile(r"silence_start:\s*(-?[\d.]+)")
_SIL_END = re.compile(r"silence_end:\s*([\d.]+)\s*\|\s*silence_duration:\s*([\d.]+)")
_CROP = re.compile(r"crop=(\d+):(\d+):(\d+):(\d+)")


def parse_black(log: str) -> list[dict]:
    return [{"start": float(a), "end": float(b), "duration": float(c)} for a, b, c in _BLACK.findall(log)]


def parse_freeze(log: str) -> list[dict]:
    events, cur = [], {}
    for key, val in _FREEZE.findall(log):
        cur[key] = float(val)
        if key == "end":
            events.append({"start": cur.get("start"), "end": cur["end"], "duration": cur.get("duration")})
            cur = {}
    if "start" in cur:
        events.append({"start": cur["start"], "end": None, "duration": None})  # frozen until the end
    return events


def parse_silence(log: str) -> list[dict]:
    events, start = [], None
    for line in log.splitlines():
        m = _SIL_START.search(line)
        if m:
            start = max(0.0, float(m.group(1)))
            continue
        m = _SIL_END.search(line)
        if m:
            events.append({"start": start, "end": float(m.group(1)), "duration": float(m.group(2))})
            start = None
    if start is not None:
        events.append({"start": start, "end": None, "duration": None})
    return events


def parse_crop(log: str) -> tuple[int, int, int, int] | None:
    found = [tuple(map(int, m)) for m in _CROP.findall(log)]
    return Counter(found).most_common(1)[0][0] if found else None


def analyse_argv(path: str, black_min_s: float = 0.25, freeze_min_s: float = 2.0, noise_db: float = -50.0,
                 silence_min_s: float = 1.5, audio: bool = True) -> list[str]:
    a = ["ffmpeg", "-nostdin", "-hide_banner", "-i", path,
         "-vf", f"blackdetect=d={black_min_s:g}:pix_th=0.10,freezedetect=n=-60dB:d={freeze_min_s:g},metadata=mode=print"]
    if audio:
        a += ["-af", f"silencedetect=n={noise_db:g}dB:d={silence_min_s:g}"]
    else:
        a += ["-an"]
    return a + ["-f", "null", "-"]


def cropdetect_argv(path: str, seconds: float = 10.0) -> list[str]:
    return ["ffmpeg", "-nostdin", "-hide_banner", "-t", f"{seconds:g}", "-i", path, "-vf", "cropdetect=24:2:0",
            "-f", "null", "-"]


def analyse(path: str, audio: bool = True, **kw) -> dict:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is not installed")
    log = subprocess.run(analyse_argv(path, audio=audio, **kw), capture_output=True, text=True, timeout=600).stderr
    return {"black": parse_black(log), "freeze": parse_freeze(log), "silence": parse_silence(log) if audio else []}
