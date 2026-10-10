import shutil

import numpy as np
import pytest

from ffmpeg_raw_frame_pipe import FrameReader, FrameWriter

needs = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def test_validation():
    with pytest.raises(ValueError):
        FrameReader("x.mp4", size=(10, 10), pix_fmt="yuv")
    with pytest.raises(ValueError):
        FrameReader("x.mp4")
    with pytest.raises(ValueError):
        FrameWriter("o.mp4", (11, 10))


@needs
def test_write_then_read_roundtrip(tmp_path):
    out = tmp_path / "g.mp4"
    with FrameWriter(str(out), (64, 48), fps=10) as wr:
        for i in range(10):
            wr.write(np.full((48, 64, 3), i * 20, np.uint8))
        with pytest.raises(ValueError):
            wr.write(np.zeros((10, 10, 3), np.uint8))
    assert wr.frames == 10
    with FrameReader(str(out), size=(32, 24), pix_fmt="gray") as rd:
        frames = list(rd)
    assert len(frames) == 10 and frames[0].shape == (24, 32)
    means = [f.mean() for f in frames]
    assert means == sorted(means) and means[-1] - means[0] > 100


@needs
def test_reader_error_surface(tmp_path):
    with pytest.raises(RuntimeError, match="ffmpeg reader failed"):
        with FrameReader(str(tmp_path / "missing.mp4"), size=(8, 8)) as rd:
            list(rd)
