import shutil
import subprocess

import numpy as np
import pytest

from hald_clut_identity import apply, ffmpeg_graph, identity_array, identity_image, to_lut


def test_identity_shape_and_corners():
    a = identity_array(4)
    assert a.shape == (64, 64, 3)
    assert a[0, 0].tolist() == [0, 0, 0] and a[-1, -1].tolist() == [255, 255, 255]
    assert identity_image(8).size == (512, 512)


def test_identity_apply_is_noop_and_edit_applies():
    hald = identity_array(6)
    img = np.random.default_rng(0).integers(0, 256, (20, 20, 3)).astype(np.uint8)
    assert np.abs(apply(img, hald).astype(int) - img).max() <= 1
    inverted = 255 - hald
    assert np.abs(apply(img, inverted).astype(int) - (255 - img)).max() <= 1


def test_errors():
    with pytest.raises(ValueError):
        identity_array(1)
    with pytest.raises(ValueError):
        to_lut(np.zeros((10, 10, 3), np.uint8))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_ffmpeg_haldclut_identity(tmp_path):
    p = tmp_path / "hald.png"
    identity_image(4).save(p)
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=0x336699:s=16x16:d=0.2:r=10",
                        "-i", str(p), "-filter_complex", ffmpeg_graph() + ";[graded]format=rgb24[o]", "-map", "[o]",
                        "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    px = np.frombuffer(r.stdout, np.uint8)[:3].astype(int)
    assert np.abs(px - [0x33, 0x66, 0x99]).max() <= 6
