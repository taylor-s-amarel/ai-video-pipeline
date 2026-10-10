import pytest

from edl_cmx3600_writer import Event, read_edl, write_edl


def test_write_and_read():
    text = write_edl("DEMO", [Event("A001", 0.0, 4.0, clip="intro.mp4"),
                             Event("A002", 2.0, 7.5, transition="D", dissolve_frames=15)], fps=30)
    assert text.startswith("TITLE: DEMO\nFCM: NON-DROP FRAME\n")
    ev = read_edl(text)
    assert len(ev) == 2 and ev[0]["clip"] == "intro.mp4"
    assert ev[0]["rec_in"] == "00:00:00:00" and ev[0]["rec_out"] == "00:00:04:00"
    assert ev[1]["src_in"] == "00:00:02:00" and ev[1]["rec_out"] == "00:00:09:15"
    assert ev[1]["transition"] == "D" and ev[1]["dissolve_frames"] == 15


def test_drop_frame():
    text = write_edl("NTSC", [Event("R1", 0, 60.06)], fps=30000 / 1001)
    assert "DROP FRAME" in text.splitlines()[1] and "00:01:00;02" in text


@pytest.mark.parametrize("ev", [Event("A", 2, 1), Event("TOO_LONG_REEL", 0, 1), Event("A", 0, 1, track="X"),
                                Event("A", 0, 1, transition="W")])
def test_validation(ev):
    with pytest.raises(ValueError):
        write_edl("x", [ev])
