import pytest

from ass_karaoke_tags import durations, karaoke_text

WORDS = [{"word": "FIVE", "start": 1.2, "end": 1.5}, {"word": "SCIENTISTS", "start": 1.55, "end": 2.1},
         {"word": "{LIVED}", "start": 2.2, "end": 2.6}]


def test_tags_and_total():
    t = karaoke_text(WORDS, cue_start=1.0, cue_end=3.0)
    assert t.startswith("{\\k20}{\\kf35}FIVE {\\kf65}SCIENTISTS {\\kf80}\\{LIVED\\}")
    assert sum(durations(t)) == 200


def test_no_drift_with_awkward_times():
    words = [{"word": str(i), "start": 0.333 * i, "end": 0.333 * i + 0.2} for i in range(30)]
    t = karaoke_text(words, cue_start=0.0, cue_end=10.0, mode="k")
    assert sum(durations(t)) == 1000


def test_errors():
    with pytest.raises(ValueError):
        karaoke_text(WORDS, cue_start=1.5)
    with pytest.raises(ValueError):
        karaoke_text(WORDS, 1.0, mode="x")
    assert karaoke_text([], 0) == ""
