"""Break a caption into one or two lines of balanced rendered width.

Width is measured with a real font through Pillow when a font path is given
(otherwise a character-count proxy), so balancing reflects how the text will
actually look. Among break points that fit ``max_width``, the chosen one
minimises the width difference between lines, with penalties for breaking
after a function word or between a number and its unit and a bonus for
breaking after punctuation. A bottom-heavy shape (longer second line) is
preferred on ties, a common subtitle convention.

Usage::

    from caption_line_balancer import balance, text_width
    balance("five scientists lived underwater for fourteen days", max_width=900,
            font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size=64)
    # -> ['five scientists lived', 'underwater for fourteen days']
"""

from __future__ import annotations

import re
from functools import lru_cache

FUNCTION_WORDS = {"a", "an", "the", "of", "to", "and", "or", "in", "on", "at", "by", "for", "with", "from",
                  "my", "your", "his", "her", "its", "our", "their", "is", "was", "are", "were", "that"}


@lru_cache(maxsize=16)
def _font(path: str, size: int):
    from PIL import ImageFont
    return ImageFont.truetype(path, size)


def text_width(text: str, font_path: str | None = None, font_size: int = 64) -> float:
    if font_path:
        return float(_font(font_path, font_size).getlength(text))
    return len(text) * font_size * 0.55


def balance(text: str, max_width: float, font_path: str | None = None, font_size: int = 64,
            max_lines: int = 2) -> list[str]:
    words = text.split()
    if not words:
        return []
    full = text_width(" ".join(words), font_path, font_size)
    if full <= max_width or max_lines == 1 or len(words) == 1:
        return [" ".join(words)]
    best, best_cost = None, float("inf")
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        wa, wb = text_width(a, font_path, font_size), text_width(b, font_path, font_size)
        if max(wa, wb) > max_width:
            continue
        cost = abs(wa - wb) / max_width
        last = re.sub(r"[^\w']", "", words[i - 1]).lower()
        if re.search(r"[.,;:!?]$", words[i - 1]):
            cost -= 0.15
        elif last in FUNCTION_WORDS:
            cost += 0.3
        if re.fullmatch(r"[\d,.$%]+", words[i - 1]):
            cost += 0.3
        if wa > wb:
            cost += 0.01  # tie-break toward a longer bottom line
        if cost < best_cost:
            best, best_cost = [a, b], cost
    if best is None:
        raise ValueError("text does not fit in two lines at this width; shorten the caption or the font")
    return best


def fits(lines: list[str], max_width: float, font_path: str | None = None, font_size: int = 64) -> bool:
    return all(text_width(line, font_path, font_size) <= max_width for line in lines)
