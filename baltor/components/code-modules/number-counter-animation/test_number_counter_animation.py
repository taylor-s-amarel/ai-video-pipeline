import os
import shutil
import subprocess

import pytest

import number_counter_animation as nc

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def test_format_number():
    assert nc.format_number(1234567) == "1,234,567"
    assert nc.format_number(86.5, 1, suffix="%") == "86.5%"
    assert nc.format_number(-1500, prefix="$") == "-$1,500"
    assert nc.format_number(1234.5, 1, thousands=".", decimal_point=",") == "1.234,5"


def test_frames_land_exactly_and_never_overshoot():
    f = nc.counter_frames(0, 1000, duration=1.0, fps=30, suffix=" dogs")
    assert f[0] == "0 dogs" and f[-1] == "1,000 dogs"
    vals = [int(x.split()[0].replace(",", "")) for x in f]
    assert vals == sorted(vals) and max(vals) == 1000


def test_counting_down():
    f = nc.counter_frames(10, 0, duration=0.5, fps=10)
    assert f[0] == "10" and f[-1] == "0"


def test_bad_easing():
    with pytest.raises(ValueError):
        nc.counter_frames(0, 1, 1, easing="bounce")


@pytest.mark.skipif(not (shutil.which("ffmpeg") and os.path.exists(FONT)), reason="ffmpeg or font missing")
def test_drawtext_expression_runs():
    text = nc.drawtext_text(0, 1000, at=0.1, duration=0.3)
    vf = f"drawtext=fontfile={FONT}:text='{text}':fontsize=20:x=5:y=5:fontcolor=white"
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=160x40:d=0.5:r=10",
                        "-vf", vf, "-f", "null", "-"], capture_output=True, text=True, timeout=60,
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr
