import pytest

from colour_harmony import accent_for, contrast, scheme


def test_complementary_of_red():
    assert scheme("#FF0000", "complementary") == ["#FF0000", "#00FFFF"]
    assert scheme("#FF0000", "triadic") == ["#FF0000", "#00FF00", "#0000FF"]


def test_sizes_and_base_first():
    for kind, n in (("analogous", 3), ("split_complementary", 3), ("tetradic", 4), ("square", 4)):
        s = scheme("#FFD21F", kind)
        assert len(s) == n and s[0] == "#FFD21F"
    assert scheme("#FFD21F", "monochrome")[0] == "#FFD21F"


def test_accent_and_errors():
    best, ratio = accent_for("#0E1116", ["#FFD21F", "#1F4CFF"])
    assert best == "#FFD21F" and ratio > 7
    assert contrast("#FFFFFF", "#000000") == pytest.approx(21)
    with pytest.raises(ValueError):
        scheme("#FFD21F", "rainbow")
    with pytest.raises(ValueError):
        scheme("#FFF", "triadic")
