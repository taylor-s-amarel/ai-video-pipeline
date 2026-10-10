"""Reading-speed checks and fixes for caption cues.

Measures characters per second (CPS, spaces included, line breaks excluded)
and words per minute per cue and flags cues that are too fast, too short or
too long. ``extend_to_readable`` lengthens fast cues into the free time
before the next cue, never overlapping it.

Thresholds are parameters; the defaults (20 CPS, 0.7 s minimum, 7 s maximum)
are house defaults for short-form video, not a broadcaster specification.

Usage::

    from caption_reading_speed import analyse, extend_to_readable
    report = analyse(cues)          # cues: [{'start','end','text'}]
    fixed = extend_to_readable(cues, max_cps=20, min_gap=0.083)
"""

from __future__ import annotations


def cps(text: str, duration: float) -> float:
    chars = len(text.replace("\n", " ").strip())
    return chars / duration if duration > 0 else float("inf")


def wpm(text: str, duration: float) -> float:
    return len(text.split()) / duration * 60 if duration > 0 else float("inf")


def analyse(cues, max_cps: float = 20.0, min_duration: float = 0.7, max_duration: float = 7.0) -> dict:
    rows = []
    for i, c in enumerate(cues):
        d = c["end"] - c["start"]
        issues = []
        r = cps(c["text"], d)
        if r > max_cps:
            issues.append(f"{r:.1f} cps > {max_cps:g}")
        if d < min_duration:
            issues.append(f"{d:.2f}s < {min_duration:g}s")
        if d > max_duration:
            issues.append(f"{d:.2f}s > {max_duration:g}s")
        rows.append({"index": i, "duration": round(d, 3), "cps": round(r, 2), "wpm": round(wpm(c["text"], d), 1),
                     "issues": issues})
    return {"cues": rows, "failing": sum(1 for r in rows if r["issues"]),
            "max_cps": max((r["cps"] for r in rows), default=0.0)}


def extend_to_readable(cues, max_cps: float = 20.0, min_duration: float = 0.7, min_gap: float = 0.083) -> list[dict]:
    out = [dict(c) for c in cues]
    for i, c in enumerate(out):
        need = max(min_duration, len(c["text"].replace("\n", " ").strip()) / max_cps)
        limit = out[i + 1]["start"] - min_gap if i + 1 < len(out) else float("inf")
        if c["end"] - c["start"] < need:
            c["end"] = max(c["end"], min(c["start"] + need, limit))
    return out
