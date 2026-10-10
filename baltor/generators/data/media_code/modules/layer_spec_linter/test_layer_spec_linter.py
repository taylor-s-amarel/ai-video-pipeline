import copy

from layer_spec_linter import lint


def scene(start, end):
    return {"start_s": start, "end_s": end, "layers": [
        {"kind": "background-video", "source": "waves", "opacity": 0.92, "motion": "loop"},
        {"kind": "grid-2x2", "source": "grid", "opacity": 0.35},
        {"kind": "light", "source": "sweep", "opacity": 0.4},
        {"kind": "particles", "source": "dust", "opacity": 0.3},
        {"kind": "photo", "source": "p.jpg", "opacity": 0.98, "feather_px": 48}]}


GOOD = {"scenes": [scene(0, 16), scene(16, 32), scene(32, 48), scene(48, 64)]}


def rules(spec):
    return {f["rule"] for f in lint(spec)}


def test_good_spec_passes():
    assert lint(GOOD) == []


def test_each_rule():
    bad = copy.deepcopy(GOOD)
    bad["scenes"][0]["layers"][4]["opacity"] = 1.0
    bad["scenes"][0]["layers"][4]["feather_px"] = 0
    bad["scenes"][1]["layers"] = bad["scenes"][1]["layers"][4:]
    bad["scenes"][2]["start_s"] = 33
    bad["scenes"][3]["layers"].append({"kind": "progress-bar", "source": "bar", "opacity": 0.5})
    bad["scenes"][3]["end_s"] = 50
    assert rules(bad) == {"opacity_cap", "feathered_edges", "min_layers", "moving_background", "contiguous",
                          "forbidden_layer", "min_duration"}


def test_empty():
    assert rules({}) == {"scenes"}
