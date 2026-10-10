import shutil
import subprocess

import pytest

from ffprobe_media_info import probe, summarise

SAMPLE = {
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080, "pix_fmt": "yuv420p",
         "avg_frame_rate": "30000/1001", "r_frame_rate": "30000/1001", "nb_frames": "1918",
         "side_data_list": [{"rotation": -90}]},
        {"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000", "channels": 2, "channel_layout": "stereo"},
        {"codec_type": "video", "codec_name": "mjpeg", "disposition": {"attached_pic": 1}},
    ],
    "format": {"duration": "64.000000", "size": "12345678", "bit_rate": "1543209", "format_name": "mov,mp4,m4a,3gp,3g2,mj2"},
}


def test_summarise_sample():
    s = summarise(SAMPLE)
    assert s["duration"] == 64.0 and s["video"]["codec"] == "h264"
    assert (s["video"]["width"], s["video"]["height"]) == (1080, 1920)  # rotation applied
    assert s["video"]["fps"] == pytest.approx(29.97, abs=0.01) and s["video"]["frames"] == 1918
    assert s["audio"]["sample_rate"] == 48000 and not s["vfr"]


def test_vfr_and_missing():
    info = {"streams": [{"codec_type": "video", "avg_frame_rate": "24/1", "r_frame_rate": "30/1"}], "format": {}}
    s = summarise(info)
    assert s["vfr"] and s["audio"] is None and s["duration"] is None


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg missing")
def test_real_file(tmp_path):
    p = tmp_path / "t.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=128x72:d=1:r=25",
                    "-f", "lavfi", "-i", "sine=d=1:r=44100", "-shortest", "-pix_fmt", "yuv420p", str(p)],
                   check=True, timeout=60)
    s = summarise(probe(str(p)))
    assert s["video"]["width"] == 128 and s["video"]["fps"] == 25 and s["audio"]["sample_rate"] == 44100
