import math
import shutil
import subprocess

import pytest

import style_kit as k

HAVE_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None
needs_ffmpeg = pytest.mark.skipif(not HAVE_FFMPEG, reason="ffmpeg/ffprobe not installed")


# ----------------------------------------------------------------- contrast

def test_black_white_is_21():
    assert k.contrast_ratio("#FFFFFF", "#000000") == pytest.approx(21.0)
    assert k.contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21.0)


def test_known_grey_thresholds():
    # #767676 is the lightest grey that passes 4.5:1 on white; #777777 just fails
    assert k.contrast_ratio("#767676", "#FFFFFF") >= 4.5
    assert k.contrast_ratio("#777777", "#FFFFFF") < 4.5


def test_house_yellow_on_black():
    assert k.contrast_ratio("#FFD21F", "#000000") == pytest.approx(14.49, abs=0.05)


def test_hex_round_trip_and_validation():
    assert k.rgb_to_hex(k.hex_to_rgb("#0b1220")) == "#0B1220"
    with pytest.raises(ValueError):
        k.hex_to_rgb("FFD21F")


def test_panel_worst_case_is_over_white_for_light_text():
    r = k.panel_contrast("#FFFFFF", "#000000", 0.6)
    assert r["panel_light"] == "#666666"
    assert r["worst"] == pytest.approx(5.74, abs=0.01)
    assert r["over_black"] == pytest.approx(21.0 * 1.0, abs=0.01)


def test_panel_worst_case_collapses_when_text_luminance_is_inside_range():
    r = k.panel_contrast("#808080", "#000000", 0.3)
    assert r["worst"] == 1.0


def test_required_ratio_and_levels():
    assert k.required_ratio(64, 800) == 3.0
    assert k.required_ratio(64, 400) == 4.5
    assert k.required_ratio(20, 700) == 4.5
    assert k.wcag_level(7.2, 16) == "AAA"
    assert k.wcag_level(4.6, 16) == "AA"
    assert k.wcag_level(3.2, 30, 700) == "AA"
    assert k.wcag_level(3.2, 16) == "fail"
    assert k.is_large_text(19, 700) and not k.is_large_text(19, 400)


# ----------------------------------------------------------------- easing and springs

NAMES = ["linear", "ease-in", "ease-out", "ease-in-out", "sine-in-out", "ease-out-back", "ease-out-elastic", "step"]


@pytest.mark.parametrize("name", NAMES)
def test_easing_endpoints(name):
    assert k.ease(name, 0.0) == pytest.approx(0.0, abs=1e-9)
    assert k.ease(name, 1.0) == pytest.approx(1.0, abs=1e-9)


def test_back_overshoots():
    assert max(k.ease("ease-out-back", i / 100) for i in range(101)) > 1.05


def _eval_ffmpeg_expr(expr, s):
    py = expr.replace("if(", "iff(").replace("PI", "pi")
    env = {"pow": pow, "cos": math.cos, "pi": math.pi, "lt": lambda a, b: float(a < b),
           "gte": lambda a, b: float(a >= b), "iff": lambda c, a, b: a if c else b}
    return eval(py, env, {"s": s})  # expressions come from this module, not from users


@pytest.mark.parametrize("name", ["linear", "ease-in", "ease-out", "ease-in-out", "sine-in-out", "ease-out-back"])
def test_ffmpeg_expressions_match_python_curves(name):
    expr = k.ease_expr(name, "s")
    for i in range(0, 11):
        s = i / 10
        assert _eval_ffmpeg_expr(expr, s) == pytest.approx(k.ease(name, s), abs=1e-6)


def test_cubic_bezier_linear_and_standard():
    lin = k.cubic_bezier(0, 0, 1, 1)
    for t in (0.1, 0.5, 0.9):
        assert lin(t) == pytest.approx(t, abs=1e-5)
    std = k.cubic_bezier(0.25, 0.1, 0.25, 1.0)
    vals = [std(i / 20) for i in range(21)]
    assert vals[0] == pytest.approx(0) and vals[-1] == pytest.approx(1)
    assert all(b >= a - 1e-9 for a, b in zip(vals, vals[1:]))


