import os
import shutil

import pytest

from font_file_finder import find_font, list_fonts

DEJAVU = "/usr/share/fonts/truetype/dejavu"


def test_custom_root_and_names(tmp_path):
    if not os.path.isdir(DEJAVU):
        pytest.skip("DejaVu fonts not installed")
    shutil.copy(os.path.join(DEJAVU, "DejaVuSans-Bold.ttf"), tmp_path / "a.ttf")
    (tmp_path / "notes.txt").write_text("not a font")
    (tmp_path / "broken.ttf").write_bytes(b"nope")
    fonts = list_fonts([str(tmp_path)])
    assert len(fonts) == 1 and fonts[0]["family"] == "DejaVu Sans" and fonts[0]["style"] == "Bold"
    assert find_font("DejaVu Sans", "Bold", roots=[str(tmp_path)], use_fc_match=False).endswith("a.ttf")


def test_fallback_chain(tmp_path):
    if not os.path.isdir(DEJAVU):
        pytest.skip("DejaVu fonts not installed")
    shutil.copy(os.path.join(DEJAVU, "DejaVuSans.ttf"), tmp_path / "b.ttf")
    p = find_font("Inter", "Black", fallbacks=[("DejaVu Sans", "Book")], roots=[str(tmp_path)], use_fc_match=False)
    assert p and p.endswith("b.ttf")
    assert find_font("Nope", "Bold", roots=[str(tmp_path)], use_fc_match=False) is None
