import math

import pytest

from two_bone_ik import chain_points, solve


@pytest.mark.parametrize("target", [(60, 80), (-30, 40), (100, 0), (10, -5)])
@pytest.mark.parametrize("bend", [1, -1])
def test_reaches_and_preserves_lengths(target, bend):
    s = solve((0, 0), target, 60, 55, bend)
    assert s["reached"]
    assert s["end"] == pytest.approx(target, abs=1e-6)
    assert math.dist((0, 0), s["joint"]) == pytest.approx(60)
    assert math.dist(s["joint"], s["end"]) == pytest.approx(55)


def test_bend_direction_mirrors():
    a = solve((0, 0), (80, 0), 50, 50, 1)["joint"]
    b = solve((0, 0), (80, 0), 50, 50, -1)["joint"]
    assert a[0] == pytest.approx(b[0]) and a[1] == pytest.approx(-b[1])


def test_unreachable_points_at_target():
    s = solve((0, 0), (300, 0), 50, 40)
    assert not s["reached"]
    assert s["end"] == pytest.approx((90, 0))
    pts = chain_points((0, 0), s)
    assert len(pts) == 3


def test_validation():
    with pytest.raises(ValueError):
        solve((0, 0), (1, 1), 0, 1)
    with pytest.raises(ValueError):
        solve((0, 0), (1, 1), 1, 1, bend=0)
