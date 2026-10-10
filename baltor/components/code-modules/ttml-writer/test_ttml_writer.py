import xml.etree.ElementTree as ET

import pytest

from ttml_writer import clock, dumps, parse_time, read


def test_roundtrip_with_escaping_and_breaks():
    cues = [(1.0, 2.5, "Hello & <welcome>"), (2.6, 4.0, "Line one\nLine two")]
    xml = dumps(cues)
    ET.fromstring(xml.encode())  # well-formed
    assert "&amp;" in xml and "&lt;welcome&gt;" in xml
    assert read(xml) == cues


def test_times():
    assert clock(3723.5) == "01:02:03.500"
    assert parse_time("12.5s") == 12.5 and parse_time("1.5m") == 90
    assert parse_time("00:00:01.25") == 1.25
    with pytest.raises(ValueError):
        parse_time("10f")


def test_validation():
    with pytest.raises(ValueError):
        dumps([(2, 1, "x")])
