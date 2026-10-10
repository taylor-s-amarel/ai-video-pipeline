import json

import numpy as np
import pytest

import video_re_cut_beat_alignment as m

BEATS = list(np.arange(0.0, 60.0, 0.5))  # 120 BPM


def test_cuts_on_the_beat():
    cuts = [2.0, 4.0, 5.5, 7.02, 9.0]
    res = m.run(cuts, BEATS)
    assert res["cuts_on_beat_ratio"] == 1.0
    assert res["chance_ratio"] == pytest.approx(0.28)
    assert res["lift"] == pytest.approx(1 / 0.28, abs=1e-3)
    assert res["beats_per_shot"] == pytest.approx(3.5, abs=0.05)  # median shot 1.75 s at 0.5 s per beat


def test_random_cuts_are_near_chance():
    rng = np.random.default_rng(0)
    cuts = sorted(rng.uniform(1, 59, 400))
    res = m.run(cuts, BEATS)
    assert res["cuts_on_beat_ratio"] == pytest.approx(res["chance_ratio"], abs=0.06)


def test_offsets_show_cuts_leading_the_beat():
    res = m.run([1.96, 2.96, 3.97], BEATS)
    assert res["median_offset_s"] == pytest.approx(-0.04)
    assert all(c["on_beat"] for c in res["per_cut"])


def test_onsets_fallback_and_missing_music():
    res = m.run([1.0, 2.5], beats_s=None, onsets_s=[0.0, 1.0, 1.3, 2.5, 4.0])
    assert res["reference"] == "onsets" and res["cuts_on_beat_ratio"] == 1.0 and 0 < res["chance_ratio"] < 1
    assert m.run([1.0], None, None)["cuts_on_beat_ratio"] is None
    assert m.run([100.0], BEATS)["cuts_on_beat_ratio"] is None


def test_cli(tmp_path, capsys):
    shots = [{"start_s": 0.0, "end_s": 2.0}, {"start_s": 2.0, "end_s": 4.0}, {"start_s": 4.0, "end_s": 6.0}]
    (tmp_path / "s.json").write_text(json.dumps({"shots": shots}))
    (tmp_path / "b.json").write_text(json.dumps({"beats_s": BEATS}))
    assert m.main(["--shots", str(tmp_path / "s.json"), "--beats", str(tmp_path / "b.json")]) == 0
    assert json.loads(capsys.readouterr().out)["cuts_on_beat_ratio"] == 1.0
