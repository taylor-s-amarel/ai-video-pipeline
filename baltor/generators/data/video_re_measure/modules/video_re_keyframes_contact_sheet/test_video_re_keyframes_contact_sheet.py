import shutil

import numpy as np
import pytest
from PIL import Image

import video_re_keyframes_contact_sheet as m
import video_re_synth as synth

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


@ffmpeg
def test_one_keyframe_per_shot_and_a_sheet(tmp_path):
    path, cuts = synth.lavfi_cuts_video(tmp_path / "c.mp4", seconds_per_shot=1.0, fps=25)
    shots = [{"index": i, "start_s": a, "end_s": b} for i, (a, b) in enumerate(zip([0.0] + cuts, cuts + [4.0]))]
    res = m.run(str(path), shots, tmp_path / "ev", width=160)
    assert res["status"] == "ok"
    assert [k["index"] for k in res["keyframes"]] == [0, 1, 2, 3]
    for k in res["keyframes"]:
        img = Image.open(tmp_path / "ev" / k["path"])
        assert img.size == (160, 90)
        shot = shots[k["index"]]
        assert shot["start_s"] < k["t_s"] < shot["end_s"]
    # shot 1 is a flat colour, shot 0 is a detailed test pattern
    assert res["keyframes"][0]["sharpness"] > res["keyframes"][1]["sharpness"]
    assert len(res["contact_sheets"]) == 1
    sheet = Image.open(tmp_path / "ev" / res["contact_sheets"][0])
    assert sheet.width > 4 * 160


def test_candidate_times_stay_inside_the_shot():
    ts = m.candidate_times({"start_s": 2.0, "end_s": 4.0}, 25.0)
    assert len(ts) == 3 and all(2.0 < t < 4.0 for t in ts)
    assert m.candidate_times({"start_s": 2.0, "end_s": 2.08}, 25.0, 3) == [pytest.approx(2.04)]


def test_sharpness_prefers_detail():
    flat = np.full((40, 40), 128, np.uint8)
    rng = np.random.default_rng(0)
    busy = rng.integers(0, 255, (40, 40)).astype(np.uint8)
    assert m.sharpness(busy) > m.sharpness(flat) == 0
