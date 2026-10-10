import shutil
import subprocess

import numpy as np
import pytest

from lut_look_generator import LOOKS, cube_text, identity, make_lut


@pytest.mark.parametrize("look", sorted(LOOKS))
def test_shapes_range_and_strength_zero(look):
    lut = make_lut(look, 9)
    assert lut.shape == (9, 9, 9, 3) and lut.min() >= 0 and lut.max() <= 1
    assert np.allclose(make_lut(look, 9, strength=0.0), identity(9))


def test_look_directions():
    mid = np.array([[0.5, 0.5, 0.5]])
    assert LOOKS["warm"](mid)[0, 0] > LOOKS["warm"](mid)[0, 2]
    assert LOOKS["cool"](mid)[0, 2] > LOOKS["cool"](mid)[0, 0]
    black = np.array([[0.0, 0.0, 0.0]])
    assert LOOKS["matte"](black)[0, 0] > 0.05
    m = LOOKS["mono_contrast"](np.array([[0.9, 0.2, 0.1]]))
    assert m[0, 0] == m[0, 1] == m[0, 2]
    dark, bright = np.array([[0.15, 0.15, 0.15]]), np.array([[0.85, 0.85, 0.85]])
    to = LOOKS["teal_orange"]
    assert to(dark)[0, 2] > to(dark)[0, 0] and to(bright)[0, 0] > to(bright)[0, 2]


def test_cube_text_and_errors():
    t = cube_text("warm", 5, 0.5)
    assert t.splitlines()[1] == "LUT_3D_SIZE 5" and len(t.splitlines()) == 4 + 125
    with pytest.raises(ValueError):
        make_lut("sepia")
    with pytest.raises(ValueError):
        make_lut("warm", strength=2)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_ffmpeg_accepts(tmp_path):
    p = tmp_path / "t.cube"
    p.write_text(cube_text("teal_orange", 9))
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=32x32:d=0.1:r=10",
                        "-vf", f"lut3d=file={p}", "-f", "null", "-"], capture_output=True, timeout=60,
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
