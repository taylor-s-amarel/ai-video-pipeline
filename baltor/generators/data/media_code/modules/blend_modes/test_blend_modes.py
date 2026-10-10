import numpy as np
import pytest

from blend_modes import MODES, blend


def g(v, shape=(2, 2, 3)):
    return np.full(shape, v, float)


def test_reference_values():
    assert blend(g(0.5), g(0.5), "multiply")[0, 0, 0] == pytest.approx(0.25)
    assert blend(g(0.5), g(0.5), "screen")[0, 0, 0] == pytest.approx(0.75)
    assert blend(g(0.25), g(0.5), "overlay")[0, 0, 0] == pytest.approx(0.25)
    assert blend(g(0.5), g(0.75), "color-dodge")[0, 0, 0] == pytest.approx(1.0)
    assert blend(g(0.5), g(0.25), "color-burn")[0, 0, 0] == pytest.approx(0.0)
    assert blend(g(0.3), g(0.8), "difference")[0, 0, 0] == pytest.approx(0.5)
    assert blend(g(0.5), g(0.5), "soft-light")[0, 0, 0] == pytest.approx(0.5)


def test_neutral_colours():
    rng = np.random.default_rng(0)
    b = rng.random((4, 4, 3))
    assert np.allclose(blend(b, np.ones_like(b), "multiply"), b)
    assert np.allclose(blend(b, np.zeros_like(b), "screen"), b)
    assert np.allclose(blend(b, g(0.5, b.shape), "soft-light"), b)


@pytest.mark.parametrize("mode", sorted(MODES))
def test_range_and_opacity(mode):
    rng = np.random.default_rng(1)
    b, s = rng.random((8, 8, 3)), rng.random((8, 8, 3))
    out = blend(b, s, mode, opacity=0.35)
    assert out.min() >= 0 and out.max() <= 1
    assert np.allclose(blend(b, s, mode, opacity=0.0), b)


def test_errors_and_alpha():
    with pytest.raises(ValueError):
        blend(g(0), g(0), "vivid")
    with pytest.raises(ValueError):
        blend(g(0), g(0, (3, 3, 3)))
    out = blend(g(0.0), g(1.0), "normal", source_alpha=np.full((2, 2), 0.5))
    assert out[0, 0, 0] == pytest.approx(0.5)
