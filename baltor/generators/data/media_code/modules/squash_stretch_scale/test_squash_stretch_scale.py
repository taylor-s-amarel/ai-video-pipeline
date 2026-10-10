import pytest

from squash_stretch_scale import bounce_track, impact_squash, stretch_from_velocity


def test_volume_preserved():
    s, c, a = stretch_from_velocity(300, 400, k=0.001)
    assert s * c == pytest.approx(1)
    assert a == pytest.approx(53.13, abs=0.01)
    sx, sy = impact_squash(0.0, 0.3)
    assert sx * sy == pytest.approx(1) and sy < 1


def test_stretch_capped_and_rest():
    assert stretch_from_velocity(0, 1e9, max_stretch=1.4)[0] == 1.4
    assert stretch_from_velocity(0, 0) == (1.0, 1.0, 0.0)


def test_squash_recovers():
    assert impact_squash(0.2) == (1.0, 1.0)


def test_bounce_track():
    tr = bounce_track(400, bounces=2, fps=60)
    assert tr[0]["y"] < 400 and min(f["y"] for f in tr) == 0
    assert all(f["sx"] * f["sy"] == pytest.approx(1) for f in tr)
    with pytest.raises(ValueError):
        bounce_track(100, restitution=1.5)
