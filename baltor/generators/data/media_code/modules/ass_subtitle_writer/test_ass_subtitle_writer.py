import shutil
import subprocess

import numpy as np
import pytest

from ass_subtitle_writer import Event, Script, Style, ass_color, ass_time, escape_text


def test_colour_and_time():
    assert ass_color("#FFD21F") == "&H001FD2FF"
    assert ass_color("#000000", 0.5) == "&H80000000"
    assert ass_time(3661.239) == "1:01:01.24"
    with pytest.raises(ValueError):
        ass_color("yellow")


def test_escape_blocks_injection():
    assert escape_text("a{\\pos(0,0)}b\nc") == "a\\{＼pos(0,0)\\}b\\Nc"


def test_script_text():
    s = Script(1080, 1920, styles=[Style("Cap", font="DejaVu Sans")],
               events=[Event(2, 3, "B", style="Cap"), Event(1, 2, "A", style="Cap", tags="\\fad(80,80)")])
    text = s.dumps()
    assert "PlayResY: 1920" in text
    assert text.index("Dialogue: 0,0:00:01.00") < text.index("Dialogue: 0,0:00:02.00")
    assert "{\\fad(80,80)}A" in text


def test_validation():
    with pytest.raises(ValueError):
        Script(events=[Event(0, 1, "x", style="Missing")]).dumps()
    with pytest.raises(ValueError):
        Event(2, 1, "x").line()
    with pytest.raises(ValueError):
        Style(name="a,b").line()


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_libass_renders(tmp_path):
    s = Script(320, 180, styles=[Style("Cap", font="DejaVu Sans", size=40, align=5, outline=0, margin_v=0)],
               events=[Event(0, 1, "Hi {there}", style="Cap")])
    p = tmp_path / "c.ass"
    p.write_text(s.dumps(), encoding="utf-8")
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=black:s=320x180:d=0.2:r=10",
                        "-vf", f"ass={p}", "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    img = np.frombuffer(r.stdout, np.uint8)
    assert (img > 128).sum() > 200  # text was drawn