def test_spring_underdamped_overshoots_and_settles():
    m = k.spring_metrics(300, 18)
    assert 0.45 < m["damping_ratio"] < 0.6
    assert 1.10 < m["peak"] < 1.20
    assert 0.15 < m["peak_time_s"] < 0.3
    assert m["settle_time_s"] < 0.6
    assert k.spring(3.0, 300, 18) == pytest.approx(1.0, abs=1e-3)


def test_spring_critical_and_overdamped_do_not_overshoot():
    for damping in (2 * math.sqrt(300), 60):
        assert max(k.spring(i / 1000, 300, damping) for i in range(1, 3000)) <= 1.0 + 1e-9


def test_keyframes_and_text_animation():
    kf = [{"t": 0, "scale": 1.0}, {"t": 0.4, "scale": 1.12, "ease": "ease-out"}, {"t": 1, "scale": 1.0, "ease": "ease-in-out"}]
    assert k.keyframe_value(kf, 0.4, "scale") == pytest.approx(1.12)
    assert k.keyframe_value(kf, 1.0, "scale") == pytest.approx(1.0)
    anim = {"unit": "word", "duration_ms": 300, "stagger_ms": 100,
            "keyframes": [{"t": 0, "opacity": 0.0}, {"t": 1, "opacity": 1.0}]}
    st = k.text_anim_state(anim, 150, 4)
    assert st[0]["visible"] and not st[3]["visible"]
    assert st[0]["opacity"] == pytest.approx(0.5)
    pop = {"unit": "word", "spring": {"stiffness": 300, "damping": 18}, "from": {"scale": 0.0, "opacity": 0.0},
           "to": {"scale": 1.0, "opacity": 1.0}}
    peak = max(k.text_anim_state(pop, t, 1)[0]["scale"] for t in range(0, 600, 5))
    assert peak > 1.1


# ----------------------------------------------------------------- camera moves

MOVE = {"duration_s": 4, "zoom": {"from": 1.0, "to": 1.2}, "center": {"from": [0.5, 0.5], "to": [0.5, 0.33]},
        "easing": "ease-in-out"}


def test_camera_state_endpoints():
    a, b = k.camera_state(MOVE, 0), k.camera_state(MOVE, 4)
    assert a["zoom"] == pytest.approx(1.0) and b["zoom"] == pytest.approx(1.2)
    assert b["cy"] == pytest.approx(0.33)


def test_zoompan_filter_text():
    f = k.zoompan_filter(MOVE, 540, 960, fps=30)
    assert "zoompan=" in f and "d=120" in f and "s=540x960" in f and "crop=2160:3840" in f


def test_punch_in_keyframes():
    punch = {"duration_s": 1.0, "zoom": {"from": 1, "to": 1}, "center": {"from": [0.5, 0.5], "to": [0.5, 0.5]},
             "zoom_keyframes": [{"t": 0, "zoom": 1.0}, {"t": 0.08, "zoom": 1.15, "ease": "ease-out"},
                                {"t": 1, "zoom": 1.1, "ease": "ease-in-out"}]}
    assert k.camera_state(punch, 0.08)["zoom"] == pytest.approx(1.15)
    assert "if(lt(" in k.zoompan_filter(punch, 270, 480)


@needs_ffmpeg
def test_zoompan_renders(tmp_path):
    src = tmp_path / "photo.png"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=800x600:d=1", "-frames:v", "1", str(src)],
                   check=True)
    out = tmp_path / "kb.mp4"
    move = dict(MOVE, duration_s=0.5)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf", k.zoompan_filter(move, 180, 320, fps=30, prescale=2),
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    info = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                           "stream=width,height,nb_read_frames", "-of", "csv=p=0", str(out)],
                          capture_output=True, text=True, check=True).stdout.strip()
    assert info == "180,320,15"


def test_camera_frames_with_pillow():
    Image = pytest.importorskip("PIL.Image")
    img = Image.linear_gradient("L").convert("RGB").resize((400, 300))
    frames = list(k.camera_frames(img, dict(MOVE, duration_s=0.2, rotation_deg={"from": 0, "to": 2}), (90, 160), fps=10))
    assert len(frames) == 2 and frames[0].size == (90, 160)


