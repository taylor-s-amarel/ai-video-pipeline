import numpy as np

from scene_change_detector import detect, distances, histogram, shot_lengths


def clip(color, n, noise=0, seed=0):
    rng = np.random.default_rng(seed)
    base = np.zeros((n, 24, 32, 3), np.int16) + np.array(color, np.int16)
    if noise:
        base += rng.integers(-noise, noise + 1, base.shape)
    return np.clip(base, 0, 255).astype(np.uint8)


def test_histogram_normalised():
    h = histogram(clip((10, 20, 30), 1)[0])
    assert h.sum() == 1.0 and len(h) == 48


def test_detects_hard_cuts_only():
    frames = np.concatenate([clip((200, 30, 30), 20, 8, 1), clip((30, 30, 200), 25, 8, 2), clip((240, 240, 240), 15, 8, 3)])
    cuts = detect(frames, fps=10)
    assert [c["frame"] for c in cuts] == [20, 45]
    stats = shot_lengths(cuts, len(frames), 10)
    assert stats["shots"] == 3 and stats["lengths_s"] == [2.0, 2.5, 1.5]


def test_slow_fade_is_not_a_cut():
    frames = np.stack([np.full((24, 32, 3), int(v), np.uint8) for v in np.linspace(0, 255, 120)])
    assert detect(frames, fps=30) == []
    assert distances(frames).max() < 0.35
