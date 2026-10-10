import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

import showcase_evaluators as ev


@pytest.fixture()
def ctx(tmp_path):
    ws = tmp_path / "ws"
    priv = tmp_path / "private"
    ws.mkdir()
    priv.mkdir()
    return ev.EvalContext(workspace=ws, task_dir=tmp_path, private_dirs=[priv])


def test_resolve_refuses_escapes(ctx):
    with pytest.raises(ValueError):
        ctx.resolve("../secret")
    with pytest.raises(ValueError):
        ctx.resolve("/etc/passwd")
    with pytest.raises(FileNotFoundError):
        ctx.resolve("private:missing.csv")


def test_files_present(ctx):
    (ctx.workspace / "out").mkdir()
    (ctx.workspace / "out" / "a.png").write_bytes(b"x")
    res = ev.run_evaluator("files_present", {"paths": ["out/*.png", "report.md"]}, ctx)
    assert res.value == 0.5 and res.passed is False


def test_pytest_hidden_tests(ctx):
    (ctx.workspace / "solution.py").write_text("def add(a, b):\n    return a + b\n\ndef sub(a, b):\n    return a + b\n")
    tests = ctx.private_dirs[0] / "tests"
    tests.mkdir()
    (tests / "test_solution.py").write_text(
        "from solution import add, sub\n\ndef test_add():\n    assert add(2, 3) == 5\n\n"
        "def test_sub():\n    assert sub(5, 3) == 2\n")
    res = ev.run_evaluator("pytest", {"tests": "private:tests"}, ctx)
    assert res.error is None, res.details
    assert res.value == 0.5 and res.passed is False and res.details["failed"] == 1
    assert not (ctx.workspace / "_hidden_tests").exists()  # the real workspace is untouched


def test_metric_from_file_variants(ctx):
    (ctx.workspace / "m.json").write_text(json.dumps({"scores": {"f1": 0.8125}}))
    (ctx.workspace / "m.csv").write_text("split,score\ntrain,0.9\nholdout,0.71\n")
    (ctx.workspace / "log.txt").write_text("epoch 3 val_auc=0.8842\n")
    assert ev.run_evaluator("metric_from_file", {"file": "m.json", "pointer": "/scores/f1"}, ctx).value == 0.8125
    r = ev.run_evaluator("metric_from_file", {"file": "m.csv", "column": "score", "where": {"split": "holdout"}}, ctx)
    assert r.value == 0.71 and r.details["trust"].startswith("agent-written")
    assert ev.run_evaluator("metric_from_file", {"file": "log.txt", "regex": r"val_auc=([0-9.]+)"}, ctx).value == 0.8842
    cmd = [sys.executable, "-c", "import json; json.dump({'v': 3.5}, open('computed.json', 'w'))"]
    r = ev.run_evaluator("metric_from_file", {"file": "computed.json", "pointer": "/v", "command": cmd}, ctx)
    assert r.value == 3.5 and r.details["trust"].startswith("computed")


def test_f1_clusters_pairs_and_labels(ctx):
    (ctx.private_dirs[0] / "truth.csv").write_text("id,cluster\n1,a\n2,a\n3,b\n4,b\n5,c\n")
    (ctx.workspace / "pred.csv").write_text("id,cluster\n1,x\n2,x\n3,y\n4,z\n5,y\n")
    r = ev.run_evaluator("f1_ground_truth", {"mode": "clusters", "predictions": "pred.csv",
                                             "truth": "private:truth.csv"}, ctx)
    # truth pairs {1-2, 3-4}; predicted {1-2, 3-5}
    assert r.details["tp"] == 1 and r.details["fp"] == 1 and r.details["fn"] == 1
    assert r.value == pytest.approx(0.5)
    (ctx.workspace / "pairs.csv").write_text("a,b\n2,1\n4,3\n")
    r = ev.run_evaluator("f1_ground_truth", {"mode": "pairs", "predictions": "pairs.csv",
                                             "truth": "pairs.csv"}, ctx)
    assert r.value == 1.0
    (ctx.workspace / "lab.csv").write_text("id,label\n1,1\n2,0\n3,1\n")
    (ctx.private_dirs[0] / "lab.csv").write_text("id,label\n1,1\n2,1\n3,1\n")
    r = ev.run_evaluator("f1_ground_truth", {"mode": "labels", "predictions": "lab.csv",
                                             "truth": "private:lab.csv"}, ctx)
    assert r.details["precision"] == 1.0 and r.details["recall"] == pytest.approx(2 / 3)


