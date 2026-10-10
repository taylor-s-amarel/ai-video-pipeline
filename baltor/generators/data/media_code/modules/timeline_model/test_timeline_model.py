import pytest

from timeline_model import Clip, Timeline


def make():
    tl = Timeline(fps=30)
    tl.add("bg", Clip("waves.mp4", 0, 30, start=0, source_duration=120))
    tl.add("bg", Clip("waves.mp4", 30, 64, start=30, source_duration=120))
    tl.add("photo", Clip("p1.jpg", 0, 16, start=0))
    tl.add("photo", Clip("p2.jpg", 0, 16, start=16))
    return tl


def test_duration_and_at():
    tl = make()
    assert tl.duration == 64
    active = tl.at(17.0)
    assert active["photo"].source == "p2.jpg" and active["bg"].in_s == 0


def test_problems():
    tl = make()
    assert tl.problems(continuous=("bg",)) == []
    tl.add("photo", Clip("p3.jpg", 0, 5, start=30, opacity=1.0))
    tl.add("bg", Clip("waves.mp4", 100, 130, start=70, source_duration=120))
    probs = " | ".join(tl.problems(continuous=("bg",)))
    assert "gap of 6.000s" in probs and "past its 120" in probs and "opacity 1.0" in probs
    tl.add("photo", Clip("p4.jpg", 0, 5, start=31))
    assert any("overlaps" in p for p in tl.problems())


def test_json_roundtrip_and_validation():
    tl = make()
    back = Timeline.from_json(tl.to_json())
    assert back.duration == tl.duration and len(back.tracks["photo"]) == 2
    with pytest.raises(ValueError):
        tl.add("x", Clip("a", 2, 1, 0))
