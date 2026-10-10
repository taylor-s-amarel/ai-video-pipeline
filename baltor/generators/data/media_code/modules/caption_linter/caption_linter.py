"""Lint caption cues against short-video house rules.

Checks each cue and the track as a whole:

* at most ``max_words`` words (default 7) and ``max_lines`` lines (default 1);
* duration between ``min_duration`` and ``max_duration``;
* no overlaps, no empty text, times inside the video;
* no forbidden content such as progress-bar glyphs or repeated section labels
  ("FACT 1" style labels belong in their own layer, not in every caption);
* optional sync check against word timestamps (start within ``sync_ms``).

Returns a list of findings (rule, cue index, message); empty means pass.

Usage::

    from caption_linter import lint
    findings = lint(cues, video_duration=64.0, words=words)
"""

from __future__ import annotations

import re

LABEL = re.compile(r"^\s*(FACT|TIP|STEP|PART)\s+\d+\b", re.I)
PROGRESS = re.compile(r"[█░▒▓■□]{3,}|\[[#=\-]{3,}\]")


def lint(cues: list[dict], video_duration: float | None = None, words: list[dict] | None = None,
         max_words: int = 7, max_lines: int = 1, min_duration: float = 0.5, max_duration: float = 6.0,
         sync_ms: float = 150.0) -> list[dict]:
    out = []

    def add(rule, i, msg):
        out.append({"rule": rule, "cue": i, "message": msg})

    for i, c in enumerate(cues):
        text = c.get("text", "")
        n_words = len(text.split())
        if not text.strip():
            add("empty", i, "empty caption")
        if n_words > max_words:
            add("max_words", i, f"{n_words} words > {max_words}")
        lines = [l for l in text.split("\n") if l.strip()]
        if len(lines) > max_lines:
            add("max_lines", i, f"{len(lines)} lines > {max_lines}")
        d = c["end"] - c["start"]
        if d < min_duration:
            add("min_duration", i, f"{d:.2f}s < {min_duration}s")
        if d > max_duration:
            add("max_duration", i, f"{d:.2f}s > {max_duration}s")
        if c["start"] < 0 or (video_duration is not None and c["end"] > video_duration + 1e-6):
            add("bounds", i, "cue outside the video")
        if LABEL.match(text):
            add("label_in_caption", i, "section label inside a caption")
        if PROGRESS.search(text):
            add("progress_bar", i, "progress-bar glyphs in caption")
    for i, (a, b) in enumerate(zip(cues, cues[1:])):
        if b["start"] < a["end"] - 1e-9:
            add("overlap", i, f"overlaps next cue by {a['end'] - b['start']:.3f}s")
    if words:
        starts = sorted(w["start"] for w in words)
        for i, c in enumerate(cues):
            nearest = min(starts, key=lambda s: abs(s - c["start"]))
            if abs(nearest - c["start"]) * 1000 > sync_ms:
                add("sync", i, f"starts {abs(nearest - c['start']) * 1000:.0f} ms from the nearest spoken word")
    return out


def summary(findings: list[dict]) -> dict:
    by_rule: dict[str, int] = {}
    for f in findings:
        by_rule[f["rule"]] = by_rule.get(f["rule"], 0) + 1
    return {"passed": not findings, "count": len(findings), "by_rule": by_rule}
