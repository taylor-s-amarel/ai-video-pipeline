import pytest

from sbv_format import dumps, format_time, parse


def test_roundtrip():
    cues = [(0.0, 1.5, "Hello"), (3601.25, 3603.0, "Two\nlines")]
    text = dumps(cues)
    assert text.startswith("0:00:00.000,0:00:01.500\nHello\n")
    assert "1:00:01.250,1:00:03.000" in text
    assert parse(text) == cues


def test_crlf_and_bom():
    assert parse("﻿0:00:01.000,0:00:02.000\r\nHi\r\n") == [(1.0, 2.0, "Hi")]


def test_errors():
    with pytest.raises(ValueError):
        dumps([(2, 1, "x")])
    with pytest.raises(ValueError):
        format_time(-0.1)
