"""Typewriter text reveal: timing with punctuation pauses and stable-layout ASS.

``reveal_schedule`` gives the time at which each character appears, typing
at ``cps`` characters per second with extra pauses after punctuation.
``ass_events`` writes one ASS Dialogue text per reveal step where the hidden
remainder is drawn fully transparent (``{\\alpha&HFF&}``), so line breaks and
centring never jump while the text types on.

Usage::

    from typewriter_reveal_timing import reveal_schedule, visible_at, ass_events
    sched = reveal_schedule("In 1970, five scientists...", cps=22)
    visible_at("In 1970, five", sched, 0.4)
    for start, end, text in ass_events("Hello, world.", start=1.0, end=4.0): ...
"""

from __future__ import annotations

DEFAULT_PAUSES = {",": 0.12, ";": 0.18, ":": 0.18, ".": 0.32, "!": 0.32, "?": 0.32, "\n": 0.25}


def reveal_schedule(text: str, cps: float = 20.0, start: float = 0.0, pauses: dict | None = None,
                    skip_spaces: bool = True) -> list[float]:
    """Appearance time (s) of each character of ``text``."""
    if cps <= 0:
        raise ValueError("cps must be > 0")
    pauses = DEFAULT_PAUSES if pauses is None else pauses
    times = []
    t = start
    for i, ch in enumerate(text):
        times.append(t)
        if not (skip_spaces and ch == " "):
            t += 1.0 / cps
        # pause after punctuation only when followed by whitespace or end of text
        nxt = text[i + 1] if i + 1 < len(text) else " "
        if ch in pauses and (nxt.isspace()):
            t += pauses[ch]
    return times


def visible_at(text: str, schedule: list[float], t: float) -> str:
    return "".join(ch for ch, at in zip(text, schedule) if at <= t)


def duration(schedule: list[float], cps: float = 20.0) -> float:
    return (schedule[-1] - schedule[0] + 1.0 / cps) if schedule else 0.0


def _ass_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def ass_events(text: str, start: float, end: float, cps: float = 20.0, pauses: dict | None = None):
    """(start_s, end_s, ass_text) tuples; each step shows typed text + transparent remainder."""
    sched = reveal_schedule(text, cps, start, pauses)
    steps = sorted(set(sched))
    out = []
    for k, t in enumerate(steps):
        if t >= end:
            break
        t_next = steps[k + 1] if k + 1 < len(steps) else end
        n = sum(1 for at in sched if at <= t)
        shown, hidden = text[:n], text[n:]
        body = _ass_escape(shown) + ("{\\alpha&HFF&}" + _ass_escape(hidden) if hidden else "")
        out.append((t, min(t_next, end), body))
    return out
