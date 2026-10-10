"""Spell numbers as English words for text-to-speech.

* cardinals up to the quadrillions, negatives and decimals
  ("3.14" -> "three point one four");
* ordinals ("21st" -> "twenty-first");
* years read the way people say them ("1970" -> "nineteen seventy",
  "1905" -> "nineteen oh five", "2000" -> "two thousand",
  "2026" -> "twenty twenty-six" or "two thousand twenty-six" by style).

Usage::

    from number_to_words import cardinal, ordinal, year, decimal
    cardinal(1000)        # 'one thousand'
    ordinal(3)            # 'third'
    year(2026)            # 'twenty twenty-six'
"""

from __future__ import annotations

ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
        "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
SCALES = [(10 ** 15, "quadrillion"), (10 ** 12, "trillion"), (10 ** 9, "billion"), (10 ** 6, "million"),
          (1000, "thousand")]
ORD_IRREGULAR = {"one": "first", "two": "second", "three": "third", "five": "fifth", "eight": "eighth",
                 "nine": "ninth", "twelve": "twelfth"}


def _under_100(n: int) -> str:
    if n < 20:
        return ONES[n]
    t, o = divmod(n, 10)
    return TENS[t] + (f"-{ONES[o]}" if o else "")


def _under_1000(n: int) -> str:
    h, rest = divmod(n, 100)
    parts = []
    if h:
        parts.append(f"{ONES[h]} hundred")
    if rest:
        parts.append(_under_100(rest))
    return " ".join(parts) if parts else "zero"


def cardinal(n: int) -> str:
    n = int(n)
    if n < 0:
        return "minus " + cardinal(-n)
    if n < 1000:
        return _under_1000(n)
    if n >= 10 ** 18:
        raise ValueError("number too large")
    parts = []
    for value, name in SCALES:
        if n >= value:
            q, n = divmod(n, value)
            parts.append(f"{cardinal(q)} {name}")
    if n:
        parts.append(_under_1000(n))
    return " ".join(parts)


def ordinal(n: int) -> str:
    words = cardinal(n)
    head, sep, last = words.rpartition(" ")
    if "-" in last:
        a, b = last.rsplit("-", 1)
        last = a + "-" + _ord_word(b)
    else:
        last = _ord_word(last)
    return f"{head}{sep}{last}"


def _ord_word(w: str) -> str:
    if w in ORD_IRREGULAR:
        return ORD_IRREGULAR[w]
    if w.endswith("y"):
        return w[:-1] + "ieth"
    return w + "th"


def year(n: int, style: str = "pairs") -> str:
    """Read a year. style 'pairs' says 2026 as 'twenty twenty-six'; 'thousand' as 'two thousand twenty-six'."""
    n = int(n)
    if n < 0:
        return cardinal(-n) + " BC"
    if n < 1000 or n >= 10000:
        return cardinal(n)
    hi, lo = divmod(n, 100)
    if n % 1000 == 0 or (2000 <= n < 2010) or (style == "thousand" and 2000 <= n < 2100):
        return cardinal(n).replace(" and ", " ")
    if lo == 0:
        return f"{_under_100(hi)} hundred"
    if lo < 10:
        return f"{_under_100(hi)} oh {ONES[lo]}"
    return f"{_under_100(hi)} {_under_100(lo)}"


def decimal(text: str) -> str:
    """'3.14' -> 'three point one four'; '-0.5' -> 'minus zero point five'."""
    s = text.strip().replace(",", "")
    neg = s.startswith("-")
    s = s.lstrip("+-")
    whole, _, frac = s.partition(".")
    if not (whole or frac) or not (whole + frac).isdigit():
        raise ValueError(f"not a decimal number: {text!r}")
    out = cardinal(int(whole or "0"))
    if frac:
        out += " point " + " ".join(ONES[int(d)] for d in frac)
    return ("minus " if neg else "") + out
