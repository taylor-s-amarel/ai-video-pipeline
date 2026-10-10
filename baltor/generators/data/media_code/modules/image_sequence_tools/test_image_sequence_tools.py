import pytest

from image_sequence_tools import ffmpeg_input, frame_name, gaps, group, parse, pattern


def test_parse_and_group():
    assert parse("frame_00012.png") == ("frame_", 12, 5, ".png")
    assert parse("notes.txt") is None
    seqs = group(["frame_00001.png", "frame_00002.png", "frame_00004.png", "bg_001.jpg", "readme.md"])
    assert seqs == {"frame_%05d.png": [1, 2, 4], "bg_%03d.jpg": [1]}
    assert pattern("50%_", 3, ".png") == "50%%_%03d.png"


def test_gaps_and_input():
    assert gaps([1, 2, 4, 5, 9]) == [(3, 3), (6, 8)]
    assert ffmpeg_input("f/frame_%05d.png", [10, 11, 12], 24) == ["-framerate", "24", "-start_number", "10", "-i",
                                                                    "f/frame_%05d.png"]
    with pytest.raises(ValueError):
        ffmpeg_input("x", [1, 3])


def test_frame_name():
    assert frame_name("f_", 7, 4) == "f_0007.png"
    with pytest.raises(ValueError):
        frame_name("f_", 100000, 4)
