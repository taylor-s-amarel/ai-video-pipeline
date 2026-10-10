import json

import pytest

import video_re_shot_stats as m


def shots_from(durations):
    out, t = [], 0.0
    for i, d in enumerate(durations):
        out.append({"index": i, "start_s": t, "end_s": t + d, "duration_s": d,
                    "transition_in": {"type": "start" if i == 0 else "cut"}})
        t += d
    return out


def test_regular_template_timing():
    res = m.run(shots_from([2.0] * 30))  # 60 s, a cut every 2 s
    assert res["count"] == 30
    assert res["median_s"] == 2.0 and res["mean_s"] == 2.0
    assert res["cut_rate_per_min"] == pytest.approx(29.0)
    assert res["cv"] == 0
    assert res["dominant_s"] == 2.0 and res["share_near_dominant"] == 1.0
    assert res["histogram"]["2-4"] == 30
    assert res["transitions"] == {"cut": 29}


def test_accelerating_edit_has_negative_trend_and_fast_hook():
    res = m.run(shots_from([3.0, 2.8, 2.6, 2.4, 2.2, 2.0, 1.8, 1.6, 1.4, 1.2, 1.0]))
    assert res["trend_s_per_min"] < 0
    assert res["thirds"][2]["cut_rate_per_min"] > res["thirds"][0]["cut_rate_per_min"]
    hook = m.run(shots_from([0.4, 0.5, 0.6, 3.0, 3.0, 3.0]))
    assert hook["hook_cuts_first_3s"] == 3


def test_explicit_duration_sets_the_rate():
    res = m.run(shots_from([5.0, 5.0]), duration_s=60.0)
    assert res["cut_rate_per_min"] == pytest.approx(1.0)


def test_empty_and_invalid():
    assert m.run([])["count"] == 0
    with pytest.raises(ValueError):
        m.run([{"start_s": 2, "end_s": 1}])


def test_cli_reads_detect_shots_json(tmp_path, capsys):
    p = tmp_path / "shots.json"
    p.write_text(json.dumps({"duration_s": 6.0, "shots": shots_from([1.5, 1.5, 3.0])}))
    assert m.main([str(p)]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["count"] == 3 and out["cut_rate_per_min"] == pytest.approx(20.0)
