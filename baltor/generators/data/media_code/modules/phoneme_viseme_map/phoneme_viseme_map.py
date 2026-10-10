"""ARPAbet phonemes to mouth shapes (visemes) for lip-sync animation.

The target shapes are the nine letters used by Rhubarb Lip Sync
(https://github.com/DanielSWolf/rhubarb-lip-sync): A closed (P B M),
B slightly open / teeth (most consonants, EE), C open (EH, AE), D wide (AA),
E slightly rounded (AO, ER), F puckered (UW, OW, W), G teeth on lip (F V),
H tongue up (L), X rest. The phoneme-to-letter table below is this module's
own mapping built from those shape descriptions; adjust it per character.

``visemes_from_phones`` turns timed phones (for example from a forced
aligner) into mouth cues, merging cues shorter than ``min_s`` so the mouth
does not flicker faster than the frame rate.

Usage::

    from phoneme_viseme_map import viseme, visemes_from_phones
    viseme("AA1")                        # 'D' (stress digits are ignored)
    visemes_from_phones([(0.0, 0.08, "HH"), (0.08, 0.2, "AH0"), (0.2, 0.3, "L")])
"""

from __future__ import annotations

MAP = {
    "P": "A", "B": "A", "M": "A",
    "F": "G", "V": "G",
    "L": "H",
    "UW": "F", "OW": "F", "W": "F", "UH": "F", "OY": "F",
    "AO": "E", "ER": "E", "R": "E",
    "AA": "D", "AW": "D", "AY": "D",
    "EH": "C", "AE": "C", "AH": "C", "EY": "C", "HH": "C",
    "IY": "B", "IH": "B", "Y": "B", "K": "B", "G": "B", "NG": "B", "T": "B", "D": "B", "N": "B",
    "S": "B", "Z": "B", "SH": "B", "ZH": "B", "CH": "B", "JH": "B", "TH": "B", "DH": "B",
    "SIL": "X", "SP": "X", "": "X",
}
SHAPES = "ABCDEFGHX"


def viseme(phone: str) -> str:
    p = phone.strip().upper().rstrip("012")
    if p not in MAP:
        raise KeyError(f"unknown ARPAbet phone {phone!r}")
    return MAP[p]


def visemes_from_phones(phones, min_s: float = 0.04, rest_gap_s: float = 0.15) -> list[tuple[float, float, str]]:
    """``phones``: iterable of (start, end, phone). Returns merged (start, end, letter) cues.

    Gaps longer than ``rest_gap_s`` become rest (X); shorter gaps extend the previous cue.
    """
    cues: list[list] = []
    last_end = 0.0
    for start, end, ph in sorted(phones):
        if end <= start:
            raise ValueError(f"phone {ph!r} has end <= start")
        if start - last_end > rest_gap_s:
            cues.append([last_end, start, "X"])
        elif cues and start > last_end:
            cues[-1][1] = start
        letter = viseme(ph)
        if cues and cues[-1][2] == letter and abs(cues[-1][1] - start) < 1e-9:
            cues[-1][1] = end
        else:
            cues.append([start, end, letter])
        last_end = end
    merged: list[list] = []
    for c in cues:
        if merged and (c[1] - c[0] < min_s):
            merged[-1][1] = c[1]
        elif merged and merged[-1][2] == c[2]:
            merged[-1][1] = c[1]
        else:
            merged.append(c)
    return [(round(a, 6), round(b, 6), s) for a, b, s in merged]


def letter_at(cues, t: float) -> str:
    for a, b, s in cues:
        if a <= t < b:
            return s
    return "X"
