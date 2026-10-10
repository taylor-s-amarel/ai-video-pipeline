"""Clean spoken-word transcripts for captions: fillers, stutters, spacing.

Removes standalone fillers ("um", "uh", "er", "erm", "hmm"), immediate word
repeats ("the the"), and stutter fragments ("w- we"), normalises spacing
around punctuation, curly quotes and dashes, and can optionally drop a
configurable list of discourse markers ("you know", "I mean"). Timed words
can be filtered too, keeping each kept word's original timing.

Only clear fillers are removed by default: words like "like" and "so" carry
meaning too often to drop automatically.

Usage::

    from caption_disfluency_filter import clean_text, clean_words
    clean_text("So, um, the the reef was, uh, w- well alive")   # 'So, the reef was, well alive'
"""

from __future__ import annotations

import re

FILLERS = {"um", "umm", "uh", "uhh", "er", "erm", "hmm", "mm", "ah"}
DISCOURSE = ("you know", "i mean", "sort of", "kind of")


def _core(w: str) -> str:
    return re.sub(r"[^\w'-]", "", w.lower())


def clean_tokens(tokens: list[str], drop_discourse: bool = False) -> list[int]:
    """Indices of tokens to keep."""
    keep = []
    n = len(tokens)
    skip_until = -1
    for i, tok in enumerate(tokens):
        if i <= skip_until:
            continue
        core = _core(tok)
        if core in FILLERS:
            # move trailing punctuation of a removed filler to the previous kept token
            if keep and re.search(r"[.!?]$", tok) and not re.search(r"[.!?,;:]$", tokens[keep[-1]]):
                tokens[keep[-1]] = tokens[keep[-1]] + tok[-1]
            continue
        if core.endswith("-") and i + 1 < n and _core(tokens[i + 1]).startswith(core.rstrip("-")):
            continue  # stutter fragment
        if keep and core and core == _core(tokens[keep[-1]]) and not re.search(r"[.!?,;:]$", tokens[keep[-1]]):
            continue  # immediate repeat
        if drop_discourse:
            hit = False
            for phrase in DISCOURSE:
                parts = phrase.split()
                window = [_core(t) for t in tokens[i:i + len(parts)]]
                if window == parts:
                    skip_until = i + len(parts) - 1
                    hit = True
                    break
            if hit:
                continue
        keep.append(i)
    return keep


def normalise_punctuation(text: str) -> str:
    t = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    t = re.sub(r",\s*,+", ",", t)
    t = re.sub(r"^[,;:\s]+", "", t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()


def clean_text(text: str, drop_discourse: bool = False) -> str:
    tokens = text.split()
    kept = clean_tokens(tokens, drop_discourse)
    out = " ".join(tokens[i] for i in kept)
    out = re.sub(r"(\w),\s*,", r"\1,", out)
    return normalise_punctuation(out)


def clean_words(words: list[dict], drop_discourse: bool = False) -> list[dict]:
    tokens = [w["word"] for w in words]
    kept = clean_tokens(tokens, drop_discourse)
    return [{**words[i], "word": tokens[i]} for i in kept]
