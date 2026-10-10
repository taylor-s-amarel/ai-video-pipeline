import shutil
import subprocess

import numpy as np
import pytest

from asc_cdl_grade import CDL, apply, ffmpeg_lutrgb, from_cc_xml, to_cc_xml


def test_identity_and_formula():
    img = np.random.default_rng(0).integers(0, 256, (8, 8, 3)).astype(np.uint8)
    assert np.array_equal(apply(img, CDL()), img)
    c = apply(np.array([[[0.5, 0.5, 0.5]]]), CDL(slope=(2, 1, 1), offset=(0, 0.1, 0), power=(1, 1, 2)))
    assert c[0, 0].tolist() == pytest.approx([1.0, 0.6, 0.25])


def test_saturation_zero_is_grey():
    out = apply(np.array([[[0.9, 0.2, 0.1]]]), CDL(saturation=0))
    assert out[0, 0, 0] == pytest.approx(out[0, 0, 1]) == pytest.approx(out[0, 0, 2])


def test_xml_roundtrip_and_validation():
    cdl = CDL((1.05, 1.0, 0.95), (0.0, 0.0, 0.01), (1.0, 1.0, 1.05), 1.1, "shot42")
    back = from_cc_xml(to_cc_xml(cdl))
    assert back.slope == pytest.approx(cdl.slope) and back.saturation == pytest.approx(1.1) and back.id == "shot42"
    with pytest.raises(ValueError):
        apply(np.zeros((1, 1, 3)), CDL(power=(0, 1, 1)))


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_lutrgb_matches_numpy():
    cdl = CDL(slope=(1.2, 1.0, 0.8), offset=(0.02, 0, 0), power=(1.1, 1, 0.9))
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=0x808080:s=4x4:d=0.1:r=10",
                        "-vf", "format=rgb24," + ffmpeg_lutrgb(cdl), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                       capture_output=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    got = np.frombuffer(r.stdout, np.uint8)[:3].astype(int)
    want = apply(np.array([[[128, 128, 128]]], np.uint8), CDL(cdl.slope, cdl.offset, cdl.power))[0, 0].astype(int)
    assert np.abs(got - want).max() <= 2
