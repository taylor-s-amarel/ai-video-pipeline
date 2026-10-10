import shutil

import numpy as np
import pytest

import video_re_palette_per_shot as m
import video_re_synth as synth

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def rgb_of(hex_):
    return np.array([int(hex_[i:i + 2], 16) for i in (1, 3, 5)])


@ffmpeg
def test_flat_colour_shots_report_their_colour(tmp_path):
    srcs = ["color=c=0xD02020:s=160x90:r=25", "color=c=0x2040D0:s=160x90:r=25", "testsrc2=s=160x90:r=25"]
    path, cuts = synth.lavfi_cuts_video(tmp_path / "p.mp4", 1.0, (160, 90), 25, sources=srcs)
    shots = [{"index": i, "start_s": a, "end_s": b} for i, (a, b) in enumerate(zip([0.0] + cuts, cuts + [3.0]))]
    res = m.run(str(path), shots)
    assert res["status"] == "ok"
    red, blue, pattern = res["shots"]
    assert np.abs(rgb_of(red["palette"][0]) - [0xD0, 0x20, 0x20]).max() <= 16
    assert np.abs(rgb_of(blue["palette"][0]) - [0x20, 0x40, 0xD0]).max() <= 16
    assert red["shares"][0] > 0.95 and red["warmth"] > 0.5 and blue["warmth"] < -0.5
    assert len(pattern["palette"]) >= 3
    assert sum(pattern["shares"]) == pytest.approx(1.0, abs=1e-3)
    assert res["overall"]["palette"]


def test_palette_finds_two_known_colours_with_their_shares():
    px = np.zeros((100, 100, 3), np.uint8)
    px[:, :70] = (255, 210, 31)   # house yellow, 70%
    px[:, 70:] = (10, 20, 40)     # navy, 30%
    pal = m.palette(px, k=5)
    assert [c["hex"] for c in pal] == ["#FFD21F", "#0A1428"]
    assert pal[0]["share"] == pytest.approx(0.7, abs=0.02)


def test_lab_of_white_and_black():
    lab = m.srgb_to_lab(np.array([[255, 255, 255], [0, 0, 0]], np.uint8))
    assert lab[0, 0] == pytest.approx(100, abs=0.1) and abs(lab[0, 1]) < 0.5
    assert lab[1, 0] == pytest.approx(0, abs=0.1)


def test_tone_stats_grey_has_no_saturation():
    s = m.tone_stats(np.full((10, 10, 3), 128, np.uint8))
    assert s["saturation"] == 0 and s["mean_luma"] == pytest.approx(128) and s["luma_std"] == 0
