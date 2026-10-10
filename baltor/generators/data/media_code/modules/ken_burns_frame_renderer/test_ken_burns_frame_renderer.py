import numpy as np
import pytest
from PIL import Image

import ken_burns_frame_renderer as kr


def gradient(w=200, h=100):
    x = np.tile(np.linspace(0, 255, w, dtype=np.float32), (h, 1))
    return Image.fromarray(np.stack([x, x, x], -1).astype(np.uint8))


def test_full_crop_matches_resize():
    img = gradient()
    f = kr.render_frame(img, (0, 0, 200, 100), (100, 50))
    assert f.size == (100, 50)
    ref = np.asarray(img.resize((100, 50), Image.Resampling.BILINEAR), np.float32)
    assert np.abs(np.asarray(f, np.float32) - ref).mean() < 3


def test_subpixel_shift_moves_content_smoothly():
    img = gradient()
    a = np.asarray(kr.render_frame(img, (10.0, 0, 100, 100), (100, 100)), np.float32).mean()
    b = np.asarray(kr.render_frame(img, (10.5, 0, 100, 100), (100, 100)), np.float32).mean()
    c = np.asarray(kr.render_frame(img, (11.0, 0, 100, 100), (100, 100)), np.float32).mean()
    assert a < b < c


def test_render_frames_and_supersample():
    frames = list(kr.render_frames(gradient(), [(0, 0, 100, 100), (50, 0, 100, 100)], (64, 64), supersample=2))
    assert len(frames) == 2 and frames[0].size == (64, 64)
    with pytest.raises(ValueError):
        kr.render_frame(gradient(), (0, 0, 0, 10), (10, 10))
    with pytest.raises(ValueError):
        list(kr.render_frames(gradient(), [(0, 0, 10, 10)], (10, 10), supersample=0))


def test_argv():
    argv = kr.ffmpeg_pipe_argv("o.mp4", (1080, 1920), 30)
    assert argv[argv.index("-s") + 1] == "1080x1920" and argv[-1] == "o.mp4"
