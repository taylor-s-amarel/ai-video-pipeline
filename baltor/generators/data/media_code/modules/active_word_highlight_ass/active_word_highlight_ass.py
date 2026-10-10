"""ASS events that highlight the word being spoken (TikTok-style captions).

For a cue with word timings, emits one Dialogue event per word interval. All
words of the cue are visible in every event (so the line never reflows) and
the active word gets a highlight colour, optional scale and optional box via
a second colour on the border. Intervals run from each word's start to the
next word's start, so there is never a frame without a highlight inside the
cue.

Usage::

    from active_word_highlight_ass import highlight_events
    for start, end, text in highlight_events(words, cue_end=3.2, color="#FFD21F"):
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Caption,,0,0,0,,{text}")
"""

from __future__ import annotations

import re


def _bgr(hex_rgb: str) -> str:
    h = hex_rgb.lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
        raise ValueError(f"colour must be #RRGGBB, got {hex_rgb!r}")
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def _esc(t: str) -> str:
    return t.replace("\\", "＼").replace("{", "\\{").replace("}", "\\}")


def highlight_events(words: list[dict], cue_end: float | None = None, color: str = "#FFD21F",
                     scale: int = 100, uppercase: bool = False) -> list[tuple[float, float, str]]:
    if not words:
        return []
    for a, b in zip(words, words[1:]):
        if b["start"] < a["start"]:
            raise ValueError("words must be in time order")
    tokens = [_esc(w["word"].upper() if uppercase else w["word"]) for w in words]
    col = _bgr(color)
    events = []
    for i, w in enumerate(words):
        start = w["start"]
        end = words[i + 1]["start"] if i + 1 < len(words) else (cue_end if cue_end is not None else w["end"])
        if end <= start:
            continue
        parts = []
        for j, tok in enumerate(tokens):
            if j == i:
                sc = f"\\fscx{scale}\\fscy{scale}" if scale != 100 else ""
                parts.append(f"{{\\1c{col}{sc}}}{tok}{{\\r}}")
            else:
                parts.append(tok)
        events.append((start, end, " ".join(parts)))
    return events
