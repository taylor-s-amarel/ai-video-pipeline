import pytest

from scene_duration_planner import plan


def test_equal_split_and_exact_total():
    p = plan(4, total=64)
    assert [s["label"] for s in p] == ["HOOK", "FACT 1", "FACT 2", "FACT 3", "FACT 4", "OUTRO"]
    assert p[-1]["end_s"] == 64 and p[1]["duration_s"] == pytest.approx(14)
    assert all(a["end_s"] == b["start_s"] for a, b in zip(p, p[1:]))


def test_weights_and_clamping():
    p = plan(3, total=60, weights=[1, 1, 20], min_item=8, max_item=30)
    d = [s["duration_s"] for s in p[1:4]]
    assert d[2] == pytest.approx(30, abs=0.05) and min(d) >= 8 - 1e-6
    assert sum(d) == pytest.approx(52, abs=0.05)


def test_frame_rounding():
    p = plan(3, total=61.7, fps=30)
    for s in p[:-1]:
        assert abs(s["end_s"] * 30 - round(s["end_s"] * 30)) < 1e-6


def test_errors():
    with pytest.raises(ValueError):
        plan(4, total=30)
    with pytest.raises(ValueError):
        plan(10, total=60)
    with pytest.raises(ValueError):
        plan(1, total=90, max_item=20)
    with pytest.raises(ValueError):
        plan(2, weights=[1])
