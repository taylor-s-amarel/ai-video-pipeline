import pytest

from damped_follow_camera import FollowCamera, smooth_damp


def test_smooth_damp_converges_without_overshoot():
    x, v = 0.0, 0.0
    xs = []
    for _ in range(120):
        x, v = smooth_damp(x, 100.0, v, 0.2, 1 / 60)
        xs.append(x)
    assert xs[-1] == pytest.approx(100, abs=0.5)
    assert max(xs) <= 100 + 1e-9
    assert xs == sorted(xs)


def test_dead_zone_ignores_small_moves():
    cam = FollowCamera(view=(100, 100), dead_zone=(20, 20))
    cam.update((0, 0), 1 / 30)
    for _ in range(30):
        pos = cam.update((15, -10), 1 / 30)
    assert pos == (0.0, 0.0)


def test_follows_and_respects_bounds():
    cam = FollowCamera(view=(100, 100), world=(0, 0, 500, 500), smooth_time=0.05)
    cam.update((250, 250), 1 / 30)
    for _ in range(60):
        pos = cam.update((1000, -50), 1 / 30)
    assert pos == (pytest.approx(450), pytest.approx(50))
    assert cam.view_rect()[0] == pytest.approx(400)


def test_small_world_centres():
    cam = FollowCamera(view=(1000, 1000), world=(0, 0, 400, 400))
    assert cam.update((10, 10), 1 / 30) == (200, 200)


def test_look_ahead_leads():
    a = FollowCamera(view=(10, 10), smooth_time=0.05)
    b = FollowCamera(view=(10, 10), smooth_time=0.05, look_ahead=0.2)
    for i in range(30):
        pa = a.update((i * 10.0, 0), 1 / 30)
        pb = b.update((i * 10.0, 0), 1 / 30)
    assert pb[0] > pa[0]
