import numpy as np
import pytest

from palette_extractor import extract


def blocks():
    img = np.zeros((60, 100, 3), np.uint8)
    img[:, :50] = (30, 58, 95)       # 50%
    img[:, 50:80] = (255, 210, 31)   # 30%
    img[:, 80:] = (240, 240, 240)    # 20%
    return img


@pytest.mark.parametrize("perceptual", [True, False])
def test_recovers_block_colours(perceptual):
    pal = extract(blocks(), k=3, perceptual=perceptual)
    assert [p["hex"] for p in pal] == ["#1E3A5F", "#FFD21F", "#F0F0F0"]
    assert [p["share"] for p in pal] == pytest.approx([0.5, 0.3, 0.2], abs=0.01)


def test_deterministic_and_small_k():
    rng = np.random.default_rng(0)
    img = rng.integers(0, 255, (40, 40, 3)).astype(np.uint8)
    assert extract(img, 4, seed=1) == extract(img, 4, seed=1)
    assert len(extract(np.zeros((5, 5, 3), np.uint8), k=4)) == 1
    with pytest.raises(ValueError):
        extract(img, 0)
