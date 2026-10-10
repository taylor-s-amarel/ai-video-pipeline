import numpy as np
import pytest

from precipitation_overlay import Precipitation


@pytest.mark.parametrize("kind", ["rain", "snow"])
def test_loops_exactly(kind):
    p = Precipitation(kind=kind, count=50, size=(200, 300), loop_s=3.0, seed=2)
    assert np.allclose(p.positions(0.7), p.positions(3.7), atol=1e-6)


def test_moves_between_frames_and_renders():
    p = Precipitation(count=80, size=(200, 300), seed=1)
    assert not np.allclose(p.positions(0.0), p.positions(0.1))
    a = np.asarray(p.render(0.3))[..., 3]
    assert a.max() > 0 and a.max() <= int(255 * 0.6)


def test_deterministic():
    a = Precipitation(kind="snow", count=20, size=(100, 100), seed=9).positions(1.0)
    b = Precipitation(kind="snow", count=20, size=(100, 100), seed=9).positions(1.0)
    assert np.array_equal(a, b)


def test_validation():
    with pytest.raises(ValueError):
        Precipitation(kind="hail")
    with pytest.raises(ValueError):
        Precipitation(max_opacity=1.0)
