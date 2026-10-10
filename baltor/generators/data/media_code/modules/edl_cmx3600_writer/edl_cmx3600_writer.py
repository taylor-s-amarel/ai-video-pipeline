"""CMX3600 edit decision lists (EDL) for handing a cut to an editor.

Writes the classic EDL text format: a TITLE and FCM line, then numbered
events with reel name, track (V/A/AA/B), transition (C cut, D dissolve with
duration), source in/out and record in/out timecodes. Optional
``* FROM CLIP NAME:`` comments keep file names. Non-drop timecode is used
for integer frame rates and drop-frame (';') for 29.97/59.94. The reader
parses events back for round-trip checks.

Usage::

    from edl_cmx3600_writer import Event, write_edl, read_edl
    text = write_edl("SYLVIA EARLE", [Event("A001", 0.0, 4.0, clip="intro.mp4"),
                                      Event("A002", 2.0, 7.5, transition="D", dissolve_frames=15)], fps=30)
"""

from __future__ import annotations

import re
from dataclasses import dataclass


def _tc(frames: int, fps: int, drop: bool) -> str:
    if drop:
        d = 2 if fps == 30 else 4
        per_10 = fps * 600 - 9 * d
        per_min = fps * 60 - d
        tens, rem = divmod(frames, per_10)
        frames += 9 * d * tens + (d * ((rem - d) // per_min) if rem > d else 0)
    ff = frames % fps
    ss = frames // fps % 60
    mm = frames // (fps * 60) % 60
    hh = frames // (fps * 3600)
    return f"{hh:02d}:{mm:02d}:{ss:02d}{';' if drop else ':'}{ff:02d}"


@dataclass
class Event:
    reel: str
    src_in: float
    src_out: float
    track: str = "V"
    transition: str = "C"
    dissolve_frames: int = 0
    clip: str | None = None


def write_edl(title: str, events: list[Event], fps: float = 30, start_tc_frames: int = 0) -> str:
    nominal = int(round(fps))
    drop = abs(fps - nominal) > 0.01 and nominal in (30, 60)
    if "\n" in title:
        raise ValueError("title must be one line")
    lines = [f"TITLE: {title}", f"FCM: {'DROP FRAME' if drop else 'NON-DROP FRAME'}", ""]
    rec = start_tc_frames
    for n, e in enumerate(events, 1):
        if e.src_out <= e.src_in:
            raise ValueError(f"event {n}: out must be after in")
        if not re.fullmatch(r"[A-Za-z0-9_]{1,8}", e.reel):
            raise ValueError(f"event {n}: reel names are 1-8 letters, digits or _")
        if e.track not in ("V", "A", "A2", "AA", "B", "AA/V"):
            raise ValueError(f"event {n}: unknown track {e.track!r}")
        if e.transition not in ("C", "D"):
            raise ValueError(f"event {n}: transition must be C or D")
        sin, sout = int(round(e.src_in * fps)), int(round(e.src_out * fps))
        length = sout - sin
        trans = "C   " if e.transition == "C" else f"D    {e.dissolve_frames:03d}"
        lines.append(f"{n:03d}  {e.reel:<8} {e.track:<5} {trans} {_tc(sin, nominal, drop)} {_tc(sout, nominal, drop)} "
                     f"{_tc(rec, nominal, drop)} {_tc(rec + length, nominal, drop)}")
        if e.clip:
            lines.append(f"* FROM CLIP NAME: {e.clip}")
        rec += length
    return "\n".join(lines) + "\n"


_EVENT = re.compile(r"^(\d{3,6})\s+(\S+)\s+(\S+)\s+(C|D)\s*(\d{3})?\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")


def read_edl(text: str) -> list[dict]:
    out = []
    for line in text.splitlines():
        m = _EVENT.match(line.strip())
        if m:
            out.append({"num": int(m[1]), "reel": m[2], "track": m[3], "transition": m[4],
                        "dissolve_frames": int(m[5]) if m[5] else 0, "src_in": m[6], "src_out": m[7],
                        "rec_in": m[8], "rec_out": m[9]})
        elif line.startswith("* FROM CLIP NAME:") and out:
            out[-1]["clip"] = line.split(":", 1)[1].strip()
    return out
