import shutil
import subprocess

import numpy as np
import pytest

from cube_lut import apply, identity, read_cube, write_cube


def test_identity_roundtrip_and_apply():
    lut = identity(9)
    text = write_cube(lut, "id")
    assert text.splitlines()[1] == "LUT_3D_SIZE 9"
    assert text.splitlines()[5] == "0.125000 0.000000 0.000000"   # red changes fastest
    back = read_cube(text)
    assert np.allclose(back, lut)
    img = np.random.default_rng(0).integers(0, 256, (16, 16, 3)).astype(np.uint8)
    assert np.abs(apply(img, back).astype(int) - img).max() <= 1


def test_known_transform():
    lut = 1.0 - identity(5)                      # invert
    img = np.array([[[0, 128, 255]]], np.uint8)
    assert apply(img, lut).tolist() == [[[255, 127, 0]]]


def test_domain_and_errors():
    text = "LUT_3D_SIZE 2\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 2 2 2\n" + "\n".join(["0 0 0"] * 7 + ["2 2 2"])
    assert read_cube(text)[1, 1, 1].tolist() == [1, 1, 1]
    with pytest.raises(ValueError):
        read_cube("LUT_3D_SIZE 2\n0 0 0\n")
    with pytest.raises(ValueError):
        read_cube("0 0 0")
    with pytest.raises(ValueError):
        write_cube(np.zeros((2, 2, 3)))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_ffmpeg_lut3d_reads_file(tmp_path):
    p = tmp_path / "inv.cube"
    p.write_text(write_cube(1.0 - identity(5), "invert"))
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=8x8:d=0.1:r=10",
                        "-vf", f"lut3d=file={p},format=rgb24", "-frames:v", "1", "-f", "rawvideo", "-"],
                       capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    assert np.frombuffer(r.stdout, np.uint8).min() > 240     # black became white
