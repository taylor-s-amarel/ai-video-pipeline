import numpy as np
import pytest

from amplitude_lip_sync import cues, frame_rms, mouth_openness, mouth_shapes

SR = 16000


def speechlike():
    t = np.arange(SR * 2) / SR
    sig = 0.5 * np.sin(2 * np.pi * 180 * t)
    env = np.zeros_like(t)
    env[(t > 0.3) & (t < 0.8)] = 1.0
    env[(t > 1.2) & (t < 1.5)] = 0.3
    return sig * env


def test_rms_frames():
    r = frame_rms(np.ones(SR), SR, 25)
    assert len(r) == 25 and np.allclose(r, 1)


def test_openness_follows_speech():
    o = mouth_openness(speechlike(), SR, fps=25)
    assert o[2] == 0  # silence at 0.08 s
    assert o[15] > 0.8  # loud part at 0.6 s
    assert 0 < o[34] < o[15]  # quieter part at 1.36 s
    assert o.max() <= 1


def test_shapes_and_hold():
    shapes = mouth_shapes([0, 0.9, 0, 0, 0, 0], fps=50, min_hold_s=0.06)
    assert shapes[:4] == ["X", "D", "D", "D"]
    c = cues(mouth_shapes(mouth_openness(speechlike(), SR, 25), 25), 25)
    assert c[0] == (0.0, "X") and any(s == "D" for _, s in c)
    with pytest.raises(ValueError):
        mouth_shapes([0.1], thresholds=(0.5,), letters=("X",))
