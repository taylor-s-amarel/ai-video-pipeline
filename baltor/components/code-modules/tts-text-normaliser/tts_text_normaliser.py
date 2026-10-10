"""Normalise narration text so TTS engines read numbers and symbols correctly.

Neural TTS voices often misread "$2.5M", "86%", "1,000", "3:30 pm",
"21st", "10-20 km" or "Dr." This module rewrites them into words before
synthesis (captions keep the original digits):

* money: $, GBP and EUR signs with k/M/B suffixes and decimals;
* percentages, ranges ("10-20" -> "ten to twenty"), ordinals, decimals,
  comma-grouped numbers, plain integers;
* years: four-digit numbers from 1100 to 2099 not followed by a unit are
  read as years;
* clock times ("3:30 pm", "14:05");
* common abbreviations and units (Dr., Mr., Mrs., vs., e.g., i.e., km, kg,
  mph, degrees F/C) and symbols (&, +, @).

Usage::

    from tts_text_normaliser import normalise
    normalise("In 1970, 5 scientists spent 14 days 50 ft down; cost: $2.5M (86%).")
"""

from __future__ import annotations

import re

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
        "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
SCALES = [(10 ** 12, "trillion"), (10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")]


def _u100(n):
    return ONES[n] if n < 20 else TENS[n // 10] + (f"-{ONES[n % 10]}" if n % 10 else "")


def _u1000(n):
    h, r = divmod(n, 100)
    return " ".join(p for p in ([f"{ONES[h]} hundred"] if h else []) + ([_u100(r)] if r else [])) or "zero"


def cardinal(n: int) -> str:
    if n < 0:
        return "minus " + cardinal(-n)
    if n < 1000:
        return _u1000(n)
    parts = []
    for v, name in SCALES:
        if n >= v:
            q, n = divmod(n, v)
            parts.append(f"{cardinal(q)} {name}")
    if n:
        parts.append(_u1000(n))
    return " ".join(parts)


def ordinal(n: int) -> str:
    w = cardinal(n)
    irregular = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth",
                 "nine": "ninth", "twelve": "twelfth"}
    head, sep, last = w.rpartition(" ")
    pre, dash, core = last.rpartition("-")
    core = irregular.get(core, core[:-1] + "ieth" if core.endswith("y") else core + "th")
    return f"{head}{sep}{pre}{dash}{core}"


def year(n: int) -> str:
    hi, lo = divmod(n, 100)
    if n % 1000 == 0 or 2000 <= n < 2010:
        return cardinal(n)
    if lo == 0:
        return f"{_u100(hi)} hundred"
    return f"{_u100(hi)} oh {ONES[lo]}" if lo < 10 else f"{_u100(hi)} {_u100(lo)}"


def number(text: str) -> str:
    s = text.replace(",", "")
    whole, _, frac = s.partition(".")
    out = cardinal(int(whole or "0"))
    if frac:
        out += " point " + " ".join(ONES[int(d)] for d in frac)
    return out


ABBREV = [(r"\bDr\.", "Doctor"), (r"\bMr\.", "Mister"), (r"\bMrs\.", "Missus"), (r"\bMs\.", "Miz"),
          (r"\bvs\.?", "versus"), (r"\be\.g\.", "for example"), (r"\bi\.e\.", "that is"), (r"\betc\.", "et cetera"),
          (r"\bapprox\.", "approximately"), (r"&", " and "), (r"\s\+\s", " plus "), (r"@", " at ")]
UNITS = {"km": "kilometers", "kg": "kilograms", "mph": "miles per hour", "kph": "kilometers per hour",
         "ft": "feet", "m": "meters", "cm": "centimeters", "mm": "millimeters", "lb": "pounds", "lbs": "pounds",
         "mi": "miles", "g": "grams", "ms": "milliseconds", "hrs": "hours", "min": "minutes"}
CURRENCY = {"$": "dollars", "£": "pounds", "€": "euros"}
SUFFIX = {"k": "thousand", "K": "thousand", "m": "million", "M": "million", "b": "billion", "B": "billion",
          "bn": "billion"}
NUM = r"\d[\d,]*(?:\.\d+)?"


def normalise(text: str) -> str:
    t = text
    for pat, rep in ABBREV:
        t = re.sub(pat, rep, t)

    def money(m):
        sym, amount, suf = m.group(1), m.group(2), m.group(3)
        words = number(amount)
        if suf:
            words += " " + SUFFIX[suf]
        return f"{words} {CURRENCY[sym]}"
    t = re.sub(rf"([$£€])({NUM})(bn|[kKmMbB])?\b", money, t)

    def clock(m):
        h, mi, ampm = int(m.group(1)), int(m.group(2)), (m.group(3) or "").lower().replace(".", "")
        mins = "o'clock" if mi == 0 and ampm else ("" if mi == 0 else (f"oh {ONES[mi]}" if mi < 10 else _u100(mi)))
        if not ampm and mi == 0:
            mins = "hundred"
        return " ".join(p for p in (cardinal(h), mins, " ".join(ampm.upper()) if ampm else "") if p)
    t = re.sub(r"\b(\d{1,2}):(\d{2})\s*([ap]\.?m\.?)?(?!\w)", clock, t, flags=re.I)
    t = re.sub(rf"({NUM})\s?%", lambda m: f"{number(m.group(1))} percent", t)
    t = re.sub(r"(-?\d+)\s?°\s?([FC])\b",
               lambda m: f"{number(m.group(1).lstrip('-'))}{' below zero' if m.group(1).startswith('-') else ''} degrees "
                         f"{'Fahrenheit' if m.group(2) == 'F' else 'Celsius'}", t)
    t = re.sub(r"\b(\d+)(st|nd|rd|th)\b", lambda m: ordinal(int(m.group(1))), t)
    # units first (digits kept) so "10-20 km" becomes "10-20 kilometers" before the range rule
    t = re.sub(rf"\b({NUM})\s?({'|'.join(sorted(UNITS, key=len, reverse=True))})\b",
               lambda m: f"{m.group(1)} {UNITS[m.group(2)]}", t)
    t = re.sub(rf"\b({NUM})\s?[-–]\s?({NUM})\b", lambda m: f"{number(m.group(1))} to {number(m.group(2))}", t)
    not_year = "|".join(sorted(set(UNITS.values()) | {"people", "dogs", "years", "times"}))
    t = re.sub(rf"\b(1[1-9]\d\d|20\d\d)\b(?!\s?(?:{not_year}))",
               lambda m: year(int(m.group(1))), t)
    t = re.sub(NUM, lambda m: number(m.group(0)), t)
    t = re.sub(r"\s{2,}", " ", t)
    return t.strip()
