import pytest
from PIL import Image

from storyboard_grid_exporter import contact_sheet, extract_argv, fmt_time, timestamps_for


def frames(n, size=(108, 192)):
    return [Image.new("RGB", size, (40 * i % 255, 120, 200)) for i in range(n)]


def test_layout_size():
    sheet = contact_sheet(frames(5), times=[0, 1, 2, 3, 4], notes=list("abcde"), cols=3, cell_w=90, gap=10,
                          caption_h=30, title="Demo")
    cell_h = 160
    assert sheet.size == (3 * 90 + 4 * 10, 48 + 2 * (cell_h + 30) + 3 * 10)
    assert sheet.getpixel((10 + 45, 48 + 10 + 80)) == (0, 120, 200)


def test_helpers():
    assert fmt_time(65.5) == "01:05.50"
    assert timestamps_for(60, 4) == [0, 15, 30, 45]
    assert timestamps_for(60, 2, include_first=False) == [15, 45]
    assert extract_argv("v.mp4", 1.5, "f.png")[4] == "1.500"


def test_validation():
    with pytest.raises(ValueError):
        contact_sheet([])
    with pytest.raises(ValueError):
        contact_sheet(frames(2), times=[0])
    with pytest.raises(ValueError):
        timestamps_for(0, 3)
