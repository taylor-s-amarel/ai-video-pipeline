import pytest

from narration_timing_planner import duration_for, plan_segments, word_count, words_for, wpm_needed

TEXT = " ".join(["word"] * 150)


def test_basic_rates():
    assert word_count("It's 14 days, $2.5M.") == 4
    assert duration_for(TEXT, 150) == pytest.approx(60.0)
    assert duration_for(TEXT + ".", 150) == pytest.approx(60.3)
    assert wpm_needed(TEXT, 60) == pytest.approx(150)
    assert words_for(64, 150) == 160


def test_plan_advice_short_and_long():
    short = plan_segments([{"label": "HOOK", "text": " ".join(["w"] * 50)}], wpm=150)
    assert not short["ok"] and "add about" in short["advice"][0]
    long_ = plan_segments([{"text": " ".join(["w"] * 300)}], wpm=150)
    assert "cut about" in long_["advice"][0]


def test_plan_ok_and_offsets():
    segs = [{"label": "HOOK", "text": " ".join(["w"] * 40)}, {"label": "FACT 1", "text": " ".join(["w"] * 120)}]
    p = plan_segments(segs, wpm=150)
    assert p["ok"] and p["segments"][1]["start"] == pytest.approx(16.6)
    assert not plan_segments(segs, wpm=190)["ok"]


def test_errors():
    with pytest.raises(ValueError):
        duration_for("x", 0)
    with pytest.raises(ValueError):
        wpm_needed("a. b. c.", 0.5)
