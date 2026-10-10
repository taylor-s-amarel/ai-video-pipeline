import shutil
import subprocess

import pytest

import ken_burns_zoompan_filter as kz


def test_filter_text():
    vf = kz.zoompan_filter(90, (1080, 1920), 1.0, 1.2, (0.5, 0.4))
    assert "zoompan=" in vf and "d=90" in vf and "s=1080x1920" in vf
    assert vf.endswith("setsar=1")


def test_validation():
    with pytest.raises(ValueError):
        kz.zoompan_filter(1)
    with pytest.raises(ValueError):
        kz.zoompan_filter(10, z0=0.8)
    with pytest.raises(ValueError):
        kz.zoompan_filter(10, focus=(1.5, 0))


def test_command_argv():
    argv = kz.command("in.jpg", "out.mp4", 30)
    assert argv[0] == "ffmpeg" and argv[-1] == "out.mp4" and "-vf" in argv


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
@pytest.mark.parametrize("src", ["640x480", "300x900"])
def test_runs_in_ffmpeg_and_emits_frames(src):
    vf = kz.zoompan_filter(12, (90, 160), 1.0, 1.3, (0.3, 0.6), fps=30, prescale=2)
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", f"testsrc=s={src}:d=1:r=1",
                        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                       capture_output=True, check=True, timeout=60, stdin=subprocess.DEVNULL)
    r2 = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "png_pipe", "-i", "-", "-vf", vf,
                         "-f", "rawvideo", "-pix_fmt", "gray", "-"], input=r.stdout, capture_output=True, timeout=60)
    assert r2.returncode == 0, r2.stderr.decode()
    assert len(r2.stdout) == 12 * 90 * 160
