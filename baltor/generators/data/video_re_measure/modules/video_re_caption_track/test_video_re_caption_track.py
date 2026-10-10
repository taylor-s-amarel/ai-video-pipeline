import shutil
import subprocess

import pytest

import video_re_caption_track as m

SRT = """1
00:00:00,500 --> 00:00:02,000
In <i>1970</i>, five scientists

2
00:00:02,100 --> 00:00:03,900
lived UNDER the sea
for 14 days
"""

VTT = """WEBVTT

NOTE a comment

00:00.500 --> 00:02.000 align:center
In 1970, five scientists

00:00:02.100 --> 00:00:03.900
lived under the sea
"""


def test_parse_srt_and_vtt_agree():
    srt, vtt = m.parse_srt(SRT), m.parse_vtt(VTT)
    assert [(c["start_s"], c["end_s"]) for c in srt] == [(0.5, 2.0), (2.1, 3.9)]
    assert [(c["start_s"], c["end_s"]) for c in vtt] == [(0.5, 2.0), (2.1, 3.9)]
    assert srt[0]["text"] == "In 1970, five scientists"  # tags stripped
    assert srt[1]["text"] == "lived UNDER the sea\nfor 14 days"


def test_stats_and_masking():
    caps = m.parse_srt(SRT)
    st = m.stats(caps, duration_s=10.0)
    assert st["count"] == 2 and st["words_max"] == 7 and st["lines_max"] == 2
    assert st["coverage"] == pytest.approx(0.33)
    assert st["first_start_s"] == 0.5 and st["gap_mean_s"] == pytest.approx(0.1)
    masked = m.apply_text_mode(caps, "masked")
    assert masked[0]["text"] == "Word {n}, word word" and masked[0]["start_s"] == 0.5
    assert m.apply_text_mode(caps, "none")[1]["text"] == ""


def test_ocr_samples_become_events():
    items = [{"t_s": 1.0, "bbox": [0, 500, 100, 20], "text": "for 14 days"},
             {"t_s": 1.5, "bbox": [0, 500, 100, 20], "text": "for 14 days"},
             {"t_s": 2.0, "bbox": [0, 500, 100, 20], "text": "for 14 dayz"},   # OCR noise, same caption
             {"t_s": 2.5, "bbox": [0, 500, 100, 20], "text": "in a steel habitat"},
             {"t_s": 2.5, "bbox": [0, 60, 100, 40], "text": "FACT 1"}]          # title band, ignored
    ev = m.from_ocr(items, sample_dt=0.5, frame_height=640)
    assert [(e["start_s"], e["end_s"], e["text"]) for e in ev] == [(1.0, 2.5, "for 14 days"),
                                                                   (2.5, 3.0, "in a steel habitat")]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_embedded_subtitle_stream_is_extracted(tmp_path):
    srt = tmp_path / "s.srt"
    srt.write_text(SRT)
    out = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=160x90:r=10:d=4",
                    "-i", str(srt), "-c:v", "libx264", "-preset", "ultrafast", "-c:s", "mov_text", str(out)], check=True)
    res = m.run(str(out))
    assert res["source"] == "embedded"
    assert [(c["start_s"], c["end_s"]) for c in res["captions"]] == [(0.5, 2.0), (2.1, 3.9)]
    assert res["stats"]["count"] == 2


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_no_captions_is_reported_as_none(tmp_path):
    out = tmp_path / "v.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "color=c=black:s=160x90:r=10:d=1",
                    "-c:v", "libx264", "-preset", "ultrafast", str(out)], check=True)
    res = m.run(str(out))
    assert res["source"] == "none" and res["captions"] == [] and res["stats"] == {"count": 0}
