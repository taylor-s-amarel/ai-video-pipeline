import pytest

from shot_list_planner import pacing, plan_shots

BEATS = [{"text": "In 1970, five scientists lived underwater.", "duration": 7.0, "asset": "habitat.jpg"},
         {"text": "Fifty feet down.", "duration": 2.0, "asset": "reef.mp4", "emphasis": True},
         {"text": "For fourteen days.", "duration": 1.0}]


def test_splits_long_beats_and_keeps_time():
    shots = plan_shots(BEATS, max_shot_s=3.0)
    assert [s["beat"] for s in shots] == [0, 0, 0, 1, 2]
    assert shots[-1]["end"] == pytest.approx(10.0)
    assert all(a["end"] == pytest.approx(b["start"]) for a, b in zip(shots, shots[1:]))
    assert max(s["duration"] for s in shots) <= 3.0


def test_moves_alternate_and_emphasis():
    shots = plan_shots(BEATS)
    assert shots[3]["move"] == "punch_in"
    assert all(a["move"] != b["move"] for a, b in zip(shots, shots[1:]))
    assert shots[0]["text"] and not shots[1]["text"]


def test_pacing_and_validation():
    p = pacing(plan_shots(BEATS))
    assert p["shots"] == 5 and p["cuts_per_minute"] == 30.0
    with pytest.raises(ValueError):
        plan_shots([{"duration": 0}])
    with pytest.raises(ValueError):
        plan_shots(BEATS, max_shot_s=0.5, min_shot_s=1.0)
