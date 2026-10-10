import math

import pytest

import easing_functions as ef


@pytest.mark.parametrize("name", sorted(ef.EASINGS))
def test_endpoints(name):
    f = ef.EASINGS[name]
    assert f(0.0) == pytest.approx(0.0, abs=1e-9)
    assert f(1.0) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("name", [n for n in ef.EASINGS if n not in ef.OVERSHOOTING and "bounce" not in n])
def test_monotonic_without_overshoot(name):
    vals = ef.sample(name, 201)
    assert all(b >= a - 1e-12 for a, b in zip(vals, vals[1:]))


def test_in_out_symmetry():
    for fam in ("sine", "quad", "cubic", "quart", "quint", "expo", "circ", "back", "elastic", "bounce"):
        assert ef.EASINGS[f"in_out_{fam}"](0.5) == pytest.approx(0.5, abs=1e-9)


def test_known_values():
    assert ef.ease("in_out_cubic", 0.25) == pytest.approx(0.0625)
    assert ef.ease("out_quad", 0.5) == pytest.approx(0.75)
    assert ef.ease("in_sine", 0.5) == pytest.approx(1 - math.cos(math.pi / 4))


def test_back_overshoots():
    assert min(ef.sample("in_back", 101)) < 0
    assert max(ef.sample("out_back", 101)) > 1


def test_name_aliases():
    assert ef.get("easeInOutCubic") is ef.in_out_cubic
    assert ef.get("ease-out-bounce") is ef.out_bounce
    assert ef.get("InOutSine") is ef.in_out_sine
    with pytest.raises(KeyError):
        ef.get("wobble")


def test_clamp_and_tween():
    assert ef.ease("linear", 2) == 1.0
    assert ef.tween(10, 20, 0.5, "in_out_quad") == pytest.approx(15)