# ----------------------------------------------------------------- transitions and grids

def test_xfade_offsets_and_total():
    graph, total = k.xfade_chain([3, 3, 3], [{"xfade": "fade", "duration_ms": 500}, {"cut": True}])
    assert "offset=2.500" in graph and "concat=n=2" in graph
    assert total == pytest.approx(8.5)
    with pytest.raises(ValueError):
        k.xfade_chain([1, 1], [{"xfade": "nope", "duration_ms": 200}])
    with pytest.raises(ValueError):
        k.xfade_chain([0.3, 1], [{"xfade": "fade", "duration_ms": 400}])


@needs_ffmpeg
def test_xfade_chain_renders(tmp_path):
    graph, total = k.xfade_chain([1.0, 1.0, 1.0], [{"xfade": "slideup", "duration_ms": 300},
                                                   {"xfade": "fadeblack", "duration_ms": 200}], size=(160, 284))
    out = tmp_path / "x.mp4"
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for c in ("red", "green", "blue"):
        cmd += ["-f", "lavfi", "-i", f"color=c={c}:s=160x284:d=1:r=30"]
    subprocess.run(cmd + ["-filter_complex", graph, "-map", "[v]", str(out)], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
                               capture_output=True, text=True, check=True).stdout)
    assert dur == pytest.approx(total, abs=0.07)


def test_grid_rects_are_even_and_inside():
    rects = k.grid_2x2_rects(1080, 1920, gutter=24, margin=36)
    assert len(rects) == 4
    for x, y, w, h in rects:
        assert w % 2 == 0 and h % 2 == 0 and x + w <= 1080 and y + h <= 1920
    assert rects[1][0] - (rects[0][0] + rects[0][2]) == 24


@needs_ffmpeg
def test_grid_filter_renders(tmp_path):
    grid = {"gutter_px": 8, "feather_px": 6, "corner_radius_px": 6,
            "cells": [{"opacity": 0.5}, {"opacity": 0.5, "mirror": "h"}, {"opacity": 0.4, "reveal_delay_s": 0.3},
                      {"opacity": 0.4, "start_offset_s": 0.2}]}
    g = "[0:v]format=yuv420p[base];" + k.grid_2x2_filter(grid, 180, 320, fps=10) + ";[grid]format=yuv420p[v]"
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=0x101820:s=180x320:d=1:r=10"]
    for _ in range(4):
        cmd += ["-f", "lavfi", "-i", "testsrc2=s=200x200:d=1:r=10"]
    subprocess.run(cmd + ["-filter_complex", g, "-map", "[v]", str(tmp_path / "g.mp4")], check=True)
    with pytest.raises(ValueError):
        k.grid_2x2_filter({"cells": [{"opacity": 1.0}] * 4}, 180, 320)


# ----------------------------------------------------------------- layer stacks

def _stack():
    return {"layers": [
        {"z": 1, "id": "base", "role": "base", "opacity": 0.98, "blend": "normal", "motion": {"type": "drift"}},
        {"z": 2, "id": "waves", "role": "background-video", "opacity": 0.9, "blend": "normal", "motion": {"type": "loop"}},
        {"z": 3, "id": "leak", "role": "light", "opacity": 0.3, "blend": "screen", "motion": {"type": "drift"}},
        {"z": 4, "id": "grain", "role": "grain", "opacity": 0.1, "blend": "overlay", "motion": {"type": "loop"}},
        {"z": 5, "id": "photo", "role": "photo", "opacity": 0.98, "blend": "normal", "rect": {"x": 0.08, "y": 0.2, "w": 0.84, "h": 0.5}},
    ]}


def test_layer_stack_problems():
    assert k.layer_stack_problems(_stack()) == []
    bad = _stack()
    bad["layers"][1]["opacity"] = 1.0
    bad["layers"][4]["rect"]["w"] = 0.6
    probs = k.layer_stack_problems(bad)
    assert any("opacity 1.0" in p for p in probs) and any("photo" in p for p in probs)
    still = {"layers": [dict(l, motion={"type": "static"}) for l in _stack()["layers"]]}
    assert "no moving background layer" in k.layer_stack_problems(still)


