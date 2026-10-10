import pytest

import cubic_bezier_timing as cb


def brute(curve, t):
    # dense parametric search, independent of the solver
    best = min((abs(curve._coord(i / 20000, curve.x1, curve.x2) - t), i / 20000) for i in range(20001))
    return curve._coord(best[1], curve.y1, curve.y2)


def test_linear_is_identity():
    lin = cb.preset("linear")
    for t in (0.1, 0.33, 0.9):
        assert lin(t) == pytest.approx(t, abs=1e-6)


@pytest.mark.parametrize("name", ["ease", "ease-in", "ease-out", "ease-in-out"])
def test_presets_match_brute_force(name):
    c = cb.preset(name)
    for t in (0.05, 0.25, 0.5, 0.75, 0.95):
        assert c(t) == pytest.approx(brute(c, t), abs=2e-4)


def test_ease_in_out_symmetric():
    assert cb.preset("ease-in-out")(0.5) == pytest.approx(0.5, abs=1e-6)


def test_overshoot_curve_exceeds_one():
    c = cb.CubicBezier(0.34, 1.56, 0.64, 1)
    assert max(cb.sample(c, 101)) > 1.0


def test_parse_css_and_errors():
    c = cb.parse_css("cubic-bezier(0.42, 0, 0.58, 1)")
    assert c == cb.preset("ease-in-out")
    assert cb.parse_css("ease") == cb.preset("ease")
    with pytest.raises(ValueError):
        cb.CubicBezier(1.2, 0, 0.5, 1)
    with pytest.raises(ValueError):
        cb.parse_css("steps(4)")
    assert c.css() == "cubic-bezier(0.42, 0, 0.58, 1)"
