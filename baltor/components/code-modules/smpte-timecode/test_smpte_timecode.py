import pytest

import smpte_timecode as tc

NTSC = 30000 / 1001


def test_non_drop_roundtrip():
    for f in (0, 1, 29, 30, 1799, 1800, 107892, 2589407):
        assert tc.tc_to_frames(tc.frames_to_tc(f, 30), 30) == f
    assert tc.frames_to_tc(90061, 25) == "01:00:02:11"


def test_drop_frame_known_values():
    assert tc.frames_to_tc(1799, NTSC) == "00:00:59;29"
    assert tc.frames_to_tc(1800, NTSC) == "00:01:00;02"
    assert tc.frames_to_tc(17982, NTSC) == "00:10:00;00"
    assert tc.frames_to_tc(107892, NTSC) == "01:00:00;00"


def test_drop_frame_roundtrip():
    for f in range(0, 40000, 37):
        assert tc.tc_to_frames(tc.frames_to_tc(f, NTSC), NTSC) == f


def test_invalid():
    with pytest.raises(ValueError):
        tc.tc_to_frames("00:01:00;00", NTSC)  # dropped label
    with pytest.raises(ValueError):
        tc.tc_to_frames("00:00:00:30", 30)
    with pytest.raises(ValueError):
        tc.frames_to_tc(10, 25, drop=True)


def test_seconds():
    assert tc.seconds_to_frames(60, NTSC) == 1798
    assert tc.frames_to_seconds(30000, NTSC) == pytest.approx(1001.0)
    assert tc.is_drop_rate(NTSC) and not tc.is_drop_rate(25)
