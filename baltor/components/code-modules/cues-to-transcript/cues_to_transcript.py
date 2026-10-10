"""Turn caption cues into a readable transcript.

* removes the rolling duplication of auto-generated captions, where each cue
  repeats the previous line and adds a few words;
* starts a new paragraph after a pause longer than ``paragraph_gap`` seconds
  or after ``max_sentences`` sentences;
* optionally prefixes each paragraph with a ``[mm:ss]`` timestamp.

Usage::

    from cues_to_transcript import transcript
    print(transcript(cues, timestamps=True))
"""

from __future__ import annotations

import re


def _ts(t: float) -> str:
    m, s = divmod(int(t), 60)
    h, m = divmod(m, 60)
    return f"[{h}:{m:02d}:{s:02d}]" if h else f"[{m:02d}:{s:02d}]"


def dedupe_rolling(cues: list[dict]) -> list[dict]:
    """Drop the part of each cue that repeats the end of the text so far."""
    out = []
    so_far: list[str] = []
    for c in cues:
        words = c["text"].replace("\n", " ").split()
        overlap = 0
        for k in range(min(len(words), len(so_far)), 0, -1):
            if [w.lower() for w in so_far[-k:]] == [w.lower() for w in words[:k]]:
                overlap = k
                break
        new = words[overlap:]
        if new:
            out.append({**c, "text": " ".join(new)})
            so_far.extend(new)
    return out


def paragraphs(cues: list[dict], paragraph_gap: float = 2.0, max_sentences: int = 4) -> list[dict]:
    paras: list[dict] = []
    last_end = None
    for c in cues:
        text = " ".join(c["text"].split())
        if not text:
            continue
        new_para = (not paras or (last_end is not None and c["start"] - last_end > paragraph_gap)
                    or len(re.findall(r"[.!?](?:\s|$)", paras[-1]["text"])) >= max_sentences)
        if new_para:
            paras.append({"start": c["start"], "text": text})
        else:
            paras[-1]["text"] += " " + text
        last_end = c["end"]
    return paras


def transcript(cues: list[dict], timestamps: bool = False, dedupe: bool = True, **kw) -> str:
    seq = dedupe_rolling(cues) if dedupe else cues
    out = []
    for p in paragraphs(seq, **kw):
        out.append(f"{_ts(p['start'])} {p['text']}" if timestamps else p["text"])
    return "\n\n".join(out) + ("\n" if out else "")
