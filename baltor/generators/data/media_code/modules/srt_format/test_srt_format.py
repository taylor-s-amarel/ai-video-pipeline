import pytest

from srt_format import Cue, dumps, format_time, parse, validate

MESSY = "﻿1\r\n00:00:01,000 --> 00:00:02.5\r\nHello\r\nworld\r\n\r\n\r\n7\r\n00:00:03,250 --> 00:00:04,000\r\nSecond"


def test_parse_messy():
    cues = parse(MESSY)
    assert len(cues) == 2
    assert cues[0] == Cue(1.0, 2.5, "Hello\nworld")
    assert cues[1].start == pytest.approx(3.25) and cues[1].text == "Second"


def test_roundtrip():
    cues = [Cue(0, 1.234, "A"), Cue(3661.5, 3662.0, "B\nC")]
    text = dumps(cues)
    assert text.startswith("1\n00:00:00,000 --> 00:00:01,234\nA\n")
    assert "01:01:01,500" in text
    assert parse(text) == cues


def test_back_to_back_without_blank_line():
    text = "1\n00:00:01,000 --> 00:00:02,000\nOne\n2\n00:00:02,000 --> 00:00:03,000\nTwo\n"
    assert [c.text for c in parse(text)] == ["One", "Two"]


def test_validate():
    probs = validate([Cue(0, 1, "a"), Cue(0.5, 0.6, ""), Cue(2, 1, "x")])
    assert any("overlap" in p for p in probs)
    assert any("empty" in p for p in probs)
    assert any("not after" in p for p in probs)
    with pytest.raises(ValueError):
        format_time(-1)