def test_layer_stack_filter_refuses_opaque_layers():
    layers = [{"input": 0, "opacity": 0.98, "blend": "normal"}, {"input": 1, "opacity": 0.99, "blend": "screen"}]
    with pytest.raises(ValueError):
        k.layer_stack_filter(layers, 64, 64)


@needs_ffmpeg
def test_layer_stack_blend_math(tmp_path):
    # base grey 64 at 0.98 over black -> 62.72; screen 192 at 0.5 -> 62.72 + (screen - 62.72) * 0.5
    layers = [{"input": 0, "opacity": 0.98, "blend": "normal"}, {"input": 1, "opacity": 0.5, "blend": "screen"},
              {"input": 2, "opacity": 0.5, "blend": "normal", "rect": {"x": 0.5, "y": 0.5, "w": 0.5, "h": 0.5}}]
    g = k.layer_stack_filter(layers, 64, 64, fps=10) + ";[v]format=rgb24[o]"
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for c in ("0x404040", "0xC0C0C0", "0xFFFFFF"):
        cmd += ["-f", "lavfi", "-i", f"color=c={c}:s=64x64:d=0.2:r=10"]
    raw = subprocess.run(cmd + ["-filter_complex", g, "-map", "[o]", "-frames:v", "1", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    assert len(raw) == 64 * 64 * 3
    base = 64 * 0.98
    screen = 255 - (255 - base) * (255 - 192) / 255
    expected_tl = base + (screen - base) * 0.5
    assert raw[0] == pytest.approx(expected_tl, abs=3)
    centre = raw[(48 * 64 + 48) * 3]
    assert centre == pytest.approx(255 * 0.5 + expected_tl * 0.5, abs=4)


# ----------------------------------------------------------------- layout

def test_safe_rect_and_place_box():
    margins = {"top": 0.1, "bottom": 0.25, "left": 0.06, "right": 0.14}
    assert k.safe_rect(1080, 1920, margins) == (65, 192, 929, 1440)
    x, y = k.place_box(600, 120, 0.9, 1080, 1920, margins)
    assert y + 120 <= 1440
    with pytest.raises(ValueError):
        k.place_box(2000, 100, 0.5, 1080, 1920, margins)


# ----------------------------------------------------------------- Pillow renderers

def test_frosted_panel_darkens_only_inside():
    Image = pytest.importorskip("PIL.Image")
    img = Image.new("RGB", (200, 200), (240, 240, 240))
    out = k.frosted_panel(img, (40, 40, 160, 120), tint="#0B1220", opacity=0.6, blur_px=6, radius_px=10, feather_px=4)
    assert out.getpixel((100, 80))[0] < 120
    assert out.getpixel((5, 5)) == (240, 240, 240)
    with pytest.raises(ValueError):
        k.frosted_panel(img, (0, 0, 10, 10), opacity=1.0)


def test_caption_preview_draws_inside_frame():
    Image = pytest.importorskip("PIL.Image")
    frame = Image.new("RGB", (270, 480), (200, 220, 240))
    style = {"font": {"size_px": 64, "weight": 800}, "fill": "#FFFFFF", "stroke": {"color": "#000000", "width_px": 4},
             "backing": {"type": "frosted-glass", "tint": "#0B1220", "opacity": 0.62, "blur_px": 28, "radius_px": 28,
                         "padding_px": [20, 32], "feather_px": 12},
             "layout": {"center_y_fraction": 0.74},
             "emphasis": {"mode": "keyword-pop", "color": "#FFD21F", "scale_peak": 1.12, "duration_ms": 180},
             "reference_size": [1080, 1920]}
    out = k.render_caption_preview(frame, ["In", "1970,", "five", "divers"], style, keyword_index=1, t_ms=90)
    assert out.size == frame.size
    band = [out.getpixel((x, int(480 * 0.74))) for x in range(0, 270, 5)]
    assert min(p[0] for p in band) < 150
