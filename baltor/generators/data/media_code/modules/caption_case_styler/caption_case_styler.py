"""Caption casing: UPPER, Title Case and Sentence case that respect acronyms.

* ``upper`` capitalises everything except tokens in ``keep`` (for example
  "iPhone" or "mRNA") whose casing is fixed;
* ``title`` capitalises words except short function words (a, an, the, and,
  but, or, for, nor, on, at, to, by, of, in, up, as), which stay lower case
  unless first or last; existing ALL-CAPS acronyms (NASA, DNA) stay (when the
  whole input is in capitals, only words in ``keep`` are protected);
* ``sentence`` lower-cases words that are not acronyms and capitalises the
  first letter of each sentence.

Usage::

    from caption_case_styler import style
    style("the dna of a nasa probe", "title", keep={"DNA", "NASA"})   # 'The DNA of a NASA Probe'
"""

from __future__ import annotations

import re

SMALL = {"a", "an", "the", "and", "but", "or", "for", "nor", "on", "at", "to", "by", "of", "in", "up", "as"}
_SPLIT = re.compile(r"(\s+)")


def _keep_map(keep) -> dict[str, str]:
    return {k.lower(): k for k in (keep or [])}


def _is_acronym(word: str) -> bool:
    letters = re.sub(r"[^A-Za-z]", "", word)
    return len(letters) >= 2 and letters.isupper()


def _cap(word: str) -> str:
    m = re.search(r"[A-Za-z]", word)
    if not m:
        return word
    i = m.start()
    return word[:i] + word[i].upper() + word[i + 1:].lower()


def style(text: str, mode: str, keep=None) -> str:
    if mode not in ("upper", "title", "sentence"):
        raise ValueError("mode must be upper, title or sentence")
    kmap = _keep_map(keep)
    letters = re.sub(r"[^A-Za-z]", "", text)
    # in ALL-CAPS input every word looks like an acronym: then only ``keep`` protects casing
    shouting = len(letters) > 3 and letters.isupper()
    is_acro = (lambda w: False) if shouting else _is_acronym
    parts = _SPLIT.split(text)
    words_idx = [i for i, p in enumerate(parts) if p and not p.isspace()]
    out = list(parts)
    new_sentence = True
    for n, i in enumerate(words_idx):
        w = parts[i]
        core = re.sub(r"^[^\w]+|[^\w]+$", "", w)
        fixed = kmap.get(core.lower())
        if fixed:
            res = w.replace(core, fixed)
        elif mode == "upper":
            res = w.upper()
        elif mode == "title":
            if is_acro(w):
                res = w
            elif core.lower() in SMALL and 0 < n < len(words_idx) - 1:
                res = w.lower()
            else:
                res = "-".join(_cap(x) for x in w.split("-"))
        else:
            res = w if is_acro(w) else w.lower()
            if new_sentence and not is_acro(res):
                res = _cap(res)
        out[i] = res
        new_sentence = bool(re.search(r"[.!?]['\")]*$", w))
    return "".join(out)
