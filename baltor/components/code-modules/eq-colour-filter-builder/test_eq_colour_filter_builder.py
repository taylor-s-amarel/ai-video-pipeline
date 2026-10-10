import shutil
import subprocess

import numpy as np
import pytest

import eq_colour_filter_builder as cf


def test_strings():
    assert cf.eq(contrast=1.08, saturation=1.15) == "eq=contrast=1.08:saturation=1.15"
    assert cf.colorbalance(rs=0.04, bh=-0.1, preserve_lightness=True) == "colorbalance=rs=0.04:bh=-0.1:pl=1"
    vf = cf.grade(eq={"brightness": 0.02}, balance={"gm": 0.1}, curves="vintage", hue_shift=5)
    assert vf == "curves=preset=vintage,colorbalance=gm=0.1,eq=brightness=0.02,hue=h=5:s=1"
    assert cf.grade() == "null"


@pytest.mark.parametrize("call", [lambda: cf.eq(saturation=4), lambda: cf.eq(sharpness=1),
                                  lambda: cf.colorbalance(rx=0.1), lambda: cf.colorbalance(rs=2),
                                  lambda: cf.curves("teal_orange"), lambda: cf.hue(saturation=20)])
def test_validation(call):
    with pytest.raises(ValueError):
        call()


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_brightness_raises_luma():
    def mean(vf):
        r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=gray:s=16x16:d=0.1:r=10",
                            "-vf", vf + ",format=gray", "-frames:v", "1", "-f", "rawvideo", "-"],
                           capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
        assert r.returncode == 0, r.stderr.decode()
        return np.frombuffer(r.stdout, np.uint8).mean()
    assert mean(cf.grade(eq={"brightness": 0.2}, curves="increase_contrast")) != mean("null")
    assert mean(cf.eq(brightness=0.2)) > mean("null")
