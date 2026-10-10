"""Staggered word entrances: per-word start times and per-frame state.

Each word enters ``stagger`` seconds after the previous one, taking
``enter`` seconds to fade from 0 to ``max_opacity`` while rising ``rise_px``
pixels (ease-out-cubic). Opacity never exceeds ``max_opacity`` (default 0.98,
matching the house rule that no layer is fully opaque).

Usage::

    from word_stagger_timing import schedule, state_at
    sch = schedule("FIVE SCIENTISTS LIVED UNDERWATER", start=2.0, stagger=0.08)
    state_at(sch, 2.1)    # [{'word': 'FIVE', 'opacity': ..., 'dy': ...}, ...]
"""

from __future__ import annotations


def _out_cubic(x: float) -> float:
    return 1 - (1 - x) ** 3


def schedule(text_or_words, start: float = 0.0, stagger: float = 0.08, enter: float = 0.22,
             word_times: list[float] | None = None) -> list[dict]:
    """Word entrance windows. ``word_times`` (e.g. from TTS word timestamps) overrides stagger."""
    words = text_or_words.split() if isinstance(text_or_words, str) else list(text_or_words)
    if word_times is not None and len(word_times) != len(words):
        raise ValueError("word_times must have one time per word")
    if enter <= 0:
        raise ValueError("enter must be > 0")
    out = []
    for i, w in enumerate(words):
        s = word_times[i] if word_times is not None else start + i * stagger
        out.append({"word": w, "index": i, "start": s, "end": s + enter})
    return out


def state_at(sched: list[dict], t: float, rise_px: float = 24.0, max_opacity: float = 0.98) -> list[dict]:
    if not 0 <= max_opacity <= 1:
        raise ValueError("max_opacity must be within [0, 1]")
    out = []
    for w in sched:
        if t <= w["start"]:
            p = 0.0
        elif t >= w["end"]:
            p = 1.0
        else:
            p = _out_cubic((t - w["start"]) / (w["end"] - w["start"]))
        out.append({"word": w["word"], "opacity": round(max_opacity * p, 6), "dy": rise_px * (1 - p)})
    return out


def frames(sched: list[dict], fps: float, until: float, **kw) -> list[list[dict]]:
    n = int(round(until * fps)) + 1
    return [state_at(sched, i / fps, **kw) for i in range(n)]


def total_duration(sched: list[dict]) -> float:
    return max(w["end"] for w in sched) - min(w["start"] for w in sched) if sched else 0.0
