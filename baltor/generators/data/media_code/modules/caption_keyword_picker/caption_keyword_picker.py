"""Pick the one word per caption that should pop.

Scoring, highest first:

1. numbers, percentages, money and years ("14", "86%", "$2.5M", "1970");
2. words in a caller-supplied emphasis list (topic terms);
3. capitalised words that are not the first word (likely proper nouns);
4. the longest content word (stop words never pop).

Returns the index of the chosen word, or ``None`` when every word is a stop
word. ``pick_all`` spaces pops out so two neighbouring captions do not both
pop the same word.

Usage::

    from caption_keyword_picker import pick, pick_all
    pick("lived underwater for 14 days")         # 3
    pick("Grace Hopper found a moth")             # 1 ('Hopper' over 'Grace' only if not first word)
"""

from __future__ import annotations

import re

STOP = {"a", "an", "the", "of", "to", "and", "or", "but", "in", "on", "at", "by", "for", "with", "from", "is",
        "are", "was", "were", "be", "been", "it", "its", "this", "that", "these", "those", "i", "you", "he",
        "she", "we", "they", "my", "your", "his", "her", "our", "their", "as", "so", "if", "then", "than",
        "just", "very", "not", "no", "do", "did", "does", "have", "has", "had", "will", "would", "can", "could"}
NUMBER = re.compile(r"^[$£€]?\d[\d,]*(\.\d+)?([kKmMbB]|%|x)?$")


def _core(w: str) -> str:
    return re.sub(r"^[^\w$£€]+|[^\w%]+$", "", w)


def score(word: str, position: int, emphasis: set[str]) -> float:
    core = _core(word)
    low = core.lower()
    if not core or low in STOP:
        return 0.0
    if NUMBER.match(core):
        return 100.0 + len(core)
    if low in emphasis:
        return 80.0 + len(core)
    if position > 0 and core[0].isupper() and not core.isupper():
        return 60.0 + len(core)
    return 10.0 + len(core)


def pick(text: str, emphasis: set[str] | None = None, avoid: set[str] | None = None) -> int | None:
    words = text.split()
    emphasis = {e.lower() for e in (emphasis or set())}
    avoid = {a.lower() for a in (avoid or set())}
    best, best_score = None, 0.0
    for i, w in enumerate(words):
        s = score(w, i, emphasis)
        if _core(w).lower() in avoid:
            s *= 0.5
        if s > best_score:
            best, best_score = i, s
    return best


def pick_all(captions: list[str], emphasis: set[str] | None = None) -> list[int | None]:
    out, previous = [], None
    for text in captions:
        avoid = {previous} if previous else set()
        idx = pick(text, emphasis, avoid)
        out.append(idx)
        previous = _core(text.split()[idx]).lower() if idx is not None else None
    return out
