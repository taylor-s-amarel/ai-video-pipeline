import pytest

import ken_burns_path as kb


def test_base_crop_aspect():
    w, h = kb.base_crop((4000, 3000), (1080, 1920))
    assert w / h == pytest.approx(1080 / 1920)
    assert h == 3000


@pytest.mark.parametrize("name", kb.PRESETS)
def test_rects_stay_inside_and_keep_aspect(name):
    start, end = kb.preset(name, focus=(0.2, 0.8), strength=1.3)
    for x, y, w, h in kb.plan((4000, 3000), (1080, 1920), start, end, 60):
        assert x >= -1e-9 and y >= -1e-9 and x + w <= 4000 + 1e-9 and y + h <= 3000 + 1e-9
        assert w / h == pytest.approx(1080 / 1920)


def test_zoom_in_shrinks_crop_monotonically():
    s, e = kb.preset("zoom_in", strength=1.5)
    widths = [r[2] for r in kb.plan((3000, 3000), (1080, 1920), s, e, 30)]
    assert widths[0] > widths[-1]
    assert all(b <= a + 1e-9 for a, b in zip(widths, widths[1:]))
    assert widths[0] / widths[-1] == pytest.approx(1.5)


def test_pan_moves_x():
    s, e = kb.preset("pan_right", strength=1.2)
    rects = kb.plan((4000, 3000), (1920, 1080), s, e, 10)
    assert rects[-1][0] > rects[0][0]


def test_errors_and_upscale_ratio():
    with pytest.raises(ValueError):
        kb.view_rect((100, 100), (10, 10), (0.5, 0.5, 0.5))
    with pytest.raises(KeyError):
        kb.preset("spin")
    rects = kb.plan((1080, 1920), (1080, 1920), (0.5, 0.5, 1), (0.5, 0.5, 2), 5)
    assert kb.min_source_scale(rects, (1080, 1920)) == pytest.approx(0.5)
