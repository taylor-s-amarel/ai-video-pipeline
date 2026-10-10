import os

import pytest

from caption_line_balancer import balance, fits, text_width

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def test_single_line_when_it_fits():
    assert balance("short line", 1000) == ["short line"]


def test_balanced_split_proxy():
    lines = balance("five scientists lived underwater for fourteen days", max_width=1000, font_size=64)
    assert len(lines) == 2
    assert fits(lines, 1000)
    assert " ".join(lines) == "five scientists lived underwater for fourteen days"
    assert not lines[0].split()[-1] in {"for", "the"}


def test_prefers_punctuation():
    assert balance("Grace Hopper, a Navy officer", max_width=600, font_size=64) == ["Grace Hopper,", "a Navy officer"]


@pytest.mark.skipif(not os.path.exists(FONT), reason="font missing")
def test_real_font_measurement():
    assert text_width("WWWW", FONT, 50) > text_width("iiii", FONT, 50)
    lines = balance("THE MISSING YELLOW BOX WAS NEVER FOUND", 900, FONT, 60)
    assert len(lines) == 2 and fits(lines, 900, FONT, 60)


def test_too_long_raises():
    with pytest.raises(ValueError):
        balance("supercalifragilisticexpialidocious " * 3, 300)
