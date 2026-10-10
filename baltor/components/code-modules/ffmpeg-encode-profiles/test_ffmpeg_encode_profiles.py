import json
import shutil
import subprocess

import pytest

from ffmpeg_encode_profiles import PROFILES, argv, describe


def test_argv_contents():
    a = argv("vertical-1080x1920-h264", "in.mov", "out.mp4", fps=30)
    assert a[a.index("-crf") + 1] == "18" and a[a.index("-g") + 1] == "60"
    assert "+faststart" in a and a[-1] == "out.mp4"
    m = argv("master-ffv1-mkv", "in.mov", "out.mkv", fps=None)
    assert "ffv1" in m and "-movflags" not in m


def test_validation():
    with pytest.raises(KeyError):
        describe("tiktok-magic")
    with pytest.raises(ValueError):
        argv("master-ffv1-mkv", "a", "b.mp4")
    assert set(PROFILES) >= {"vertical-1080x1920-h264", "review-proxy-540x960"}


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg missing")
def test_proxy_encode(tmp_path):
    src = tmp_path / "s.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=320x180:d=1:r=30",
                    "-f", "lavfi", "-i", "sine=d=1", "-shortest", "-pix_fmt", "yuv420p", str(src)], check=True, timeout=60)
    out = tmp_path / "p.mp4"
    cmd = argv("review-proxy-540x960", str(src), str(out), fps=30)
    subprocess.run(cmd[:1] + ["-v", "error"] + cmd[1:], check=True, timeout=120)
    info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", str(out)],
                                     capture_output=True, text=True, check=True).stdout)
    v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
    assert (v["width"], v["height"], v["codec_name"], v["pix_fmt"]) == (540, 960, "h264", "yuv420p")
