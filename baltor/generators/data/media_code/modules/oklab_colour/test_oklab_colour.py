import pytest

from oklab_colour import delta_e, hex_to_oklch, oklab_to_srgb, oklch_to_hex, ramp, rotate_hue, srgb_to_oklab


def test_reference_points():
    L, a, b = srgb_to_oklab([1, 1, 1])
    assert L == pytest.approx(1.0, abs=1e-4) and abs(a) < 1e-4 and abs(b) < 1e-4
    assert srgb_to_oklab([0, 0, 0])[0] == pytest.approx(0, abs=1e-9)


@pytest.mark.parametrize("hexcol", ["#FFD21F", "#0E1116", "#87CEEB", "#E63946", "#2A9D8F"])
def test_roundtrip(hexcol):
    L, C, h = hex_to_oklch(hexcol)
    assert oklch_to_hex(L, C, h) == hexcol


def test_ramp_monotonic_and_gamut():
    r = ramp("#FFD21F", 7)
    Ls = [hex_to_oklch(c)[0] for c in r]
    assert all(a > b for a, b in zip(Ls, Ls[1:]))
    assert all(len(c) == 7 for c in r)
    rgb = oklab_to_srgb((0.95, 0.4, 0.0), clip=True)
    assert all(0 <= c <= 1 for c in rgb)


def test_rotate_and_delta():
    comp = rotate_hue("#FFD21F", 180)
    assert delta_e(comp, "#FFD21F") > 0.1
    assert delta_e("#FFD21F", "#FFD21F") == 0
    assert rotate_hue("#FFD21F", 360) == "#FFD21F"
