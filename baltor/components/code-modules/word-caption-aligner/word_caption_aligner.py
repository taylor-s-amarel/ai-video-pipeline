"""Retime captions to spoken word timestamps and report the drift.

Captions are often written from the script with planned times, while the
narration (TTS or a recording) runs at its own pace. This module aligns the
caption text to the word stream with ``difflib.SequenceMatcher`` on
normalised tokens (case, punctuation and simple number spellings ignored),
then:

* gives each cue the start of its first matched word and the end of its last;
* interpolates cues whose words were not recognised;
* reports per-cue drift (planned start minus spoken start) and whether it is
  within ``tolerance_s`` (default 0.15 s, the house sync rule).

Usage::

    from word_caption_aligner import align
    result = align(cues, words)   # cues: [{'start','end','text'}], words: [{'word','start','end'}]
    result["cues"]                 # retimed cues
    result["report"]               # {'max_abs_drift_s', 'out_of_tolerance', 'match_ratio', 'per_cue': [...]}
"""

from __future__ import annotations

import difflib
import re

_NUM_WORDS = {"zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6",
              "seven": "7", "eight": "8", "nine": "9", "ten": "10", "eleven": "11", "twelve": "12",
              "thirteen": "13", "fourteen": "14", "fifteen": "15", "twenty": "20", "hundred": "100"}


def norm(token: str) -> str:
    t = re.sub(r"[^\w%]", "", token.lower().replace("\u2019", "'"))
    t = t.replace(",", "")
    return _NUM_WORDS.get(t, t)


def align(cues: list[dict], words: list[dict], tolerance_s: float = 0.15, min_duration: float = 0.3) -> dict:
    cue_tokens: list[tuple[int, str]] = []
    for ci, c in enumerate(cues):
        for tok in c["text"].split():
            n = norm(tok)
            if n:
                cue_tokens.append((ci, n))
    word_norm = [norm(w["word"]) for w in words]
    sm = difflib.SequenceMatcher(a=[t for _, t in cue_tokens], b=word_norm, autojunk=False)
    matched: dict[int, list[int]] = {}
    total_matched = 0
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            ci = cue_tokens[a + k][0]
            matched.setdefault(ci, []).append(b + k)
            total_matched += 1
    out, per_cue = [], []
    for ci, c in enumerate(cues):
        idx = matched.get(ci)
        if idx:
            start, end = words[min(idx)]["start"], words[max(idx)]["end"]
            how = "matched"
        else:
            start, end, how = None, None, "unmatched"
        out.append({**c, "start": start, "end": end, "_how": how})
    _interpolate(out, cues)
    for c, orig in zip(out, cues):
        if c["end"] - c["start"] < min_duration:
            c["end"] = c["start"] + min_duration
    for a, b in zip(out, out[1:]):
        if a["end"] > b["start"]:
            a["end"] = max(a["start"] + 0.05, b["start"])
    for c, orig in zip(out, cues):
        drift = orig["start"] - c["start"]
        per_cue.append({"text": orig["text"], "planned_start": orig["start"], "spoken_start": round(c["start"], 3),
                        "drift_s": round(drift, 3), "ok": abs(drift) <= tolerance_s, "how": c.pop("_how")})
    drifts = [abs(p["drift_s"]) for p in per_cue] or [0.0]
    report = {
        "tolerance_s": tolerance_s,
        "max_abs_drift_s": round(max(drifts), 3),
        "mean_abs_drift_s": round(sum(drifts) / len(drifts), 3),
        "out_of_tolerance": sum(1 for p in per_cue if not p["ok"]),
        "match_ratio": round(total_matched / max(1, len(cue_tokens)), 3),
        "per_cue": per_cue,
    }
    return {"cues": out, "report": report}


def _interpolate(out: list[dict], cues: list[dict]) -> None:
    known = [i for i, c in enumerate(out) if c["start"] is not None]
    for i, c in enumerate(out):
        if c["start"] is not None:
            continue
        prev = max((k for k in known if k < i), default=None)
        nxt = min((k for k in known if k > i), default=None)
        planned = cues[i]["end"] - cues[i]["start"]
        if prev is not None and nxt is not None:
            lo, hi = out[prev]["end"], out[nxt]["start"]
            n_between = nxt - prev - 1
            pos = i - prev - 1
            span = max(0.0, hi - lo)
            c["start"] = lo + span * pos / n_between
            c["end"] = lo + span * (pos + 1) / n_between
        elif prev is not None:
            c["start"] = out[prev]["end"]
            c["end"] = c["start"] + planned
        elif nxt is not None:
            c["end"] = out[nxt]["start"]
            c["start"] = max(0.0, c["end"] - planned)
        else:
            c["start"], c["end"] = cues[i]["start"], cues[i]["end"]
