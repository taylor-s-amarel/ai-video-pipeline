import math
import shutil
import subprocess

import pytest

import text_pop_scale_curve as tp


def eval_expr(expr: str, t: float) -> float:
    py = expr.replace("PI", "math.pi").replace("pow(", "_pow(")
    py = py.replace("if(", "_if(").replace("lt(", "_lt(")
    return eval(py, {"math": math, "_pow": pow, "t": t, "cos": math.cos,
                     "_if": lambda c, a, b: a if c else b, "_lt": lambda a, b: a < b})


def test_shape_hits_peak_and_returns():
    assert tp.pop_scale(0.0) == 1.0
    assert tp.pop_scale(0.072) == pytest.approx(1.12)
    assert tp.pop_scale(0.18) == 1.0
    assert all(1.0 <= v <= 1.12 + 1e-9 for v in tp.pop_frames(240))


def test_spring_rings_below_one_and_lands():
    vals = tp.pop_frames(240, shape="spring")
    assert max(vals) == pytest.approx(1.12, abs=0.002)
    assert min(vals) < 1.0
    assert vals[-1] == 1.0


def test_frame_count():
    assert len(tp.pop_frames(60)) == 12


def test_ffmpeg_expr_matches_python():
    expr = tp.ffmpeg_expr(start_s=2.0, base=1.0)
    for dt in (-0.05, 0.01, 0.05, 0.1, 0.15, 0.3):
        assert eval_expr(expr, 2.0 + dt) == pytest.approx(tp.pop_scale(dt), abs=1e-3)


def test_ass_tags():
    assert tp.ass_tags() == r"{\fscx100\fscy100\t(0,72,0.5,\fscx112\fscy112)\t(72,180,2,\fscx100\fscy100)}"


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_expression_evaluates_in_ffmpeg():
    # overlay x/y are evaluated per frame with the variable t, like drawtext fontsize
    expr = tp.ffmpeg_expr(0.1, base=50)
    graph = f"[0][1]overlay=x='{expr}':y=0"
    r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=200x100:d=0.4:r=25",
                        "-f", "lavfi", "-i", "color=c=blue:s=10x10:d=0.4:r=25", "-filter_complex", graph,
                        "-f", "null", "-"], capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr
