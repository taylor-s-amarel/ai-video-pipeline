import shutil
import subprocess

import numpy as np
import pytest

from frosted_glass_filter import frosted_glass, rounded_alpha_expr


def test_graph_text_and_rules():
    g, out = frosted_glass(box=(10, 20, 101, 51), tint_opacity=0.6)
    assert out == "[glassed]" and "crop=100:50:10:20" in g and "gblur=sigma=16" in g
    assert "0x0E1116@0.6" in g and g.endswith("overlay=10:20:format=auto[glassed]")
    with pytest.raises(ValueError, match="0.55-0.75"):
        frosted_glass(tint_opacity=0.9)
    frosted_glass(tint_opacity=0.9, allow_any_tint=True)
    with pytest.raises(ValueError):
        frosted_glass(panel_opacity=1.0)
    with pytest.raises(ValueError):
        frosted_glass(blur="median")


def eval_alpha(expr, X, Y, W, H):
    py = expr.replace("hypot", "np.hypot").replace("abs", "np.abs").replace("max(", "np.maximum(") \
        .replace("min(", "np.minimum(").replace("clip(", "np.clip(")
    return eval(py, {"np": np, "X": X, "Y": Y, "W": W, "H": H})


def test_alpha_expression_shape():
    expr = rounded_alpha_expr(10, 8)
    ys, xs = np.mgrid[0:60, 0:100].astype(float)
    a = eval_alpha(expr, xs, ys, 100, 60)
    assert a[30, 50] == pytest.approx(255 * 0.98)
    assert a[0, 0] == 0 and 0 < a[30, 2] < a[30, 10]


def frames(argv, w, h):
    r = subprocess.run(argv, capture_output=True, timeout=120, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stderr.decode()
    return np.frombuffer(r.stdout, np.uint8).reshape(-1, h, w)


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_glass_blurs_and_tints_region():
    g, out = frosted_glass("[0:v]", box=(40, 30, 160, 80), sigma=8, tint="#000000", tint_opacity=0.6,
                           radius=12, feather=10)
    base = ["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc2=s=240x140:d=0.1:r=10"]
    glass = frames(base + ["-filter_complex", g + f";{out}format=gray[o]", "-map", "[o]", "-frames:v", "1",
                           "-f", "rawvideo", "-"], 240, 140)[0].astype(float)
    orig = frames(base + ["-vf", "format=gray", "-frames:v", "1", "-f", "rawvideo", "-"], 240, 140)[0].astype(float)
    inner = (slice(50, 90), slice(70, 170))
    assert glass[inner].std() < orig[inner].std() * 0.7      # blurred
    assert glass[inner].mean() < orig[inner].mean()          # darkened by tint
    assert np.abs(glass[0:20, :] - orig[0:20, :]).mean() < 1.0  # outside untouched (format conversion only)
