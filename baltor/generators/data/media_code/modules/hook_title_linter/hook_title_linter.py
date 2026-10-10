"""Lint first-frame hook titles: short, specific, not a copy of the caption.

Checks a hook title (the bold text on the first frame) against simple,
explainable rules:

* 2-7 words and at most ``max_chars`` characters;
* not identical to (or a prefix of) the first caption line;
* contains something concrete: a number, a proper noun or a strong noun from
  a supplied topic list (vague hooks like "YOU WON'T BELIEVE THIS" fail);
* no filler phrases from a configurable list, no trailing ellipsis, no
  emoji-only or punctuation-only titles.

Usage::

    from hook_title_linter import lint
    lint("SHE LIVED UNDERWATER FOR 14 DAYS", first_caption="In 1970, five scientists")   # []
"""

from __future__ import annotations

import re

VAGUE = ("you won't believe", "this will shock you", "wait for it", "watch till the end", "must see",
         "crazy fact", "mind blowing", "say it clearly")


def lint(title: str, first_caption: str = "", topic_terms=(), max_words: int = 7, min_words: int = 2,
         max_chars: int = 40) -> list[str]:
    probs = []
    t = " ".join(title.split())
    words = t.split()
    if not re.search(r"[A-Za-z0-9]", t):
        return ["title has no letters or digits"]
    if not min_words <= len(words) <= max_words:
        probs.append(f"{len(words)} words (use {min_words}-{max_words})")
    if len(t) > max_chars:
        probs.append(f"{len(t)} characters (max {max_chars})")
    norm = lambda s: re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()
    if first_caption and (norm(t) == norm(first_caption) or norm(first_caption).startswith(norm(t))):
        probs.append("title repeats the first caption; make it its own hook")
    low = t.lower()
    for v in VAGUE:
        if v in low:
            probs.append(f"vague filler phrase: '{v}'")
    has_number = bool(re.search(r"\d", t))
    has_proper = any(w[0].isupper() and not w.isupper() for w in words[1:])
    has_topic = any(term.lower() in low for term in topic_terms)
    if not (has_number or has_proper or has_topic):
        probs.append("nothing concrete: add a number, a name or the topic")
    if t.endswith("...") or t.endswith("…"):
        probs.append("trailing ellipsis")
    return probs
