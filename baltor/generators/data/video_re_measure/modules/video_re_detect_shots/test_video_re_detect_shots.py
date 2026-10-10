import shutil
import subprocess

import numpy as np
import pytest

import video_re_detect_shots as m
import video_re_synth as synth

ffmpeg = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def has_filter(name):
    if not shutil.which("ffmpeg"):
        return False
    out = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    return f" {name} " in out


@ffmpeg
def test_hard_cuts_found_within_one_frame(tmp_path):
    path, cuts = synth.lavfi_cuts_video(tmp_path / "cuts.mp4", seconds_per_shot=1.0, fps=25)
    res = m.run(str(path))
    assert res["status"] == "ok"
    found = [t["t_s"] for t in res["transitions"] if t["type"] == "cut"]
    assert len(found) == len(cuts)
    for f, c in zip(found, cuts):
        assert abs(f - c) <= 1 / 25 + 1e-6
    shots = res["shots"]
    assert len(shots) == 4 and shots[0]["start_s"] == 0
    assert shots[-1]["end_s"] == pytest.approx(4.0, abs=0.05)
    assert sum(s["duration_s"] for s in shots) == pytest.approx(res["duration_s"])


@ffmpeg
def test_camera_pan_and_zoom_are_not_cuts(tmp_path):
    pan = synth.encode_frames(tmp_path / "pan.mp4", synth.pan_frames(50, (320, 180), dx_per_frame=4), 25, (320, 180))
    zoom = synth.encode_frames(tmp_path / "zoom.mp4", synth.zoom_frames(50, (320, 180), 0.01), 25, (320, 180))
    for p in (pan, zoom):
        res = m.run(str(p))
        assert res["transitions"] == [], res["transitions"]
        assert len(res["shots"]) == 1


@ffmpeg
def test_dissolve_is_one_gradual_boundary_near_its_centre(tmp_path):
    out = tmp_path / "dissolve.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error",
                    "-f", "lavfi", "-i", "testsrc2=s=320x180:r=25:d=2.5", "-f", "lavfi", "-i", "smptebars=s=320x180:r=25:d=2.5",
                    "-filter_complex", "[0:v]format=yuv420p,setsar=1[a];[1:v]format=yuv420p,setsar=1[b];"
                    "[a][b]xfade=transition=fade:duration=0.8:offset=1.2[v]",
                    "-map", "[v]", "-c:v", "libx264", "-preset", "ultrafast", "-crf", "16", str(out)], check=True)
    res = m.run(str(out))
    assert [t["type"] for t in res["transitions"]] == ["gradual"]
    assert res["transitions"][0]["t_s"] == pytest.approx(1.6, abs=0.25)


@pytest.mark.skipif(not has_filter("scdet"), reason="ffmpeg scdet filter not available")
def test_scdet_cross_check_agrees(tmp_path):
    path, cuts = synth.lavfi_cuts_video(tmp_path / "cuts.mp4", seconds_per_shot=1.0, fps=25)
    res = m.run(str(path), method="scdet")
    assert res["status"] == "ok"
    assert [round(t["t_s"], 2) for t in res["transitions"]] == pytest.approx(cuts, abs=0.041)


def test_minimum_shot_length_keeps_the_stronger_of_two_close_peaks():
    scores = np.full(100, 0.01)
    scores[40], scores[42] = 0.5, 0.8   # two spikes 2 frames apart (a flash frame)
    scores[80] = 0.6
    cuts = m.find_cuts(scores, fps=25, min_shot_s=0.2)
    assert [c for c, _ in cuts] == [42, 80]


def test_quiet_noise_never_cuts():
    rng = np.random.default_rng(1)
    scores = 0.01 + 0.005 * rng.random(250)
    assert m.find_cuts(scores, fps=25) == []


def test_shots_cover_the_timeline_exactly():
    shots = m.shots_from_boundaries([{"frame": 30, "type": "cut", "score": 0.5}], 100, 25.0)
    assert [(s["start_s"], s["end_s"]) for s in shots] == [(0.0, 1.2), (1.2, 4.0)]
    assert shots[1]["transition_in"]["type"] == "cut"
