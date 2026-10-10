import pytest

import seamless_loop_motion as sl


def test_all_motions_loop():
    assert sl.check_loop(lambda t: sl.orbit(t, 8, ratio=(2, 3)), 8)
    assert sl.check_loop(lambda t: sl.breathe(t, 5), 5)
    assert sl.check_loop(lambda t: sl.drift_wrap(t, 4, 256, cycles=2), 4, tol=1e-6)
    assert sl.check_loop(lambda t: sl.loop_noise(t, 6, seed=3), 6)


def test_non_looping_detected():
    assert not sl.check_loop(lambda t: t * 0.1, 4)


def test_noise_range_and_smoothness():
    vals = [sl.loop_noise(i / 100, 6) for i in range(600)]
    assert -1 <= min(vals) and max(vals) <= 1
    assert max(abs(b - a) for a, b in zip(vals, vals[1:])) < 0.05


def test_validation_and_frames():
    with pytest.raises(ValueError):
        sl.orbit(0, 8, ratio=(1.5, 1))
    with pytest.raises(ValueError):
        sl.loop_frame_count(4.01, 30)
    assert sl.loop_frame_count(8, 30) == 240
    assert sl.breathe(0, 5) == 1.0 and sl.breathe(2.5, 5) == pytest.approx(1.06)
