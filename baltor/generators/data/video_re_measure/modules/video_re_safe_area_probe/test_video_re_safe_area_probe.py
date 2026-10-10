import json

import pytest

import video_re_safe_area_probe as m

W, H = 1080, 1920


def region(t, x, y, w, h):
    return {"t_s": t, "bbox": [x, y, w, h], "area_ratio": w * h / (W * H), "y_center_ratio": (y + h / 2) / H}


def test_centered_title_passes_and_edge_text_fails():
    regions = [region(0.0, 140, 420, 800, 160),      # title in the upper third: fine
               region(0.5, 940, 1000, 130, 60),      # sits on the right rail
               region(1.0, 100, 1700, 700, 90)]      # bottom UI band
    res = m.run(regions, W, H)
    assert res["profile"] == "vertical_ui_conservative" and "assumption" in res["basis"]
    zones = sorted(v["zone"] for v in res["violations"])
    assert zones == ["bottom-ui", "right-rail"]
    assert res["summary"]["share_of_text_samples"] == pytest.approx(2 / 3, abs=1e-3)
    assert res["summary"]["first_violation_s"] == 0.5


def test_landscape_uses_margins_and_custom_zones_override():
    res = m.run([region(0, 10, 10, 300, 50)], 1920, 1080)
    assert res["profile"] == "margins_10" and {v["zone"] for v in res["violations"]} == {"margin-top", "margin-left"}
    custom = m.run([region(0, 10, 10, 300, 50)], 1920, 1080, zones=[{"name": "logo", "x0": 0.8, "y0": 0, "x1": 1, "y1": 0.2}])
    assert custom["profile"] == "custom" and custom["violations"] == []


def test_small_overlap_is_tolerated():
    res = m.run([region(0, 140, 1500, 800, 100)], W, H)  # 1500-1600: 1536+ is bottom-ui -> 64% inside
    assert res["violations"][0]["overlap_ratio"] == pytest.approx(0.64)
    res = m.run([region(0, 140, 1440, 800, 100)], W, H)  # only the bottom 4 px are in the zone
    assert res["violations"] == []


def test_cli_with_text_regions_output(tmp_path, capsys):
    p = tmp_path / "tr.json"
    p.write_text(json.dumps({"frame_size": [W, H], "regions": [region(0, 940, 1000, 130, 60)]}))
    assert m.main([str(p)]) == 0
    assert json.loads(capsys.readouterr().out)["summary"]["violations"] == 1
