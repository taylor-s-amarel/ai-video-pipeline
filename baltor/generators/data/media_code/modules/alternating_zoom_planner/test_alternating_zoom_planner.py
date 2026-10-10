import pytest

from alternating_zoom_planner import plan_moves, summary


def test_alternates_and_never_repeats():
    moves = plan_moves([3.0] * 9)
    names = [m["move"] for m in moves]
    assert names[:3] == ["zoom_in", "zoom_out", "zoom_in"]
    assert names[3] == "pan_right" and names[7] == "pan_left"
    assert summary(moves)["back_to_back_repeats"] == 0


def test_strength_scales_with_duration_and_clamps():
    short, long_ = plan_moves([1.5, 20.0], pan_every=0)
    assert short["end"][2] == pytest.approx(1.06)
    assert long_["start"][2] == pytest.approx(1.25)


def test_punch_for_very_short_shots():
    m = plan_moves([0.5, 2.0])
    assert m[0]["move"] == "punch" and m[0]["start"] == m[0]["end"]


def test_pans_stay_inside():
    m = plan_moves([5.0] * 4)[3]
    s = m["start"][2]
    for cx in (m["start"][0], m["end"][0]):
        assert 0.5 / s - 1e-9 <= cx <= 1 - 0.5 / s + 1e-9


def test_validation():
    with pytest.raises(ValueError):
        plan_moves([1.0, -1.0])
    with pytest.raises(ValueError):
        plan_moves([1.0], focus=[])
    with pytest.raises(ValueError):
        plan_moves([1.0], start_with="spin")
