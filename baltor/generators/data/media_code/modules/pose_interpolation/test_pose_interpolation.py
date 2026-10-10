import pytest

from pose_interpolation import blend, bob_offsets, cycle, shortest_delta, walk_cycle


def test_shortest_arc():
    assert shortest_delta(170, -170) == pytest.approx(20)
    assert shortest_delta(-170, 170) == pytest.approx(-20)
    assert blend({"a": 170}, {"a": -170}, 0.5)["a"] == pytest.approx(180)


def test_blend_missing_joints_default_zero():
    out = blend({"x": 10}, {"y": 20}, 0.5)
    assert out == {"x": 5, "y": 10}


def test_cycle_loops_back():
    a, b = {"j": 0.0}, {"j": 90.0}
    fr = cycle([a, b], fps=10, seconds_per_pose=0.5, loops=2)
    assert len(fr) == 20 and fr[0]["j"] == 0 and fr[10]["j"] == 0
    assert 80 < max(f["j"] for f in fr) <= 90
    with pytest.raises(ValueError):
        cycle([a], 10, 1)


def test_walk_cycle_periodic_and_symmetric():
    g = walk_cycle(fps=30, steps_per_second=2, seconds=2)
    assert len(g) == 60
    assert g[0]["l_knee"] == pytest.approx(g[30]["l_knee"], abs=1e-9)
    assert g[7]["l_knee"] == pytest.approx(-g[7]["r_knee"])
    b = bob_offsets(30, 2, 1)
    assert min(b) == pytest.approx(-6) and max(b) <= 0
