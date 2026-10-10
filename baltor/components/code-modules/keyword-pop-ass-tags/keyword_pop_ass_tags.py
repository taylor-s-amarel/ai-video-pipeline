"""Build ASS caption lines where the key word pops and changes colour.

For one caption event, wraps the chosen word in override tags that scale it
1.0 -> ``peak`` -> 1.0 over ``duration_ms`` (default 1.12 over 180 ms) starting
when the word is spoken, optionally recolouring it (house yellow #FFD21F).
Other words are escaped plain text, so caption text cannot inject tags.
``\\r`` after the word resets to the event style.

Usage::

    from keyword_pop_ass_tags import pop_line
    text = pop_line("lived underwater for 14 days", key_index=3, word_offset_ms=820,
                    color="#FFD21F")
    # -> 'lived underwater for {\\1c&H1FD2FF&\\fscx100\\fscy100\\t(820,892,...)}14{\\r} days'
"""

from __future__ import annotations

import re


def bgr(hex_rgb: str) -> str:
    h = hex_rgb.lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
        raise ValueError(f"colour must be #RRGGBB, got {hex_rgb!r}")
    return f"&H{h[4:6]}{h[2:4]}{h[0:2]}&".upper()


def escape(text: str) -> str:
    return text.replace("\\", "\uff3c").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def pop_tags(start_ms: int, peak: float = 1.12, duration_ms: int = 180, rise_fraction: float = 0.4,
             color: str | None = None) -> str:
    if start_ms < 0 or duration_ms <= 0:
        raise ValueError("start_ms must be >= 0 and duration_ms > 0")
    p = int(round(peak * 100))
    mid = start_ms + int(round(duration_ms * rise_fraction))
    end = start_ms + duration_ms
    col = f"\\1c{bgr(color)}" if color else ""
    return (f"{{{col}\\fscx100\\fscy100\\t({start_ms},{mid},0.5,\\fscx{p}\\fscy{p})"
            f"\\t({mid},{end},2,\\fscx100\\fscy100)}}")


def pop_line(text: str, key_index: int, word_offset_ms: int = 0, color: str | None = "#FFD21F",
             peak: float = 1.12, duration_ms: int = 180) -> str:
    words = text.split()
    if not 0 <= key_index < len(words):
        raise IndexError("key_index out of range")
    parts = []
    for i, w in enumerate(words):
        if i == key_index:
            parts.append(pop_tags(word_offset_ms, peak, duration_ms, color=color) + escape(w) + "{\\r}")
        else:
            parts.append(escape(w))
    return " ".join(parts)


def pop_line_from_words(words: list[dict], key_index: int, cue_start: float, **kw) -> str:
    """Same as ``pop_line`` but the pop starts when ``words[key_index]`` is spoken."""
    text = " ".join(w["word"] for w in words)
    offset = int(round((words[key_index]["start"] - cue_start) * 1000))
    return pop_line(text, key_index, max(0, offset), **kw)
