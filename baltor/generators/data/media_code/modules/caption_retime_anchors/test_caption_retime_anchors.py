import pytest

from caption_retime_anchors import apply, fit, fps_factor, map_time, shift


def test_two_anchor_exact():
    m = fit([(10.0, 10.4), (300.0, 312.9)])
    assert map_time(10.0, m) == pytest.approx(10.4)
    assert map_time(300.0, m) == pytest.approx(312.9)
    assert m["max_residual_s"] < 1e-9


def test_least_squares_residual():
    m = fit([(0, 1), (10, 11), (20, 21.5)])
    assert m["max_residual_s"] > 0.1
    assert m["scale"] == pytest.approx(1.025)


def test_apply_shift_and_clamp():
    cues = [{"start": 0.2, "end": 1.0, "text": "a"}]
    assert shift(cues, -0.5)[0]["start"] == 0.0
    assert apply(cues, {"scale": 2, "offset": 0})[0]["end"] == 2.0
    assert cues[0]["start"] == 0.2


def test_errors_and_fps():
    with pytest.raises(ValueError):
        fit([(1, 1)])
    with pytest.raises(ValueError):
        fit([(1, 1), (1, 2)])
    assert fps_factor(25, 25) == 1
    assert fps_factor(25, 24000 / 1001) == pytest.approx(1.04270833)