def test_sklearn_metrics(ctx):
    (ctx.private_dirs[0] / "y.csv").write_text("id,label\n1,1\n2,0\n3,1\n4,0\n")
    (ctx.workspace / "p.csv").write_text("id,prediction\n1,1\n2,0\n3,0\n")
    acc = ev.run_evaluator("sklearn_metric", {"metric": "accuracy", "predictions": "p.csv",
                                              "labels": "private:y.csv"}, ctx)
    assert acc.value == pytest.approx(0.5) and acc.details["missing"] == 1  # missing id 4 counts as wrong
    err = ev.run_evaluator("sklearn_metric", {"metric": "accuracy", "predictions": "p.csv",
                                              "labels": "private:y.csv", "missing": "error"}, ctx)
    assert err.value is None and "no prediction" in err.error
    (ctx.private_dirs[0] / "r.csv").write_text("id,label\na,1.0\nb,2.0\n")
    (ctx.workspace / "r.csv").write_text("id,prediction\na,1.5\nb,2.5\n")
    rmse = ev.run_evaluator("sklearn_metric", {"metric": "rmse", "predictions": "r.csv",
                                               "labels": "private:r.csv"}, ctx)
    assert rmse.value == pytest.approx(0.5)
    (ctx.private_dirs[0] / "k.csv").write_text("id,label\n1,0\n2,1\n3,2\n4,3\n")
    (ctx.workspace / "k.csv").write_text("id,prediction\n1,0\n2,1\n3,2\n4,3\n")
    qwk = ev.run_evaluator("sklearn_metric", {"metric": "quadratic_weighted_kappa", "predictions": "k.csv",
                                              "labels": "private:k.csv"}, ctx)
    assert qwk.value == pytest.approx(1.0)


def test_contrast_maths():
    assert ev.contrast_ratio((0, 0, 0), (255, 255, 255)) == pytest.approx(21.0, rel=1e-3)
    assert ev.contrast_ratio((118, 118, 118), (255, 255, 255)) == pytest.approx(4.54, abs=0.02)


def _poster(path, fg, size=(400, 300)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", size, (255, 255, 255))
    d = ImageDraw.Draw(im)
    for i in range(6):  # fake glyph strokes inside the text box
        d.rectangle([60 + i * 40, 120, 80 + i * 40, 170], fill=fg)
    im.save(path)


def test_image_checks_contrast_safe_area_and_margins(ctx):
    _poster(ctx.workspace / "good.png", (0, 0, 0))
    _poster(ctx.workspace / "bad.png", (200, 200, 200))
    params = {"file": "good.png", "width": 400, "height": 300, "format": "PNG",
              "regions": [{"name": "headline", "box": [50, 110, 300, 180]}],
              "safe_area": {"top": 0.1, "bottom": 0.1, "left": 0.1, "right": 0.1},
              "quiet_margins": {"band": 0.08, "max_edge_density": 0.01}}
    good = ev.run_evaluator("image_checks", params, ctx)
    assert good.error is None and good.passed is True, good.details
    bad = ev.run_evaluator("image_checks", dict(params, file="bad.png"), ctx)
    checks = {c["name"]: c for c in bad.details["checks"]}
    assert checks["contrast:headline"]["passed"] is False
    (ctx.workspace / "layout.json").write_text(json.dumps({"text": [{"name": "edge", "box": [0, 0, 120, 40]}]}))
    lay = ev.run_evaluator("image_checks", {"file": "good.png", "layout": "layout.json",
                                            "safe_area": {"top": 0.1, "left": 0.1, "right": 0.1, "bottom": 0.1}}, ctx)
    assert {c["name"]: c["passed"] for c in lay.details["checks"]}["safe_area:edge"] is False


def test_mp4_checks_from_probe():
    info = {"format": {"duration": "64.2"}, "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920, "avg_frame_rate": "30/1"},
        {"codec_type": "audio", "codec_name": "aac"}]}
    checks = ev.mp4_checks_from_probe(info, {"min_duration": 60, "width": 1080, "height": 1920, "min_fps": 30,
                                             "require_audio": True, "video_codecs": ["h264"]})
    assert all(c["passed"] for c in checks)
    short = ev.mp4_checks_from_probe(dict(info, format={"duration": "6"}), {"min_duration": 60})
    assert not short[0]["passed"]


@pytest.mark.skipif(not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="ffmpeg not installed")
def test_mp4_checks_real_file(ctx):
    out = ctx.workspace / "clip.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=160x284:rate=30:duration=1",
                    "-f", "lavfi", "-i", "sine=frequency=440:duration=1", "-shortest", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", str(out)], check=True, timeout=120)
    res = ev.run_evaluator("mp4_checks", {"file": "clip.mp4", "min_duration": 0.9, "width": 160, "height": 284,
                                          "require_audio": True}, ctx)
    assert res.passed is True, res.details


