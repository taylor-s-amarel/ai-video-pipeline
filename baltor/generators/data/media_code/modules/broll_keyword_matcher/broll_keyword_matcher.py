"""Match narration sentences to B-roll clips by keywords (TF-IDF, numpy).

Each asset has tags or a description; each sentence is scored against every
asset with TF-IDF cosine similarity over normalised words (lower case, light
plural stemming, stop words removed). ``assign`` picks the best asset per
sentence while avoiding reuse of the same clip within ``no_repeat`` sentences
and reports sentences with no good match (so you know what footage is
missing instead of forcing an unrelated clip).

Usage::

    from broll_keyword_matcher import assign
    assign(sentences, {"ocean_waves.mp4": "ocean waves sea surface", "reef.mp4": "coral reef fish diver"})
"""

from __future__ import annotations

import math
import re

STOP = {"a", "an", "the", "of", "to", "and", "or", "in", "on", "at", "by", "for", "with", "from", "is", "are", "was",
        "were", "it", "this", "that", "they", "she", "he", "we", "you", "i", "as", "be", "been", "has", "have", "had",
        "their", "her", "his", "its", "our", "into", "than", "then", "so", "but", "not", "no", "just", "very"}


def tokens(text: str) -> list[str]:
    out = []
    for w in re.findall(r"[a-z0-9']+", text.lower()):
        if w in STOP or len(w) < 2:
            continue
        if len(w) > 4 and w.endswith("ies"):
            w = w[:-3] + "y"
        elif len(w) > 4 and w.endswith(("shes", "ches", "xes", "sses", "zes")):
            w = w[:-2]
        elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return out


def _vectors(docs: list[list[str]]):
    vocab = sorted({t for d in docs for t in d})
    idx = {t: i for i, t in enumerate(vocab)}
    n = len(docs)
    df = [0] * len(vocab)
    for d in docs:
        for t in set(d):
            df[idx[t]] += 1
    idf = [math.log((1 + n) / (1 + c)) + 1 for c in df]
    vecs = []
    for d in docs:
        v = [0.0] * len(vocab)
        for t in d:
            v[idx[t]] += 1.0
        v = [x * idf[i] for i, x in enumerate(v)]
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        vecs.append([x / norm for x in v])
    return vecs


def scores(sentences: list[str], assets: dict) -> list[list[float]]:
    names = list(assets)
    docs = [tokens(s) for s in sentences] + [tokens(assets[n]) for n in names]
    vecs = _vectors(docs)
    sv, av = vecs[:len(sentences)], vecs[len(sentences):]
    return [[sum(a * b for a, b in zip(s, x)) for x in av] for s in sv]


def assign(sentences: list[str], assets: dict, min_score: float = 0.12, no_repeat: int = 2) -> list[dict]:
    names = list(assets)
    if not names:
        raise ValueError("no assets")
    sc = scores(sentences, assets)
    out, recent = [], []
    for i, row in enumerate(sc):
        order = sorted(range(len(names)), key=lambda j: -row[j])
        choice = next((j for j in order if names[j] not in recent[-no_repeat:]), order[0]) if no_repeat else order[0]
        ok = row[choice] >= min_score
        out.append({"sentence": sentences[i], "asset": names[choice] if ok else None,
                    "score": round(row[choice], 4), "best_alternatives": [names[j] for j in order[:3]]})
        if ok:
            recent.append(names[choice])
    return out
