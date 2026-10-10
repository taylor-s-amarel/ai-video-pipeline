import pytest

from broll_keyword_matcher import assign, tokens

ASSETS = {"ocean_waves.mp4": "ocean waves sea surface blue water", "reef.mp4": "coral reef fish diver underwater",
          "habitat.mp4": "steel underwater habitat lab scientists", "city.mp4": "city traffic night lights"}


def test_tokens():
    assert tokens("The scientists studied reefs and fishes") == ["scientist", "studied", "reef", "fish"]


def test_assign_matches_and_flags_missing():
    sents = ["Five scientists lived in a steel habitat", "They dove the coral reef every day",
             "Waves crashed on the ocean surface", "Their budget was approved by Congress"]
    r = assign(sents, ASSETS)
    assert [x["asset"] for x in r[:3]] == ["habitat.mp4", "reef.mp4", "ocean_waves.mp4"]
    assert r[3]["asset"] is None


def test_no_repeat():
    sents = ["coral reef fish", "coral reef diver", "coral reef again"]
    r = assign(sents, ASSETS, no_repeat=1, min_score=0.0)
    assert r[0]["asset"] != r[1]["asset"]
    with pytest.raises(ValueError):
        assign(["x"], {})