def make_glb(extra_triangle_count=None) -> bytes:
    positions = struct.pack("<9f", 0, 0, 0, 1, 0, 0, 0, 2, 0)
    doc = {"asset": {"version": "2.0"}, "scenes": [{"nodes": [0]}], "nodes": [{"mesh": 0}],
           "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "material": 0}]}],
           "materials": [{"pbrMetallicRoughness": {"baseColorFactor": [1, 0, 0, 1]}}],
           "buffers": [{"byteLength": len(positions)}],
           "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": len(positions)}],
           "accessors": [{"bufferView": 0, "componentType": 5126, "count": extra_triangle_count or 3, "type": "VEC3",
                          "min": [0, 0, 0], "max": [1, 2, 0]}]}
    js = json.dumps(doc).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    body = struct.pack("<II", len(js), ev.CHUNK_JSON) + js + struct.pack("<II", len(positions), ev.CHUNK_BIN) + positions
    return struct.pack("<4sII", b"glTF", 2, 12 + len(body)) + body


def test_gltf_checks(ctx):
    (ctx.workspace / "tri.glb").write_bytes(make_glb())
    res = ev.run_evaluator("gltf_checks", {"file": "tri.glb", "max_triangles": 10, "require_materials": True,
                                           "max_extent": 5}, ctx)
    assert res.passed is True, res.details
    assert res.details["stats"]["triangles"] == 1 and res.details["stats"]["extent"] == [1, 2, 0]
    (ctx.workspace / "broken.glb").write_bytes(make_glb(extra_triangle_count=30))
    bad = ev.run_evaluator("gltf_checks", {"file": "broken.glb"}, ctx)
    assert bad.passed is False and "overruns" in bad.details["stats"]["problems"][0]
    (ctx.workspace / "not.glb").write_bytes(b"nope" * 10)
    assert ev.run_evaluator("gltf_checks", {"file": "not.glb"}, ctx).error


def test_json_schema(ctx):
    (ctx.private_dirs[0] / "s.json").write_text(json.dumps({"type": "object", "required": ["title"]}))
    (ctx.workspace / "ok.json").write_text(json.dumps({"title": "x"}))
    (ctx.workspace / "bad.json").write_text(json.dumps({"name": "x"}))
    assert ev.run_evaluator("json_schema", {"file": "ok.json", "schema": "private:s.json"}, ctx).value == 1.0
    bad = ev.run_evaluator("json_schema", {"file": "bad.json", "schema": "private:s.json"}, ctx)
    assert bad.value == 0.0 and "title" in bad.details["errors"][0]


def test_citations_offline(ctx):
    doc = ("# Findings\n\nThe rover landed in 2021 and drove 28 km in its first three years according to the "
           "mission team (https://mars.nasa.gov/mars2020/). A later paper confirmed the traverse length "
           "doi:10.1029/2022JE007455 and discussed the sampling depots in detail.\n\n"
           "This paragraph makes a substantive claim with no source at all and keeps going for long enough to "
           "count as a paragraph that needs a citation in the rubric.\n")
    (ctx.workspace / "report.md").write_text(doc)
    (ctx.private_dirs[0] / "refs.json").write_text(json.dumps(["https://mars.nasa.gov/mars2020", "10.1029/2022JE007455"]))
    res = ev.run_evaluator("citations", {"file": "report.md", "reference_set": "private:refs.json",
                                         "min_citations": 2, "require_per_paragraph": True}, ctx)
    assert res.value == 1.0
    checks = {c["name"]: c["passed"] for c in res.details["checks"]}
    assert checks == {"min_citations": True, "cited_paragraphs": False}
    syn = ev.run_evaluator("citations", {"file": "report.md", "network": True}, ctx)
    assert "network requested but not allowed" in syn.details["mode"]


def test_script_and_plugin(ctx, tmp_path):
    script = tmp_path / "check.py"
    script.write_text("import json, sys\nprint(json.dumps({'value': 0.75, 'passed': True, 'details': {'n': 4}}))\n")
    res = ev.run_evaluator("script", {"command": [sys.executable, "task:check.py", "{workspace}"]}, ctx)
    assert res.value == 0.75 and res.details["n"] == 4
    plug = tmp_path / "plug.py"
    plug.write_text("@register('always_half')\ndef f(params, ctx):\n    return EvalResult(0.5, None, {})\n")
    ev.load_plugin(plug)
    assert ev.run_evaluator("always_half", {}, ctx).value == 0.5
    assert ev.run_evaluator("nope", {}, ctx).error.startswith("unknown evaluator")


