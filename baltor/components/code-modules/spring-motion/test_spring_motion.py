import pytest

from spring_motion import Spring


def integrate(s: Spring, t_end: float, dt: float = 1e-5) -> float:
    x, v, t = s.start, s.velocity, 0.0
    while t < t_end - 1e-12:
        a = (-s.damping * v - s.stiffness * (x - s.target)) / s.mass
        v += a * dt
        x += v * dt
        t += dt
    return x


@pytest.mark.parametrize("damping", [8.0, 2 * (170 ** 0.5), 60.0])
def test_closed_form_matches_numeric(damping):
    s = Spring(stiffness=170, damping=damping, velocity=2.0)
    for t in (0.05, 0.2, 0.5):
        assert s.value(t) == pytest.approx(integrate(s, t), abs=2e-3)


def test_regimes():
    assert Spring(stiffness=100, damping=5).zeta < 1
    assert Spring(stiffness=100, damping=20).zeta == pytest.approx(1)
    assert Spring(stiffness=100, damping=40).zeta > 1


def test_underdamped_overshoots_critical_does_not():
    assert Spring(stiffness=180, damping=8).overshoot() > 0.2
    assert Spring(stiffness=100, damping=20).overshoot() < 1e-6


def test_converges_and_settles():
    s = Spring.from_ratio(0.4, 3.0)
    assert s.value(5.0) == pytest.approx(1.0, abs=1e-6)
    st = s.settle_time(0.02)
    assert 0.1 < st < 2.0
    assert abs(s.value(st + 0.1) - 1) <= 0.02


def test_frames_and_validation():
    f = Spring().frames(30, 1.0)
    assert len(f) == 31 and f[0] == 0.0
    with pytest.raises(ValueError):
        Spring(stiffness=0)
