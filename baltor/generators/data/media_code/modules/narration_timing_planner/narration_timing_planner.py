"""Plan narration length from words per minute (WPM).

* ``duration_for(text, wpm)``: estimated speaking time, with pauses for
  sentence ends and section breaks;
* ``wpm_needed(text, target_s)``: the rate that fits a target length;
* ``plan_segments(segments, wpm, min_total, max_total)``: per-segment timing,
  totals, and advice when the script is too short for a 60 s minimum or too
  long for the maximum (add or cut about N words);
* ``words_for(seconds, wpm)``: script budget for a target duration.

Default rate band is 140-160 WPM (the house narration range); the numbers are
estimates for planning and are checked against the real TTS duration after
synthesis.

Usage::

    from narration_timing_planner import plan_segments
    plan_segments([{"label": "HOOK", "text": "..."}, {"label": "FACT 1", "text": "..."}], wpm=150)
"""

from __future__ import annotations

import re


def word_count(text: str) -> int:
    return sum(1 for tok in text.split() if re.search(r"\w", tok))


def pause_seconds(text: str, sentence_pause: float = 0.3) -> float:
    return len(re.findall(r"[.!?](?:\s|$)", text)) * sentence_pause


def duration_for(text: str, wpm: float = 150.0, sentence_pause: float = 0.3) -> float:
    if wpm <= 0:
        raise ValueError("wpm must be > 0")
    return word_count(text) / wpm * 60.0 + pause_seconds(text, sentence_pause)


def wpm_needed(text: str, target_s: float, sentence_pause: float = 0.3) -> float:
    speaking = target_s - pause_seconds(text, sentence_pause)
    if speaking <= 0:
        raise ValueError("target is shorter than the pauses alone")
    return word_count(text) / speaking * 60.0


def words_for(seconds: float, wpm: float = 150.0) -> int:
    return int(round(seconds * wpm / 60.0))


def plan_segments(segments: list[dict], wpm: float = 150.0, min_total: float = 60.0, max_total: float = 90.0,
                  section_pause: float = 0.6, wpm_band=(140.0, 160.0)) -> dict:
    t = 0.0
    rows = []
    for i, s in enumerate(segments):
        d = duration_for(s["text"], wpm)
        rows.append({"label": s.get("label", f"segment {i + 1}"), "start": round(t, 2), "duration": round(d, 2),
                     "words": word_count(s["text"])})
        t += d + (section_pause if i < len(segments) - 1 else 0.0)
    total = round(t, 2)
    advice = []
    if total < min_total:
        advice.append(f"too short by {min_total - total:.1f}s: add about {words_for(min_total - total, wpm)} words")
    if total > max_total:
        advice.append(f"too long by {total - max_total:.1f}s: cut about {words_for(total - max_total, wpm)} words")
    if not wpm_band[0] <= wpm <= wpm_band[1]:
        advice.append(f"{wpm:g} WPM is outside the {wpm_band[0]:g}-{wpm_band[1]:g} band")
    return {"segments": rows, "total_s": total, "ok": not advice, "advice": advice}
