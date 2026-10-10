import pytest

from caption_reading_speed import analyse, cps, extend_to_readable, wpm


def test_rates():
    assert cps("hello world", 1.0) == 11
    assert wpm("one two three", 1.5) == pytest.approx(120)
    assert cps("x", 0) == float("inf")


def test_analyse_flags():
    cues = [{"start": 0, "end": 0.5, "text": "This is far too much text for half a second"},
            {"start": 1, "end": 3, "text": "Fine"}, {"start": 3, "end": 12, "text": "Lingers"}]
    rep = analyse(cues)
    assert rep["failing"] == 2
    assert rep["cues"][0]["issues"] and not rep["cues"][1]["issues"]
    assert "> 7s" in rep["cues"][2]["issues"][0]


def test_extend_respects_next_cue():
    cues = [{"start": 0, "end": 0.5, "text": "x" * 40}, {"start": 1.0, "end": 2.0, "text": "ok"}]
    out = extend_to_readable(cues, max_cps=20, min_gap=0.1)
    assert out[0]["end"] == pytest.approx(0.9)
    out2 = extend_to_readable([{"start": 0, "end": 0.5, "text": "x" * 40}])
    assert out2[0]["end"] == pytest.approx(2.0)
    assert cues[0]["end"] == 0.5  # input untouched
