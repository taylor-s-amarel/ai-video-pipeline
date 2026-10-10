"""Phrase-aware caption chunking (one short line at a time, <= 7 words).

Chooses break points with dynamic programming instead of cutting every N
words. A chunk may hold at most ``max_words`` words and ``max_chars``
characters; among valid splits it prefers:

* breaking after punctuation (. , ; : ! ? and dashes),
* not ending a chunk on a function word ("the", "of", "to", "and", ...),
* not separating a number from the word after it ("14 days", "1,000 dogs"),
* breaking at pauses in the speech when word timings are given,
* chunks near ``target_words`` long and no one-word orphans.

Usage::

    from caption_chunker import chunk_text, chunk_words
    chunk_text("In 1970, five scientists lived underwater for 14 days off the Virgin Islands.")
    # timed words: [{"word": "In", "start": 0.0, "end": 0.12}, ...]
    chunk_words(words)  # -> [{"text": ..., "start": ..., "end": ..., "words": [...]}, ...]
"""

from __future__ import annotations

import re

FUNCTION_WORDS = {
    "a", "an", "the", "of", "to", "and", "or", "but", "in", "on", "at", "by", "for", "with", "from", "into",
    "onto", "as", "than", "that", "this", "these", "those", "my", "your", "his", "her", "its", "our", "their",
    "is", "are", "was", "were", "be", "been", "will", "would", "can", "could", "should", "if", "so", "not",
    "no", "very", "just", "about", "over", "under", "after", "before", "while", "when", "who", "which",
    "off", "up", "out", "through", "across", "around", "between", "against", "during", "without", "upon",
}
STRONG_PUNCT = re.compile(r"[.!?]['\")\]]*$")
SOFT_PUNCT = re.compile(r"[,;:—–-]['\")\]]*$")
NUMBERISH = re.compile(r"^[$£€]?\d[\d,.]*%?$")


def _break_cost(words: list[str], i: int, gaps: list[float] | None) -> float:
    """Cost of breaking after word index i (lower is better)."""
    w = words[i]
    cost = 3.0
    if STRONG_PUNCT.search(w):
        cost = -4.0
    elif SOFT_PUNCT.search(w):
        cost = -2.0
    core = re.sub(r"[^\w']", "", w).lower()
    if core in FUNCTION_WORDS and not (STRONG_PUNCT.search(w) or SOFT_PUNCT.search(w)):
        cost += 6.0
    if NUMBERISH.match(re.sub(r"[,.;:!?]$", "", w)) and not (STRONG_PUNCT.search(w) or SOFT_PUNCT.search(w)):
        cost += 5.0
    if gaps is not None and i < len(gaps):
        g = gaps[i]
        if g >= 0.5:
            cost -= 5.0
        elif g >= 0.25:
            cost -= 2.0
    return cost


def split_points(words: list[str], max_words: int = 7, max_chars: int = 32, target_words: int = 4,
                 gaps: list[float] | None = None) -> list[int]:
    """Indices where each chunk ends (exclusive), via DP minimising total cost."""
    n = len(words)
    if n == 0:
        return []
    if max_words < 1:
        raise ValueError("max_words must be >= 1")
    inf = float("inf")
    best = [inf] * (n + 1)
    back = [-1] * (n + 1)
    best[0] = 0.0
    for j in range(1, n + 1):
        chars = -1
        for k in range(1, max_words + 1):
            i = j - k
            if i < 0:
                break
            chars += len(words[i]) + 1
            if chars > max_chars and k > 1:
                break
            c = best[i] + abs(k - target_words) * 0.6
            if k == 1 and n > 1:
                c += 4.0
            if j < n:
                c += _break_cost(words, j - 1, gaps)
            if c < best[j]:
                best[j], back[j] = c, i
    ends = []
    j = n
    while j > 0:
        ends.append(j)
        j = back[j]
    return sorted(ends)


def chunk_text(text: str, **kw) -> list[str]:
    words = text.split()
    out, start = [], 0
    for end in split_points(words, **kw):
        out.append(" ".join(words[start:end]))
        start = end
    return out


def chunk_words(words: list[dict], **kw) -> list[dict]:
    """Chunk timed words ({'word', 'start', 'end'}); pauses between words guide the breaks."""
    tokens = [w["word"].strip() for w in words]
    gaps = [max(0.0, words[i + 1]["start"] - words[i]["end"]) for i in range(len(words) - 1)]
    out, start = [], 0
    for end in split_points(tokens, gaps=gaps, **kw):
        group = words[start:end]
        out.append({"text": " ".join(tokens[start:end]), "start": group[0]["start"], "end": group[-1]["end"],
                    "words": group})
        start = end
    return out
