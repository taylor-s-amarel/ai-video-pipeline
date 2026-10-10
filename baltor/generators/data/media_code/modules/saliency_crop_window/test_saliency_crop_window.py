import numpy as np
import pytest

from saliency_crop_window import best_window, saliency, track


def frame_with_subject(cx, W=160, H=90):
    f = np.full((H, W, 3), 90, np.uint8)
    f[30:60, cx - 10:cx + 10] = (240, 200, 40)
    return f


def test_saliency_peaks_on_subject():
    s = saliency(frame_with_subject(120))
    assert s[:, 100:140].mean() > s[:, 0:40].mean() * 3


def test_window_follows_subject_and_has_aspect():
    x, y, w, h = best_window(frame_with_subject(130), aspect=9 / 16)
    assert w / h == pytest.approx(9 / 16, abs=0.02) and h == 90
    assert x <= 130 - 10 and x + w >= 130 + 10
    x2, _, _, _ = best_window(frame_with_subject(30), aspect=9 / 16)
    assert x2 < x


def test_track_smooths_and_limits():
    wins = [(0, 0, 50, 90)] * 5 + [(100, 0, 50, 90)] * 5
    t = track(wins, smoothing=0.5, max_step=10)
    xs = [w[0] for w in t]
    assert xs[5] == 10 and all(b - a <= 10 for a, b in zip(xs, xs[1:]))
    with pytest.raises(ValueError):
        track(wins, smoothing=1.0)
