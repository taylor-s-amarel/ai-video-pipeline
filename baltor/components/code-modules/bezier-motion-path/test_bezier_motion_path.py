import math

import pytest

from bezier_motion_path import BezierPath, smooth_through


def test_straight_line_length_and_midpoint():
    p = BezierPath([((0, 0), (10, 0), (20, 0), (30, 0))])
    assert p.length == pytest.approx(30, rel=1e-6)
    assert p.point_at(0.5)[0] == pytest.approx(15, abs=1e-3)


def test_uneven_controls_still_constant_speed():
    # controls bunched at the start: raw t would crawl, arc-length must not
    p = BezierPath([((0, 0), (1, 0), (2, 0), (100, 0))])
    xs = [pt[0] for pt in p.sample(11)]
    steps = [b - a for a, b in zip(xs, xs[1:])]
    assert max(steps) - min(steps) < 0.5


def test_even_spacing_on_curve():
    p = BezierPath([((0, 0), (300, -200), (700, 200), (1000, 0))])
    pts = p.sample(41)
    d = [math.dist(a, b) for a, b in zip(pts, pts[1:])]
    assert max(d) / min(d) < 1.02


def test_angle_and_multi_segment():
    segs = smooth_through([(0, 0), (100, 0), (100, 100)])
    p = BezierPath(segs)
    assert p.point_at(0) == pytest.approx((0, 0))
    assert p.point_at(1) == pytest.approx((100, 100))
    assert p.angle_at(0.01) == pytest.approx(0, abs=20)
    assert p.angle_at(0.99) == pytest.approx(90, abs=20)


def test_validation():
    with pytest.raises(ValueError):
        BezierPath([])
    with pytest.raises(ValueError):
        BezierPath([((0, 0), (1, 1), (2, 2), (3, 3)), ((9, 9), (1, 1), (2, 2), (3, 3))])
