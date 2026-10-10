import shutil

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

import video_re_ocr_adapter as m
import video_re_synth as synth

W, H = 360, 640


def test_label_patterns():
    assert m.label_pattern("FACT 3") == "FACT {n}"
    assert m.label_pattern("Fact 12:") == "Fact {n}"
    assert m.label_pattern("#2") == "#{n}"
    assert m.label_pattern("TIP #4") == "TIP #{n}"
    assert m.label_pattern("7") == "{n}"
    assert m.label_pattern("She lived underwater") is None
    assert m.label_number("STEP 10") == 10


def test_masking_keeps_shape_not_words():
    assert m.mask_text("FACT 3: Sylvia spent 14 days down") == "WORD {n}: Word word {n} word word"
    assert m.apply_text_mode("abc", "none") == ""
    with pytest.raises(ValueError):
        m.apply_text_mode("abc", "secret")
    shape = m.text_shape("FOR 14 DAYS")
    assert shape == {"words": 3, "chars": 11, "case": "upper", "has_number": True}


def test_label_summary_lists_numbers_in_order():
    items = [{"t_s": 9.0, "label_pattern": "FACT {n}", "label_number": 2},
             {"t_s": 1.0, "label_pattern": "FACT {n}", "label_number": 1},
             {"t_s": 9.5, "label_pattern": "FACT {n}", "label_number": 2},
             {"t_s": 3.0, "label_pattern": None, "label_number": None}]
    assert m.summarise_labels(items) == {"FACT {n}": {"count": 3, "numbers": [1, 2], "first_t_s": 1.0}}


def test_tesseract_tsv_parsing():
    tsv = ("level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"
           "1\t1\t0\t0\t0\t0\t0\t0\t100\t40\t-1\t\n"
           "5\t1\t1\t1\t1\t1\t5\t5\t40\t30\t96.5\tFACT\n"
           "5\t1\t1\t1\t1\t2\t50\t5\t20\t30\t91.5\t1\n")
    text, conf = m.parse_tesseract_tsv(tsv)
    assert text == "FACT 1" and conf == pytest.approx(0.94)


def test_crop_scales_bbox_to_decoded_frame_and_enlarges():
    frame = np.zeros((320, 180, 3), np.uint8)  # decoded at half of a 360x640 source
    img = m.crop_region(frame, [100, 200, 120, 20], (360, 640))
    assert img.mode == "L" and img.height == 64
    assert img.width == pytest.approx((120 * 1.3 / 2) * 64 / (20 * 1.3 / 2), rel=0.15)


def test_unavailable_without_an_engine(monkeypatch):
    monkeypatch.setattr(m, "engine_available", lambda name: False)
    res = m.run("x.mp4", [{"t_s": 0, "bbox": [0, 0, 10, 10]}])
    assert res["status"] == "unavailable" and "tesseract" in res["reason"]


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_fake_engine_end_to_end_with_masking(tmp_path, monkeypatch):
    img = Image.new("RGB", (W, H), (30, 40, 90))
    d = ImageDraw.Draw(img)
    d.text((100, 90), "FACT 1", font=ImageFont.load_default(size=44), fill=(255, 210, 31))
    p = synth.encode_frames(tmp_path / "v.mp4", [np.asarray(img)] * 10, 10, (W, H))
    seen = []

    def fake(img, engine, allow_download=False):
        seen.append(img.size)
        return "FACT 1", 0.9

    monkeypatch.setattr(m, "engine_available", lambda name: name == "tesseract")
    monkeypatch.setattr(m, "ocr_image", fake)
    regions = [{"t_s": 0.5, "bbox": [100, 95, 140, 40], "score": 0.9}]
    res = m.run(str(p), regions, text_mode="masked")
    assert res["status"] == "ok" and res["engine"] == "tesseract"
    item = res["items"][0]
    assert item["text"] == "WORD {n}" and item["label_pattern"] == "FACT {n}" and item["label_number"] == 1
    assert res["summary"]["label_patterns"]["FACT {n}"]["numbers"] == [1]
    assert seen and seen[0][1] == 64


@pytest.mark.skipif(not m.engine_available("tesseract"), reason="tesseract not installed")
def test_real_tesseract_reads_a_clear_label():
    img = Image.new("L", (300, 80), 255)
    ImageDraw.Draw(img).text((10, 10), "FACT 1", font=ImageFont.load_default(size=48), fill=0)
    text, conf = m.ocr_image(img, "tesseract")
    assert "FACT" in text.upper()
