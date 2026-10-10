import pytest

from ass_subtitle_parser import events_as_cues, parse, parse_time, plain_text

SAMPLE = """﻿[Script Info]
; comment
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, Alignment
Style: Caption,Inter,72,&H00FFFFFF,2

[Events]
Format: Layer, Start, End, Style, Text
Dialogue: 0,0:00:02.50,0:00:04.00,Caption,{\\fad(80,80)}Hello, world\\Nsecond line
Comment: 0,0:00:01.00,0:00:02.00,Caption,note to self
Dialogue: 1,0:00:01.00,0:00:02.00,Caption,{\\b1}Bold\\h{x}
"""


def test_parse_sections():
    doc = parse(SAMPLE)
    assert doc["info"]["PlayResY"] == 1920
    assert doc["styles"]["Caption"]["Fontsize"] == "72"
    assert len(doc["events"]) == 3
    assert doc["events"][0]["Text"].endswith("second line")


def test_cues_plain_and_sorted():
    cues = events_as_cues(parse(SAMPLE))
    assert cues == [(1.0, 2.0, "Bold "), (2.5, 4.0, "Hello, world\nsecond line")]
    assert len(events_as_cues(parse(SAMPLE), include_comments=True)) == 3


def test_plain_text_keeps_escaped_braces():
    assert plain_text("a\\{b\\}{\\i1}c") == "a{b}c"


def test_times_and_errors():
    assert parse_time("1:02:03.45") == pytest.approx(3723.45)
    with pytest.raises(ValueError):
        parse_time("12:00")
    with pytest.raises(ValueError):
        parse("[Events]\nDialogue: 0,0:00:00.00,0:00:01.00,x,y")
