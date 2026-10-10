import pytest

from lrc_lyrics_format import dumps, fmt, line_at, parse

TEXT = """[ti:Demo]
[ar:Someone]
[offset:+500]
[00:12.00][01:02.50]Chorus line
[00:05.20]<00:05.20>First <00:05.80>words <00:06.10>here
"""


def test_parse_meta_offset_and_repeats():
    doc = parse(TEXT)
    assert doc["meta"]["ti"] == "Demo"
    times = [round(t, 2) for t, _, _ in doc["lines"]]
    assert times == [4.7, 11.5, 62.0]
    assert doc["lines"][0][1] == "First words here"
    assert doc["lines"][0][2][1] == (pytest.approx(5.3), "words")


def test_no_offset():
    assert parse(TEXT, apply_offset=False)["lines"][0][0] == pytest.approx(5.2)


def test_roundtrip_and_line_at():
    doc = parse(dumps([(1.0, "a"), (2.5, "b", [(2.5, "b")])], meta={"ti": "x"}))
    assert [l[1] for l in doc["lines"]] == ["a", "b"]
    assert line_at(doc, 2.0) == "a" and line_at(doc, 0.5) == ""
    assert fmt(65.25) == "01:05.25"
    with pytest.raises(ValueError):
        fmt(-1)
