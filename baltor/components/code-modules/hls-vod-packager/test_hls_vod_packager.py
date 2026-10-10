import shutil
import subprocess

import pytest

from hls_vod_packager import check_segments, master_playlist, parse_media_playlist, rendition_argv


def test_master():
    m = master_playlist([{"uri": "720p/index.m3u8", "bandwidth": 2800000, "resolution": (720, 1280)},
                         {"uri": "360p/index.m3u8", "bandwidth": 800000, "resolution": (360, 640)}])
    lines = m.splitlines()
    assert lines[0] == "#EXTM3U" and lines[3] == "360p/index.m3u8" and "RESOLUTION=720x1280" in lines[4]
    with pytest.raises(ValueError):
        master_playlist([{"uri": "#bad", "bandwidth": 1}])


def test_argv():
    a = rendition_argv("in.mp4", "out", 720, 1280, 2500, segment_s=4, fps=30)
    assert a[a.index("-g") + 1] == "120" and a[-1] == "out/index.m3u8"


def test_parse_and_check():
    pl = "#EXTM3U\n#EXT-X-TARGETDURATION:4\n#EXTINF:4.0,\na.ts\n#EXTINF:5.2,\nb.ts\n#EXT-X-ENDLIST\n"
    info = parse_media_playlist(pl)
    assert info["segments"] == 2 and info["total"] == 9.2 and info["vod"]
    assert len(check_segments(info)) == 1
    with pytest.raises(ValueError):
        parse_media_playlist("nope")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_real_package(tmp_path):
    src = tmp_path / "s.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=160x90:d=5:r=10",
                    "-f", "lavfi", "-i", "sine=d=5", "-shortest", "-pix_fmt", "yuv420p", str(src)], check=True, timeout=60)
    out = tmp_path / "r"
    out.mkdir()
    a = rendition_argv(str(src), str(out), 90, 160, 300, segment_s=2, fps=10)
    subprocess.run(a[:1] + ["-v", "error"] + a[1:], check=True, timeout=120)
    info = parse_media_playlist((out / "index.m3u8").read_text())
    assert info["vod"] and info["segments"] == 3 and abs(info["total"] - 5.0) < 0.3
    assert check_segments(info) == []
