import numpy as np
import pytest

from auto_white_balance import correct, gains


def scene(cast=(1.0, 1.0, 1.0), seed=0):
    rng = np.random.default_rng(seed)
    greys = rng.uniform(0.1, 0.9, (64, 64, 1))
    colour = rng.uniform(0.8, 1.2, (64, 64, 3))  # mild colour variation around neutral
    lin = np.clip(greys * colour * np.array(cast), 0, 1)
    enc = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    return (enc * 255).astype(np.uint8)


@pytest.mark.parametrize("method", ["gray_world", "white_patch", "shades_of_gray"])
def test_removes_warm_cast(method):
    img = scene(cast=(1.25, 1.0, 0.75))
    out = correct(img, method)
    m_in, m_out = img.reshape(-1, 3).mean(0), out.reshape(-1, 3).mean(0)
    assert (m_in[0] - m_in[2]) > 30
    assert abs(m_out[0] - m_out[2]) < (m_in[0] - m_in[2]) / 3


def test_neutral_untouched_and_strength():
    img = scene()
    assert np.abs(gains(img) - 1).max() < 0.1
    warm = scene(cast=(1.3, 1.0, 0.7))
    assert np.array_equal(correct(warm, strength=0.0), warm)
    with pytest.raises(ValueError):
        correct(warm, method="magic")


def test_clamp_and_alpha():
    red = np.zeros((8, 8, 4), np.uint8)
    red[..., 0], red[..., 3] = 200, 128
    g = gains(red[..., :3])
    assert g.max() <= 2.0 and g.min() >= 0.5
    assert correct(red)[..., 3].max() == 128