def test_blind_judge_reads_merged(ctx, tmp_path):
    merged = tmp_path / "merged.json"
    merged.write_text(json.dumps({"runs": {"t/baltor/1": {"score": 0.8, "win_share": 0.75, "appearances": 4,
                                                           "wins": 3, "losses": 1, "ties": 0}}}))
    c = ev.EvalContext(ctx.workspace, run={"run_id": "t/baltor/1"}, extras={"judging_merged": merged})
    assert ev.run_evaluator("blind_judge", {}, c).value == 0.8
    assert ev.run_evaluator("blind_judge", {"field": "win_share"}, c).value == 0.75
    c2 = ev.EvalContext(ctx.workspace, run={"run_id": "t/baltor/9"}, extras={"judging_merged": merged})
    assert ev.run_evaluator("blind_judge", {}, c2).error


SPEC = {
    "id": "tiny", "over_budget": "score-as-failure",
    "metrics": [
        {"name": "present", "direction": "higher", "kind": "deterministic", "weight": 1, "on_missing": 0,
         "range": [0, 1], "evaluator": {"type": "files_present", "params": {"paths": ["answer.txt"]}}},
        {"name": "broken", "direction": "lower", "kind": "deterministic", "weight": 1, "on_missing": 10,
         "range": [0, 10], "evaluator": {"type": "metric_from_file", "params": {"file": "missing.json"}}},
    ],
    "success_threshold": {"metric": "present", "op": ">=", "value": 1},
}


def _rec(status="completed", exceeded=()):
    return {"run_id": "tiny/baltor/1", "exit": {"status": status}, "budget": {"exceeded": list(exceeded)}}


def test_score_run_policies(ctx):
    (ctx.workspace / "answer.txt").write_text("42")
    rec = ev.score_run(SPEC, _rec(), ctx, now="2026-10-10T00:00:00Z")
    res = {r["metric"]: r for r in rec["evaluation"]["results"]}
    assert res["present"]["value"] == 1.0 and res["present"]["scored_as"] == "evaluated"
    assert res["broken"]["value"] == 10 and res["broken"]["scored_as"] == "error"
    assert res["weighted_score"]["value"] == pytest.approx(0.5)
    assert rec["evaluation"]["success"] is True
    over = ev.score_run(SPEC, _rec("budget-exceeded", ["tool_calls"]), ctx)
    assert all(r["scored_as"] in ("failure", "derived") for r in over["evaluation"]["results"])
    assert over["evaluation"]["success"] is False
    lenient = ev.score_run(dict(SPEC, over_budget="evaluate-as-is"), _rec("timeout", ["wall_s"]), ctx)
    assert {r["metric"]: r for r in lenient["evaluation"]["results"]}["present"]["scored_as"] == "evaluated"


def test_evaluate_task_verifies_registration(tmp_path):
    root = tmp_path / "showcases"
    tdir = root / "tasks" / "tiny"
    (tdir / "private").mkdir(parents=True)
    (tdir / "private" / "truth.csv").write_text("id,cluster\n1,a\n2,a\n")
    spec = dict(SPEC, metrics=[SPEC["metrics"][0]],
                files_sha256={"private/truth.csv": hashlib.sha256(b"id,cluster\n1,a\n2,a\n").hexdigest()})
    spec["spec_sha256"] = ev.canonical_hash(spec)
    (tdir / "spec.json").write_text(json.dumps(spec))
    rd = root / "runs" / "tiny" / "baltor" / "1"
    (rd / "workspace").mkdir(parents=True)
    (rd / "workspace" / "answer.txt").write_text("42")
    (rd / "run.json").write_text(json.dumps(dict(_rec(), spec_sha256=spec["spec_sha256"], workspace="workspace")))
    recs = ev.evaluate_task(root, "tiny", now="2026-10-10T00:00:00Z")
    assert recs[0]["evaluation"]["success"] is True
    assert json.loads((rd / "run.json").read_text())["evaluation"]["status"] == "done"
    (tdir / "private" / "truth.csv").write_text("id,cluster\n1,a\n2,b\n")
    with pytest.raises(SystemExit):
        ev.evaluate_task(root, "tiny")
    with pytest.raises(SystemExit):
        (tdir / "private" / "truth.csv").write_text("id,cluster\n1,a\n2,a\n")
        ev.evaluate_task(root, "tiny", network=True)
