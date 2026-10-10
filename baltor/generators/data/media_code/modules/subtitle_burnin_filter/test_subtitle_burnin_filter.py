import shutil
import subprocess

import pytest

from subtitle_burnin_filter import ass_filter, command, force_style_string, subtitles_filter

SRT = "1\n00:00:00,000 --> 00:00:01,000\nHELLO\n"


def test_strings():
    assert ass_filter("/a/b.ass") == "ass=filename=/a/b.ass"
    vf = subtitles_filter("c:/x.srt", force_style={"Fontname": "DejaVu Sans", "Fontsize": 24})
    assert vf.startswith("subtitles=filename=c\\\\:/x.srt:force_style=")
    assert "Fontname=DejaVu Sans\\,Fontsize=24" in vf


def test_validation():
    with pytest.raises(ValueError):
        force_style_string({"Font name": "x"})
    with pytest.raises(ValueError):
        force_style_string({"Fontname": "a,b"})
    with pytest.raises(ValueError):
        subtitles_filter("x.srt", original_size="big")
    with pytest.raises(ValueError):
        ass_filter("a\nb")


def test_command():
    argv = command("in.mp4", "out.mp4", "ass=filename=x.ass")
    assert argv[argv.index("-vf") + 1] == "ass=filename=x.ass" and argv[-1] == "out.mp4"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_burns_text_with_hostile_filename(tmp_path):
    p = tmp_path / "it's [weird], name; ok.srt"
    p.write_text(SRT, encoding="utf-8")
    vf = subtitles_filter(str(p), force_style={"Fontname": "DejaVu Sans", "Fontsize": 40, "Alignment": 5})
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=black:s=320x180:d=0.2:r=10",
                        "-vf", vf, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                       capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    assert sum(1 for b in r.stdout if b > 128) > 100  # text drawn
