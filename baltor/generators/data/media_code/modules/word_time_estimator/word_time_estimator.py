"""Estimate word timings inside a timed segment when no aligner is available.

Spreads a segment's duration over its words in proportion to an estimate of
spoken length: English syllable count (vowel-group heuristic with silent-e,
-le, -ed and two-syllable vowel-pair rules; expect a few misses per hundred
words), numbers expanded to their syllables, and pauses
after commas and full stops. Good enough for caption chunk timing and
keyword pops; use a forced aligner when you need frame accuracy.

Usage::

    from word_time_estimator import estimate, syllables
    syllables("underwater")                  # 4
    estimate("In 1970, five scientists lived underwater.", start=2.0, end=5.4)
"""

from __future__ import annotations

import re

_VOWELS = re.compile(r"[aeiouy]+")
_DIGIT_SYL = {"0": 2, "1": 1, "2": 1, "3": 1, "4": 1, "5": 1, "6": 1, "7": 2, "8": 1, "9": 1}


def syllables(word: str) -> int:
    w = re.sub(r"[^a-z0-9]", "", word.lower())
    if not w:
        return 0
    if w.isdigit():
        if len(w) == 4 and w[0] in "12":   # years read in pairs: nineteen seventy
            return 4
        return max(1, sum(_DIGIT_SYL[d] for d in w) + max(0, len(w) - 2))
    if len(w) <= 3:
        return 1
    count = len(_VOWELS.findall(w))
    # vowel pairs usually spoken as two syllables (radio, media, violin), except -tion/-sion/-cious
    count += len(re.findall(r"(?<![tsc])i[ao]", w)) + len(re.findall(r"[^aeiou]eo", w))
    if w.endswith("e") and not w.endswith(("le", "ee", "ye")) and count > 1:
        count -= 1
    if w.endswith("le") and len(w) > 2 and w[-3] not in "aeiouy":
        count = max(count, 2) if count < 2 else count
    if w.endswith(("ed",)) and not w.endswith(("ted", "ded")) and count > 1:
        count -= 1
    return max(1, count)


def weights(words: list[str], comma_pause: float = 1.5, stop_pause: float = 3.0) -> list[tuple[float, float]]:
    """(speech_weight, pause_after_weight) per word, in syllable units."""
    out = []
    for w in words:
        pause = stop_pause if re.search(r"[.!?]['\")]*$", w) else comma_pause if re.search(r"[,;:]$", w) else 0.0
        out.append((max(1, syllables(w)) + 0.3, pause))
    return out


def estimate(text: str, start: float, end: float, **kw) -> list[dict]:
    if end <= start:
        raise ValueError("end must be after start")
    words = text.split()
    if not words:
        return []
    ws = weights(words, **kw)
    ws[-1] = (ws[-1][0], 0.0)  # no pause after the last word inside the segment
    total = sum(a + b for a, b in ws)
    scale = (end - start) / total
    out, t = [], start
    for w, (speech, pause) in zip(words, ws):
        w_end = t + speech * scale
        out.append({"word": w, "start": round(t, 3), "end": round(w_end, 3)})
        t = w_end + pause * scale
    out[-1]["end"] = round(end, 3)
    return out
