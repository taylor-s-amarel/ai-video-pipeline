import shutil

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import video_re_synth as synth
import video_re_text_regions as m

W, H = 360, 640


def font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        pytest.skip("Pillow without scalable default font")


def background(kind="gradient"):
    yy, xx = np.mgrid[0:H, 0:W]
    if kind == "gradient":
        base = np.stack([40 + 60 * yy / H, 60 + 40 * xx / W, 120 + 0 * xx], -1)
        return Image.fromarray(base.clip(0, 255).astype(np.uint8))
    return Image.fromarray(synth.texture(W, H, 1)).filter(ImageFilter.GaussianBlur(3))


def draw(img, texts):
    d = ImageDraw.Draw(img)
    boxes = []
    for txt, size, y in texts:
        f = font(size)
        bb = d.textbbox((0, 0), txt, font=f)
        x = (W - (bb[2] - bb[0])) // 2
        d.text((x, y), txt, font=f, fill=(255, 210, 31))
        x0, y0, x1, y1 = d.textbbox((x, y), txt, font=f)
        boxes.append([x0, y0, x1 - x0, y1 - y0])
    return img, boxes


def best_iou(box, regions):
    return max((m.iou(box, r["bbox"]) for r in regions), default=0.0)


@pytest.mark.parametrize("kind", ["gradient", "photo"])
def test_title_and_caption_lines_are_found(kind):
    img, boxes = draw(background(kind), [("FACT 1", 44, 90), ("She lived underwater", 22, 480), ("for 14 days", 22, 510)])
    regions = m.detect_in_frame(np.asarray(img).mean(axis=2))
    assert len(regions) == 3
    for b in boxes:
        assert best_iou(b, regions) >= 0.5, (b, regions)


def test_no_text_no_regions_on_plain_textures_and_shapes():
    yy, xx = np.mgrid[0:H, 0:W]
    grid = np.full((H, W), 60.0)
    grid[::40, :] = 200
    grid[:, ::40] = 200
    bokeh = Image.new("L", (W, H), 30)
    d = ImageDraw.Draw(bokeh)
    rng = np.random.default_rng(1)
    for _ in range(60):
        x, y, r = rng.integers(0, W), rng.integers(0, H), rng.integers(5, 30)
        d.ellipse((x - r, y - r, x + r, y + r), fill=int(rng.integers(80, 255)))
    for frame in (np.asarray(background("gradient")).mean(axis=2), np.asarray(background("photo")).mean(axis=2),
                  grid, ((xx // 8 + yy // 8) % 2 * 150 + 50).astype(float), np.asarray(bokeh).astype(float)):
        assert m.detect_in_frame(frame) == []


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_video_tracks_show_when_title_and_caption_are_on_screen(tmp_path):
    title_img, title_boxes = draw(background(), [("FACT 1", 44, 90)])
    both_img, _ = draw(title_img.copy(), [("for 14 days", 26, 500)])
    cap_img, _ = draw(background(), [("for 14 days", 26, 500)])
    frames = [np.asarray(title_img)] * 10 + [np.asarray(both_img)] * 5 + [np.asarray(cap_img)] * 15  # 10 fps
    p = synth.encode_frames(tmp_path / "t.mp4", frames, 10, (W, H))
    res = m.run(str(p), sample_fps=2.0)
    assert res["status"] == "ok"
    tracks = sorted(res["tracks"], key=lambda t: t["y_center_ratio"])
    assert len(tracks) == 2
    title, caption = tracks
    assert title["start_s"] == 0.0 and title["end_s"] == pytest.approx(1.5, abs=0.01)
    assert caption["start_s"] == pytest.approx(1.0, abs=0.01) and caption["end_s"] == pytest.approx(3.0, abs=0.01)
    assert title["y_center_ratio"] < 0.3 < 0.7 < caption["y_center_ratio"]
    assert m.iou(title["bbox"], title_boxes[0]) > 0.5
    for r in res["regions"]:
        assert 0 < r["area_ratio"] < 0.2 and set(r) >= {"t_s", "bbox", "area_ratio", "y_center_ratio"}
    assert res["summary"]["text_presence_ratio"] == 1.0


def test_merge_words_joins_same_line_only():
    boxes = [(10, 0, 20, 30), (11, 34, 20, 40), (40, 0, 45, 30)]
    assert sorted(m.merge_words(boxes)) == [(10, 0, 20, 40), (40, 0, 45, 30)]
