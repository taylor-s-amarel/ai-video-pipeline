import json

import pytest

from platform_safe_areas import PROFILES, caption_band, check_box, load_profiles, safe_rect


def test_safe_rect():
    x, y, w, h = safe_rect((1080, 1920))
    assert (x, y) == (65, 230) and x + w == 950 and y + h == 1498


def test_check_box():
    assert check_box((1080, 1920), (90, 300, 800, 260)) == []
    probs = check_box((1080, 1920), (20, 100, 1040, 1800))
    assert len(probs) == 4


def test_caption_band_clamped():
    x, y, w, h = caption_band((1080, 1920), 120, position=0.95)
    assert y + h <= 1498 and h == 120


def test_custom_profiles():
    profs = load_profiles(json.dumps({"my-app": {"top": 0.1, "bottom": 0.3, "left": 0.05, "right": 0.15}}))
    assert "my-app" in profs and "house-9x16-conservative" in profs
    assert safe_rect((1000, 1000), "my-app", profs) == (50, 100, 800, 600)
    with pytest.raises(ValueError):
        load_profiles(json.dumps({"bad": {"top": 0.7, "bottom": 0, "left": 0, "right": 0}}))
    assert all("note" in p for p in PROFILES.values())
