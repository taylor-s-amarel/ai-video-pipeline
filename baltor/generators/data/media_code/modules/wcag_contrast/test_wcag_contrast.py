import pytest

from wcag_contrast import best_text_color, contrast_ratio, grade, min_backing_opacity, parse, relative_luminance


def test_reference_values():
    assert contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0)
    assert contrast_ratio("#777777", "#FFFFFF") == pytest.approx(4.48, abs=0.01)
    assert relative_luminance("#FFFFFF") == pytest.approx(1.0)
    assert contrast_ratio("#FFD21F", "#000") == pytest.approx(contrast_ratio("#000000", "#FFD21F"))


def test_grade():
    g = grade(4.6)
    assert g["AA_normal"] and not g["AAA_normal"] and g["AAA_large"]


def test_best_text_over_mixed_backgrounds():
    c, worst = best_text_color(["#87CEEB", "#F5F5DC"], ["#FFFFFF", "#000000", "#FFD21F"])
    assert c == "#000000" and worst > 10


def test_min_backing_opacity():
    a = min_backing_opacity("#FFD21F", "#101418", ["#87CEEB", "#F5F5DC", "#FFFFFF"], target=4.5)
    assert a is not None and 0.4 < a < 0.8
    from wcag_contrast import mix
    assert contrast_ratio("#FFD21F", mix("#101418", "#FFFFFF", a)) >= 4.5
    assert min_backing_opacity("#FFFFFF", "#FFFFFF", ["#FFFFFF"]) is None


def test_parse_forms():
    assert parse("#fff") == (1.0, 1.0, 1.0)
    assert parse((255, 0, 0)) == (1.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        parse("#12345")
