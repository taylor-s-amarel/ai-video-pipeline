import pytest

from text_area_budget import _union_area, audit


def test_union_area_no_double_count():
    assert _union_area([(0, 0, 10, 10), (5, 5, 10, 10)]) == 175
    assert _union_area([(0, 0, 10, 10), (0, 0, 10, 10)]) == 100
    assert _union_area([]) == 0


def test_audit_flags_busy_moment():
    boxes = [{"name": "title", "rect": (90, 300, 900, 260), "start": 0, "end": 2.5},
             {"name": "caption", "rect": (60, 1400, 960, 120), "start": 0.5, "end": 3},
             {"name": "label", "rect": (60, 200, 400, 100), "start": 1, "end": 2},
             {"name": "sticker", "rect": (600, 700, 400, 400), "start": 1, "end": 2}]
    r = audit((1080, 1920), boxes)
    assert not r["passed"]
    busy = [m for m in r["moments"] if m["issues"]]
    assert busy[0]["start"] == 1 and len(busy[0]["elements"]) == 4


def test_audit_passes_clean():
    r = audit((1080, 1920), [{"name": "caption", "rect": (60, 1400, 960, 120), "start": 0, "end": 3}])
    assert r["passed"] and r["peak_fraction"] == pytest.approx(960 * 120 / (1080 * 1920), abs=1e-4)
