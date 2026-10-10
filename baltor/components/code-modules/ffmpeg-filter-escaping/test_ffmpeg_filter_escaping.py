import shutil
import subprocess

import pytest

import ffmpeg_filter_escaping as fe


def test_levels():
    assert fe.escape_option_value("a:b'c\\d") == "a\\:b\\'c\\\\d"
    assert fe.escape_graph("x,y;[z]") == r"x\,y\;\[z\]"
    # the documented two-level example from ffmpeg-filters
    assert fe.filter_value("this is a 'string': may contain one, or more, special characters") == \
        "this is a \\\\\\'string\\\\\\'\\\\: may contain one\\, or more\\, special characters"


def test_option_and_validation():
    assert fe.option("scale", 640, -2) == "scale=640:-2"
    assert fe.option("subtitles", filename="a:b.srt") == "subtitles=filename=a\\\\:b.srt"
    with pytest.raises(ValueError):
        fe.option("bad name")
    with pytest.raises(ValueError):
        fe.filter_value("a\nb")
    with pytest.raises(ValueError):
        fe.label("out];[x")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_injection_attempt_stays_literal(tmp_path):
    evil = "x',drawbox=c=red:t=fill,'[out];"
    sub = tmp_path / f"subs {evil}.srt".replace("/", "_")
    sub.write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")
    vf = fe.chain(fe.option("subtitles", filename=str(sub)), "format=gray")
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=black:s=64x36:d=0.1:r=10",
                        "-vf", vf, "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True, timeout=60,
                       stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    frame = r.stdout
    assert len(frame) == 64 * 36
    assert sum(frame) / len(frame) < 100  # not filled by an injected drawbox
