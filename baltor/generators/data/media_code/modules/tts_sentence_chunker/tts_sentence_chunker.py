"""Split a narration script into TTS-sized chunks without breaking sentences.

Local TTS models work best on one sentence or a few short ones at a time and
some have input length limits. This splitter:

* finds sentence ends while ignoring abbreviations (Dr., e.g., U.S.),
  decimals (3.14), initials (J. R.) and ellipses inside sentences;
* packs whole sentences into chunks up to ``max_chars``;
* splits an over-long sentence at ; : , then at spaces, never mid-word;
* records the boundary after each chunk (``sentence`` or ``paragraph``) so
  the assembler can insert the right pause.

Usage::

    from tts_sentence_chunker import sentences, chunks
    for c in chunks(script, max_chars=280):
        print(c["text"], c["boundary"])
"""

from __future__ import annotations

import re

ABBREV = {"dr", "mr", "mrs", "ms", "prof", "sr", "jr", "st", "vs", "etc", "e.g", "i.e", "u.s", "u.k", "no", "fig",
          "approx", "dept", "est", "inc", "ltd", "co", "mt", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep",
          "sept", "oct", "nov", "dec"}
_END = re.compile(r'([.!?]+["\')\]]*)(\s+)')


def sentences(text: str) -> list[str]:
    out, start = [], 0
    t = re.sub(r"[ \t]+", " ", text.strip())
    for m in _END.finditer(t):
        end = m.end(1)
        before = t[start:end]
        word = re.search(r"(\S+)$", before[:-len(m.group(1))] if m.group(1) else before)
        token = (word.group(1) if word else "").lower().rstrip(".")
        if m.group(1).startswith(".") and len(m.group(1)) == 1:
            if token in ABBREV or re.fullmatch(r"[a-z]", token) or re.fullmatch(r"(?:[a-z]\.)+[a-z]", token):
                continue
            nxt = t[m.end():m.end() + 1]
            if nxt and nxt.islower():
                continue
        s = t[start:end].strip()
        if s:
            out.append(s)
        start = m.end()
    tail = t[start:].strip()
    if tail:
        out.append(tail)
    return out


def _split_long(sentence: str, max_chars: int) -> list[str]:
    if len(sentence) <= max_chars:
        return [sentence]
    for pattern in (r"(?<=[;:])\s+", r"(?<=,)\s+", r"\s+"):
        parts = re.split(pattern, sentence)
        if len(parts) > 1:
            out, cur = [], ""
            for p in parts:
                cand = f"{cur} {p}".strip()
                if len(cand) <= max_chars or not cur:
                    cur = cand
                else:
                    out.append(cur)
                    cur = p
            if cur:
                out.append(cur)
            if all(len(x) <= max_chars for x in out):
                return out
            return [y for x in out for y in _split_long(x, max_chars)] if pattern != r"\s+" else out
    return [sentence]


def chunks(script: str, max_chars: int = 280) -> list[dict]:
    if max_chars < 20:
        raise ValueError("max_chars must be at least 20")
    out: list[dict] = []
    paragraphs = [p for p in re.split(r"\n\s*\n", script) if p.strip()]
    for pi, para in enumerate(paragraphs):
        cur = ""
        pieces = [x for s in sentences(para) for x in _split_long(s, max_chars)]
        for piece in pieces:
            cand = f"{cur} {piece}".strip()
            if cur and len(cand) > max_chars:
                out.append({"text": cur, "boundary": "sentence"})
                cur = piece
            else:
                cur = cand
        if cur:
            out.append({"text": cur, "boundary": "paragraph" if pi < len(paragraphs) - 1 else "end"})
    return out
