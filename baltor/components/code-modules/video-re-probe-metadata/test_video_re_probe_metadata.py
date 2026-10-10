import shutil
import subprocess

import pytest

import video_re_common as common
import video_re_probe_metadata as m

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


@ffmpeg
def test_probe_synthetic_clip_with_audio(tmp_path):
    out = tmp_path / "clip.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "testsrc2=s=320x180:r=25:d=2",
                    "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:d=2", "-c:v", "libx264", "-preset",
                    "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)], check=True)
    res = m.run(str(out))
    assert res["status"] == "ok"
    src = res["source"]
    assert (src["width"], src["height"]) == (320, 180)
    assert src["fps"] == pytest.approx(25.0)
    assert src["has_audio"] is True
    assert src["duration_s"] == pytest.approx(2.0, abs=0.1)
    assert res["details"]["aspect"] == "16:9" and res["details"]["orientation"] == "horizontal"
    assert "ffprobe" in res["tools"]


@ffmpeg
def test_video_without_audio(tmp_path):
    out = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=red:s=180x320:r=30:d=1",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(out)], check=True)
    res = m.run(str(out))
    assert res["source"]["has_audio"] is False
    assert res["details"]["aspect"] == "9:16" and res["details"]["orientation"] == "vertical"


def test_rotation_and_sar_applied():
    info = {"streams": [{"codec_type": "video", "width": 1920, "height": 1080, "avg_frame_rate": "30000/1001",
                         "sample_aspect_ratio": "1:1", "side_data_list": [{"rotation": -90}]}],
            "format": {"duration": "12.5"}}
    got = common.media_info_from_probe(info, "x.mov")
    assert (got["width"], got["height"]) == (1080, 1920)
    assert got["rotation"] == 270
    assert got["fps"] == pytest.approx(29.97, abs=0.01)
    anamorphic = {"streams": [{"codec_type": "video", "width": 1440, "height": 1080, "avg_frame_rate": "25/1",
                               "sample_aspect_ratio": "4:3"}], "format": {"duration": "1"}}
    assert common.media_info_from_probe(anamorphic)["width"] == 1920


def test_missing_file_is_an_error_not_a_guess(tmp_path):
    if not shutil.which("ffprobe"):
        pytest.skip("ffprobe not installed")
    res = m.run(str(tmp_path / "nope.mp4"))
    assert res["status"] == "error"
