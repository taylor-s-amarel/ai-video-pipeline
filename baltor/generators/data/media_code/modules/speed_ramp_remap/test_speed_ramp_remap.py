import pytest

from speed_ramp_remap import SpeedRamp, setpts_for_speed


def test_constant_speed():
    r = SpeedRamp([(0, 2.0)])
    assert r.source_time(3) == pytest.approx(6)
    assert r.output_duration_for(10) == pytest.approx(5, abs=1e-5)


def test_ramp_integral():
    r = SpeedRamp([(0, 1.0), (1.0, 0.0001), (2.0, 1.0)])
    # triangle-ish: integral over [0,1] of linear 1 -> ~0 is ~0.5
    assert r.source_time(1.0) == pytest.approx(0.50005)
    assert r.source_time(2.0) == pytest.approx(1.0001)


def test_monotonic_frame_map():
    r = SpeedRamp([(0, 1.0), (1.0, 0.25), (2.0, 0.25), (2.5, 1.0)])
    fm = r.frame_map(30, 4)
    assert fm == sorted(fm) and fm[0] == 0
    # slow-motion section repeats source frames
    assert len(set(fm[30:60])) < 30


def test_validation():
    with pytest.raises(ValueError):
        SpeedRamp([(1, 1.0)])
    with pytest.raises(ValueError):
        SpeedRamp([(0, 0)])
    assert setpts_for_speed(2) == "setpts=PTS/2"
