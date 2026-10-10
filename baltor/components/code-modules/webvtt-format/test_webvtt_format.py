import pytest

from webvtt_format import Cue, dumps, format_time, parse


def test_roundtrip_with_escaping_and_settings():
    cues = [Cue(1.0, 2.0, "Fish & <chips>", "c1", {"line": "80%", "align": "center"}),
            Cue(3725.5, 3726.0, "Two\nlines")]
    text = dumps(cues, header_note="made by test")
    assert "Fish &amp; &lt;chips&gt;" in text
    assert "00:00:01.000 --> 00:00:02.000 line:80% align:center" in text
    back = parse(text)
    assert back == cues


def test_parse_short_timestamps_tags_and_notes():
    text = ("WEBVTT\n\nNOTE comment\n\nSTYLE\n::cue { color: yellow }\n\n"
            "00:01.500 --> 00:02.000\n<c.yellow>Hi</c> <00:00:01.700>there\n")
    cues = parse(text)
    assert len(cues) == 1
    assert cues[0].start == 1.5 and cues[0].text == "Hi there"
    assert parse(text, strip_tags=False)[0].text.startswith("<c.yellow>")


def test_errors():
    with pytest.raises(ValueError):
        parse("1\n00:00:01,000 --> 00:00:02,000\nnot vtt")
    with pytest.raises(ValueError):
        dumps([Cue(0, 1, "x", settings={"colour": "red"})])
    with pytest.raises(ValueError):
        dumps([Cue(0, 1, "a\n\nb")])
    assert format_time(59.9995) == "00:01:00.000"
