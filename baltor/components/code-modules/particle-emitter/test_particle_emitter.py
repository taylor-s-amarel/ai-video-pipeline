import numpy as np
import pytest

from particle_emitter import Emitter


def test_deterministic():
    a = Emitter(rate=20, seed=3, horizon=10).state(2.0)
    b = Emitter(rate=20, seed=3, horizon=10).state(2.0)
    assert a == b
    assert a != Emitter(rate=20, seed=4, horizon=10).state(2.0)


def test_alive_count_matches_rate_times_lifetime():
    em = Emitter(rate=30, lifetime=2.0, horizon=20)
    assert len(em.state(5.0)) == 60
    assert len(em.state(0.5)) == 16


def test_ballistic_closed_form():
    em = Emitter(rate=1, lifetime=10, velocity=(10, 0), velocity_jitter=(0, 0), gravity=(0, 20), horizon=5)
    p = [s for s in em.state(2.0) if s["age"] == pytest.approx(2.0)][0]
    assert p["x"] == pytest.approx(20) and p["y"] == pytest.approx(40)


def test_drag_slows_down():
    free = Emitter(rate=1, lifetime=10, velocity=(100, 0), velocity_jitter=(0, 0), horizon=3)
    drag = Emitter(rate=1, lifetime=10, velocity=(100, 0), velocity_jitter=(0, 0), drag=1.0, horizon=3)
    assert drag.state(2.0)[0]["x"] < free.state(2.0)[0]["x"]


def test_render_opacity_cap_and_validation():
    em = Emitter(rate=50, origin=(50, 50), size=(4, 6), horizon=5)
    a = np.asarray(em.render(1.0, (100, 100)))[..., 3]
    assert 0 < a.max() <= 250
    with pytest.raises(ValueError):
        Emitter(max_opacity=1.0)
    with pytest.raises(ValueError):
        Emitter(rate=0)
