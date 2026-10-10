import os
import shutil
import subprocess

import pytest

from drawtext_filter_builder import drawtext

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def test_basic_string():
    f = drawtext("Hi: there", fontfile="/f.ttf", size=40, color="#FFD21F")
    assert f.startswith("drawtext=fontfile=/f.ttf:text=Hi\\\\: there:expansion=none:fontsize=40")
    assert "fontcolor=0xFFD21F@0.98" in f


def test_validation():
    with pytest.raises(ValueError):
        drawtext()
    with pytest.raises(ValueError):
        drawtext("a", textfile="b")
    with pytest.raises(ValueError):
        drawtext("a\nb")
    with pytest.raises(ValueError):
        drawtext("a", color="gold")
    with pytest.raises(ValueError):
        drawtext("a", start=2, end=1)
    with pytest.raises(ValueError):
        drawtext("a", x="w-'1'")


def render(vf):
    return subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=black:s=320x120:d=1:r=10",
                           "-vf", vf, "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, timeout=60,
                          stdin=subprocess.DEVNULL)


@pytest.mark.skipif(not (shutil.which("ffmpeg") and os.path.exists(FONT)), reason="ffmpeg or font missing")
def test_hostile_text_renders_literally():
    vf = drawtext("it's 50%{pts}: a,b;[c] \\ ok", fontfile=FONT, size=18, box=True, start=0.2, end=0.8, fade=0.2)
    r = render(vf)
    assert r.returncode == 0, r.stderr.decode()
    frames = [r.stdout[i:i + 320 * 120] for i in range(0, len(r.stdout), 320 * 120)]
    assert len(frames) == 10
    assert max(frames[0]) == 0           # before the window: nothing drawn
    assert sum(1 for b in frames[5] if b > 128) > 50   # inside: text visible


@pytest.mark.skipif(not (shutil.which("ffmpeg") and os.path.exists(FONT)), reason="ffmpeg or font missing")
def test_textfile_mode(tmp_path):
    p = tmp_path / "t.txt"
    p.write_text("line one\nline two", encoding="utf-8")
    r = render(drawtext(textfile=str(p), fontfile=FONT, size=20))
    assert r.returncode == 0, r.stderr.decode()
