#!/usr/bin/env python3
"""Evaluator plugins for Baltor showcases, and the step that scores every run.

Each metric in a task spec names an evaluator from this registry and gives it
``params``. Paths in params are workspace-relative by default; ``private:x``
resolves in the task's private assets (held-out labels, hidden tests, reference
lists that never enter an agent's workspace) and ``task:x`` in the registered
task directory.

Built-in evaluators (all deterministic and offline unless noted):

==================  ==========================================================
files_present       required output files exist (fraction present)
pytest              hidden tests run against a scratch copy of the workspace
metric_from_file    a number from a JSON/CSV/text file, optionally after a
                    pre-registered command computes it (agent-written numbers
                    are 'self-reported')
f1_ground_truth     precision/recall/F1 against ground truth: sets, pairs,
                    clusters (pairwise F1) or binary labels
sklearn_metric      a scikit-learn metric on a predictions CSV vs held-out labels
image_checks        Pillow: size, format, bytes, WCAG contrast of text regions,
                    safe-area placement, quiet margins
mp4_checks          ffprobe: duration, resolution, fps, codecs, audio present
gltf_checks         GLB/glTF 2.0 structure: header, chunks, accessors, buffers,
                    triangle count, bounds, materials
json_schema         a JSON output validates against a schema
citations           links and DOIs in a document: offline against a reference
                    list; with --network, resolves each URL (network declared)
script              a pre-registered task script prints {"value": ...}
blind_judge         reads merged blind A/B judgements (llm-judge / human-judge)
==================  ==========================================================

Plugins: ``--plugin path.py`` imports a file that calls ``register``.

CLI::

    python3 showcase_evaluators.py evaluate --root showcases --task ID [--network] [--plugin P] [--now ISO]
    python3 showcase_evaluators.py check TYPE --workspace DIR --params '{"file": "x.png", ...}'
    python3 showcase_evaluators.py list
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import fnmatch
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent


@dataclass
class EvalResult:
    value: float | None
    passed: bool | None = None
    details: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class EvalContext:
    workspace: Path
    task_dir: Path | None = None
    private_dirs: list[Path] = field(default_factory=list)
    network: bool = False
    timeout_s: int = 600
    run: dict | None = None
    extras: dict = field(default_factory=dict)

    def resolve(self, ref: str) -> Path:
        if not isinstance(ref, str) or not ref:
            raise ValueError(f"bad path reference {ref!r}")
        if ref.startswith("private:"):
            rel = _safe_rel(ref[len("private:"):])
            for d in self.private_dirs:
                if (Path(d) / rel).exists():
                    return Path(d) / rel
            raise FileNotFoundError(f"{ref} not found in private assets")
        if ref.startswith("task:"):
            if self.task_dir is None:
                raise FileNotFoundError("no task directory")
            return Path(self.task_dir) / _safe_rel(ref[len("task:"):])
        return Path(self.workspace) / _safe_rel(ref)


def _safe_rel(rel: str) -> str:
    p = Path(rel)
    if p.is_absolute() or ".." in p.parts:
        raise ValueError(f"path {rel!r} must be relative and stay inside its base")
    return rel


REGISTRY: dict[str, Callable] = {}


def register(name: str, *, kind: str = "deterministic", network: bool = False):
    def deco(fn):
        fn.evaluator_name = name
        fn.kind = kind
        fn.network = network
        REGISTRY[name] = fn
        return fn
    return deco


def load_plugin(path: str | os.PathLike) -> None:
    spec = importlib.util.spec_from_file_location(f"showcase_eval_plugin_{abs(hash(str(path)))}", str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    mod.__dict__["register"] = register
    mod.__dict__["EvalResult"] = EvalResult
    spec.loader.exec_module(mod)  # type: ignore[union-attr]


def run_evaluator(etype: str, params: dict, ctx: EvalContext) -> EvalResult:
    fn = REGISTRY.get(etype)
    if fn is None:
        return EvalResult(None, None, {}, f"unknown evaluator '{etype}'")
    try:
        res = fn(params or {}, ctx)
    except Exception as exc:  # noqa: BLE001
        return EvalResult(None, None, {}, f"{type(exc).__name__}: {exc}")
    if res.value is not None and (math.isnan(res.value) or math.isinf(res.value)):
        return EvalResult(None, res.passed, res.details, "evaluator returned a non-finite value")
    return res


def _checks_result(checks: list[dict], extra: dict | None = None) -> EvalResult:
    n = len(checks)
    ok = sum(1 for c in checks if c["passed"])
    return EvalResult(ok / n if n else None, ok == n if n else None, {"checks": checks, **(extra or {})})


# --------------------------------------------------------------------------- generic evaluators

@register("files_present")
def files_present(params: dict, ctx: EvalContext) -> EvalResult:
    pats = params.get("paths") or []
    files = [p.relative_to(ctx.workspace).as_posix() for p in Path(ctx.workspace).rglob("*") if p.is_file()]
    checks = [{"name": pat, "passed": any(fnmatch.fnmatch(f, pat) for f in files), "detail": ""} for pat in pats]
    return _checks_result(checks)


@register("pytest")
def pytest_eval(params: dict, ctx: EvalContext) -> EvalResult:
    tests = ctx.resolve(params.get("tests", "private:tests"))
    timeout = int(params.get("timeout_s", ctx.timeout_s))
    with tempfile.TemporaryDirectory(prefix="showcase-pytest-") as tmp:
        ws = Path(tmp) / "ws"
        shutil.copytree(ctx.workspace, ws, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache",
                                                                          "node_modules", ".venv"))
        dest = ws / params.get("dest", "_hidden_tests")
        if tests.is_dir():
            shutil.copytree(tests, dest, dirs_exist_ok=True)
        else:
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(tests, dest / tests.name)
        junit = Path(tmp) / "junit.xml"
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(ws))
        env.pop("PYTEST_ADDOPTS", None)
        cmd = [params.get("python", sys.executable), "-m", "pytest", "-q", "-p", "no:cacheprovider",
               f"--junitxml={junit}", "--rootdir", str(ws), str(dest.relative_to(ws)), *params.get("args", [])]
        try:
            proc = subprocess.run(cmd, cwd=ws, capture_output=True, text=True, timeout=timeout, env=env)
        except subprocess.TimeoutExpired:
            return EvalResult(None, False, {"timeout_s": timeout}, f"hidden tests timed out after {timeout} s")
        if not junit.exists():
            return EvalResult(None, False, {"stdout": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]},
                              "pytest produced no report")
        root = ET.parse(junit).getroot()
        suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
        total = sum(int(s.get("tests", 0)) for s in suites)
        failed = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
        skipped = sum(int(s.get("skipped", 0)) for s in suites)
        failing = [f"{c.get('classname')}::{c.get('name')}" for s in suites for c in s.iter("testcase")
                   if c.find("failure") is not None or c.find("error") is not None][:50]
        ran = total - skipped
        if ran <= 0:
            return EvalResult(0.0, False, {"tests": total, "skipped": skipped}, None)
        return EvalResult((ran - failed) / ran, failed == 0,
                          {"tests": total, "failed": failed, "skipped": skipped, "failing": failing,
                           "tail": proc.stdout[-1500:]})


def _json_pointer(doc, pointer: str):
    if pointer in ("", "/"):
        return doc
    for part in pointer.lstrip("/").split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        doc = doc[int(part)] if isinstance(doc, list) else doc[part]
    return doc


def _fill(arg: str, ctx: EvalContext) -> str:
    out = arg.replace("{workspace}", str(ctx.workspace))
    if ctx.task_dir:
        out = out.replace("{task_dir}", str(ctx.task_dir))
    if ctx.private_dirs:
        out = out.replace("{private}", str(ctx.private_dirs[0]))
    if arg.startswith(("task:", "private:")):
        out = str(ctx.resolve(arg))
    return out


@register("metric_from_file")
def metric_from_file(params: dict, ctx: EvalContext) -> EvalResult:
    details: dict = {"trust": "agent-written (self-reported)"}
    if params.get("command"):
        cmd = [_fill(a, ctx) for a in params["command"]]
        proc = subprocess.run(cmd, cwd=ctx.workspace, capture_output=True, text=True,
                              timeout=int(params.get("timeout_s", ctx.timeout_s)))
        details.update({"trust": "computed by a pre-registered command", "exit_code": proc.returncode,
                        "stderr": proc.stderr[-1000:]})
        if proc.returncode:
            return EvalResult(None, False, details, f"command exited {proc.returncode}")
    path = ctx.resolve(params["file"])
    fmt = params.get("format") or {".json": "json", ".csv": "csv"}.get(path.suffix.lower(), "text")
    text = path.read_text(encoding="utf-8")
    if fmt == "json":
        value = _json_pointer(json.loads(text), params.get("pointer", ""))
    elif fmt == "csv":
        rows = list(csv.DictReader(io.StringIO(text)))
        where = params.get("where") or {}
        rows = [row for row in rows if all(str(row.get(k)) == str(v) for k, v in where.items())]
        if not rows:
            raise ValueError("no CSV row matches")
        value = rows[int(params.get("row", 0))][params["column"]]
    else:
        m = re.search(params.get("regex", r"([-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"), text)
        if not m:
            raise ValueError("pattern not found")
        value = m.group(1) if m.groups() else m.group(0)
    value = float(value)
    passed = None
    if "threshold" in params:
        passed = value >= params["threshold"] if params.get("direction", "higher") == "higher" else \
            value <= params["threshold"]
    return EvalResult(value, passed, details)


@register("script")
def script_eval(params: dict, ctx: EvalContext) -> EvalResult:
    cmd = [_fill(a, ctx) for a in params["command"]]
    proc = subprocess.run(cmd, cwd=ctx.workspace, capture_output=True, text=True,
                          timeout=int(params.get("timeout_s", ctx.timeout_s)))
    lines = [x for x in proc.stdout.strip().splitlines() if x.strip()]
    if not lines:
        return EvalResult(None, False, {"stderr": proc.stderr[-1000:]}, f"script printed nothing (exit {proc.returncode})")
    data = json.loads(lines[-1])
    return EvalResult(None if data.get("value") is None else float(data["value"]), data.get("passed"),
                      dict(data.get("details") or {}, exit_code=proc.returncode))


# --------------------------------------------------------------------------- ground truth

def _read_table(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        data = json.loads(text)
        return data if isinstance(data, list) else data.get("rows", [])
    return list(csv.DictReader(io.StringIO(text)))


def _norm(x) -> str:
    return re.sub(r"\s+", " ", str(x)).strip().lower()


def _pairs_from_clusters(rows: list[dict], id_col: str, cluster_col: str) -> set[tuple[str, str]]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        c = str(row.get(cluster_col, "")).strip()
        if c == "":
            continue
        groups.setdefault(c, []).append(_norm(row[id_col]))
    pairs = set()
    for ids in groups.values():
        ids = sorted(set(ids))
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                pairs.add((ids[i], ids[j]))
    return pairs


def _items(rows: list[dict], params: dict, mode: str) -> set:
    if mode == "pairs":
        a, b = params.get("columns", ["a", "b"])
        return {tuple(sorted((_norm(r[a]), _norm(r[b])))) for r in rows}
    if mode == "clusters":
        return _pairs_from_clusters(rows, params.get("id_column", "id"), params.get("cluster_column", "cluster"))
    if mode == "labels":
        pos = _norm(params.get("positive", "1"))
        idc, lc = params.get("id_column", "id"), params.get("label_column", "label")
        return {_norm(r[idc]) for r in rows if _norm(r[lc]) == pos}
    col = params.get("column", "item")
    return {_norm(r[col]) if isinstance(r, dict) else _norm(r) for r in rows}


@register("f1_ground_truth")
def f1_ground_truth(params: dict, ctx: EvalContext) -> EvalResult:
    mode = params.get("mode", "set")
    pred = _items(_read_table(ctx.resolve(params["predictions"])), params, mode)
    truth = _items(_read_table(ctx.resolve(params["truth"])), dict(params, **params.get("truth_params", {})), mode)
    tp, fp, fn = len(pred & truth), len(pred - truth), len(truth - pred)
    precision = tp / (tp + fp) if tp + fp else (1.0 if not truth else 0.0)
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    beta = float(params.get("beta", 1.0))
    if beta != 1.0 and precision + recall:
        f1 = (1 + beta ** 2) * precision * recall / (beta ** 2 * precision + recall)
    passed = f1 >= params["threshold"] if "threshold" in params else None
    return EvalResult(f1, passed, {"mode": mode, "precision": round(precision, 6), "recall": round(recall, 6),
                                   "tp": tp, "fp": fp, "fn": fn})


SKLEARN_METRICS = {
    "accuracy": ("accuracy_score", "label", {}),
    "balanced_accuracy": ("balanced_accuracy_score", "label", {}),
    "f1": ("f1_score", "label", {"average": "binary"}),
    "f1_macro": ("f1_score", "label", {"average": "macro"}),
    "f1_weighted": ("f1_score", "label", {"average": "weighted"}),
    "precision": ("precision_score", "label", {"average": "binary"}),
    "recall": ("recall_score", "label", {"average": "binary"}),
    "matthews_corrcoef": ("matthews_corrcoef", "label", {}),
    "quadratic_weighted_kappa": ("cohen_kappa_score", "label", {"weights": "quadratic"}),
    "roc_auc": ("roc_auc_score", "score", {}),
    "log_loss": ("log_loss", "score", {}),
    "mae": ("mean_absolute_error", "number", {}),
    "rmse": ("mean_squared_error", "number", {}),
    "rmsle": ("mean_squared_log_error", "number", {}),
    "r2": ("r2_score", "number", {}),
    "mape": ("mean_absolute_percentage_error", "number", {}),
}


@register("sklearn_metric")
def sklearn_metric(params: dict, ctx: EvalContext) -> EvalResult:
    from sklearn import metrics as skm  # lazy: only this evaluator needs scikit-learn

    metric = params["metric"]
    if metric not in SKLEARN_METRICS:
        raise ValueError(f"metric must be one of {sorted(SKLEARN_METRICS)}")
    fn_name, kind, kwargs = SKLEARN_METRICS[metric]
    idc = params.get("id_column", "id")
    pcol = params.get("prediction_column", "prediction")
    lcol = params.get("label_column", "label")
    preds = {_norm(r[idc]): r.get(pcol) for r in _read_table(ctx.resolve(params["predictions"]))}
    labels = [(_norm(r[idc]), r[lcol]) for r in _read_table(ctx.resolve(params["labels"]))]
    missing = [i for i, _ in labels if i not in preds or preds[i] in (None, "")]
    policy = params.get("missing", "worst")
    if missing and policy == "error":
        raise ValueError(f"{len(missing)} id(s) have no prediction")
    y_true, y_pred = [], []
    for i, lab in labels:
        p = preds.get(i)
        if p in (None, ""):
            if policy == "drop":
                continue
            if kind == "label":
                p = "__missing__"
            elif "fill_value" in params:
                p = params["fill_value"]
            else:
                raise ValueError(f"{len(missing)} prediction(s) missing and no fill_value for a numeric metric")
        y_true.append(lab)
        y_pred.append(p)
    if kind == "label":
        y_true = [str(v).strip() for v in y_true]
        y_pred = [str(v).strip() for v in y_pred]
        if "pos_label" in params and "average" in kwargs and kwargs["average"] == "binary":
            kwargs = dict(kwargs, pos_label=str(params["pos_label"]))
        elif kwargs.get("average") == "binary":
            kwargs = dict(kwargs, pos_label="1")
        if metric == "quadratic_weighted_kappa":
            y_true = [int(float(v)) for v in y_true]
            y_pred = [int(float(v)) if v != "__missing__" else -999 for v in y_pred]
    else:
        y_true = [float(v) for v in y_true]
        y_pred = [float(v) for v in y_pred]
    value = float(getattr(skm, fn_name)(y_true, y_pred, **kwargs))
    if metric in ("rmse", "rmsle"):
        value = math.sqrt(value)
    passed = None
    if "threshold" in params:
        passed = value >= params["threshold"] if params.get("direction", "higher") == "higher" else \
            value <= params["threshold"]
    return EvalResult(value, passed, {"metric": metric, "n": len(y_true), "missing": len(missing),
                                      "missing_policy": policy})


# --------------------------------------------------------------------------- images

def _srgb_to_linear(c: float) -> float:
    c = c / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb) -> float:
    r, g, b = (_srgb_to_linear(float(x)) for x in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(rgb1, rgb2) -> float:
    l1, l2 = sorted((relative_luminance(rgb1), relative_luminance(rgb2)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def _otsu(hist: list[int]) -> int:
    total = sum(hist)
    sum_all = sum(i * h for i, h in enumerate(hist))
    w_b = sum_b = 0.0
    best, thr = -1.0, 127
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b, m_f = sum_b / w_b, (sum_all - sum_b) / w_f
        between = w_b * w_f * (m_b - m_f) ** 2
        if between > best:
            best, thr = between, t
    return thr


def region_contrast(img, box) -> dict:
    """WCAG contrast between the two dominant tones (Otsu split on luma) of a text region."""
    from PIL import ImageStat

    crop = img.convert("RGB").crop(tuple(int(round(v)) for v in box))
    luma = crop.convert("L")
    thr = _otsu(luma.histogram())
    dark_mask = luma.point(lambda v: 255 if v <= thr else 0)
    light_mask = luma.point(lambda v: 255 if v > thr else 0)
    n_dark = dark_mask.histogram()[255]
    n_light = light_mask.histogram()[255]
    if n_dark == 0 or n_light == 0:
        return {"ratio": 1.0, "threshold": thr, "fg": None, "bg": None, "note": "region is a single tone"}
    dark = ImageStat.Stat(crop, dark_mask).mean
    light = ImageStat.Stat(crop, light_mask).mean
    # the smaller cluster is taken as the text
    fg, bg = (dark, light) if n_dark <= n_light else (light, dark)
    return {"ratio": round(contrast_ratio(fg, bg), 3), "threshold": thr,
            "fg": "#%02x%02x%02x" % tuple(int(round(c)) for c in fg[:3]),
            "bg": "#%02x%02x%02x" % tuple(int(round(c)) for c in bg[:3]),
            "text_fraction": round(min(n_dark, n_light) / (n_dark + n_light), 4)}


def _box_px(box, w: int, h: int) -> list[float]:
    if all(0 <= float(v) <= 1 for v in box):
        return [box[0] * w, box[1] * h, box[2] * w, box[3] * h]
    return [float(v) for v in box]


def _safe_rect(safe: dict, w: int, h: int) -> list[float]:
    def px(v, total):
        v = float(v)
        return v * total if v <= 1 else v
    return [px(safe.get("left", 0), w), px(safe.get("top", 0), h),
            w - px(safe.get("right", 0), w), h - px(safe.get("bottom", 0), h)]


@register("image_checks")
def image_checks(params: dict, ctx: EvalContext) -> EvalResult:
    from PIL import Image, ImageFilter

    path = ctx.resolve(params["file"])
    checks: list[dict] = []
    with Image.open(path) as im:
        im.load()
        w, h = im.size
        fmt = (im.format or "").upper()
        if "width" in params or "height" in params:
            ok = (params.get("width", w), params.get("height", h)) == (w, h)
            checks.append({"name": "size", "passed": ok,
                           "detail": f"{w}x{h} (expected {params.get('width', w)}x{params.get('height', h)})"})
        if "min_width" in params or "min_height" in params:
            ok = w >= params.get("min_width", 0) and h >= params.get("min_height", 0)
            checks.append({"name": "min_size", "passed": ok, "detail": f"{w}x{h}"})
        if "aspect" in params:
            a_w, a_h = (float(x) for x in str(params["aspect"]).split(":"))
            ok = abs(w / h - a_w / a_h) <= params.get("aspect_tolerance", 0.01)
            checks.append({"name": "aspect", "passed": ok, "detail": f"{w / h:.4f} vs {a_w / a_h:.4f}"})
        if "format" in params:
            checks.append({"name": "format", "passed": fmt == str(params["format"]).upper(), "detail": fmt})
        if "max_bytes" in params:
            size = path.stat().st_size
            checks.append({"name": "max_bytes", "passed": size <= params["max_bytes"], "detail": f"{size} bytes"})
        regions = list(params.get("regions", []))
        if params.get("layout"):
            layout = json.loads(ctx.resolve(params["layout"]).read_text(encoding="utf-8"))
            for item in layout.get("text", layout.get("regions", [])):
                regions.append({"name": item.get("name", "text"), "box": item["box"],
                                "min_contrast": item.get("min_contrast", params.get("min_contrast", 4.5))})
        safe = _safe_rect(params["safe_area"], w, h) if params.get("safe_area") else None
        for reg in regions:
            box = _box_px(reg["box"], w, h)
            rc = region_contrast(im, box)
            need = float(reg.get("min_contrast", params.get("min_contrast", 4.5)))
            checks.append({"name": f"contrast:{reg.get('name', 'region')}", "passed": rc["ratio"] >= need,
                           "detail": f"{rc['ratio']}:1 (need {need}:1) fg {rc['fg']} bg {rc['bg']}"})
            if safe:
                inside = box[0] >= safe[0] and box[1] >= safe[1] and box[2] <= safe[2] and box[3] <= safe[3]
                checks.append({"name": f"safe_area:{reg.get('name', 'region')}", "passed": inside,
                               "detail": f"box {[round(v) for v in box]} within {[round(v) for v in safe]}"})
        if params.get("quiet_margins"):
            qm = params["quiet_margins"]
            band = float(qm.get("band", 0.05))
            edges = im.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > qm.get("edge", 40) else 0)
            bw, bh = max(3, int(w * band)), max(3, int(h * band))
            i = 2  # the edge filter fires on the image border itself; skip those pixels
            strips = [(i, i, w - i, bh), (i, h - bh, w - i, h - i), (i, i, bw, h - i), (w - bw, i, w - i, h - i)]
            dens = []
            for s in strips:
                c = edges.crop(s)
                dens.append(c.histogram()[255] / (c.size[0] * c.size[1]))
            worst = max(dens)
            checks.append({"name": "quiet_margins", "passed": worst <= qm.get("max_edge_density", 0.02),
                           "detail": f"max edge density {worst:.4f} in the outer {band:.0%}"})
    return _checks_result(checks, {"width": w, "height": h, "format": fmt})


# --------------------------------------------------------------------------- video

def ffprobe(path: Path) -> dict:
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is not installed")
    out = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams",
                          str(path)], capture_output=True, text=True, check=True, timeout=120).stdout
    return json.loads(out)


def _fps(s: str | None) -> float | None:
    if not s or s in ("0/0",):
        return None
    if "/" in s:
        n, d = s.split("/")
        return float(n) / float(d) if float(d) else None
    return float(s)


def mp4_checks_from_probe(info: dict, params: dict) -> list[dict]:
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float((info.get("format") or {}).get("duration") or 0)
    checks = []
    if "min_duration" in params:
        checks.append({"name": "min_duration", "passed": duration >= params["min_duration"],
                       "detail": f"{duration:.2f}s (min {params['min_duration']}s)"})
    if "max_duration" in params:
        checks.append({"name": "max_duration", "passed": duration <= params["max_duration"],
                       "detail": f"{duration:.2f}s (max {params['max_duration']}s)"})
    checks.append({"name": "video_stream", "passed": video is not None, "detail": video.get("codec_name", "")
                   if video else "none"})
    if video is not None:
        w, h = int(video.get("width", 0)), int(video.get("height", 0))
        if "width" in params or "height" in params:
            checks.append({"name": "resolution", "passed": (w, h) == (params.get("width", w), params.get("height", h)),
                           "detail": f"{w}x{h}"})
        fps = _fps(video.get("avg_frame_rate") or video.get("r_frame_rate"))
        if "min_fps" in params:
            checks.append({"name": "min_fps", "passed": fps is not None and fps >= params["min_fps"] - 0.01,
                           "detail": f"{fps}"})
        if "video_codecs" in params:
            checks.append({"name": "video_codec", "passed": video.get("codec_name") in params["video_codecs"],
                           "detail": str(video.get("codec_name"))})
    if params.get("require_audio", False):
        checks.append({"name": "audio_stream", "passed": audio is not None,
                       "detail": audio.get("codec_name", "") if audio else "none"})
    return checks


@register("mp4_checks")
def mp4_checks(params: dict, ctx: EvalContext) -> EvalResult:
    info = ffprobe(ctx.resolve(params["file"]))
    return _checks_result(mp4_checks_from_probe(info, params),
                          {"duration_s": float((info.get("format") or {}).get("duration") or 0)})


# --------------------------------------------------------------------------- glTF / GLB

GLB_MAGIC = b"glTF"
CHUNK_JSON = 0x4E4F534A
CHUNK_BIN = 0x004E4942
COMPONENT_SIZE = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
TYPE_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}


def parse_glb(data: bytes) -> tuple[dict, bytes | None]:
    if len(data) < 20 or data[:4] != GLB_MAGIC:
        raise ValueError("not a GLB file (bad magic)")
    _, version, length = struct.unpack_from("<4sII", data, 0)
    if version != 2:
        raise ValueError(f"GLB version {version}, expected 2")
    if length != len(data):
        raise ValueError(f"header length {length} != file size {len(data)}")
    offset = 12
    doc, binchunk = None, None
    while offset + 8 <= len(data):
        clen, ctype = struct.unpack_from("<II", data, offset)
        body = data[offset + 8: offset + 8 + clen]
        if len(body) != clen:
            raise ValueError("truncated chunk")
        if ctype == CHUNK_JSON and doc is None:
            doc = json.loads(body.decode("utf-8").rstrip(" \x00"))
        elif ctype == CHUNK_BIN and binchunk is None:
            binchunk = body
        offset += 8 + clen
    if doc is None:
        raise ValueError("GLB has no JSON chunk")
    return doc, binchunk


def gltf_stats(doc: dict, bin_len: int | None) -> dict:
    problems: list[str] = []
    buffers = doc.get("buffers", [])
    views = doc.get("bufferViews", [])
    accessors = doc.get("accessors", [])
    for i, b in enumerate(buffers):
        if i == 0 and bin_len is not None and "uri" not in b and b.get("byteLength", 0) > bin_len:
            problems.append(f"buffer 0 byteLength {b.get('byteLength')} > BIN chunk {bin_len}")
    for i, v in enumerate(views):
        if v.get("buffer", -1) >= len(buffers):
            problems.append(f"bufferView {i} points at missing buffer")
            continue
        end = v.get("byteOffset", 0) + v.get("byteLength", 0)
        if end > buffers[v["buffer"]].get("byteLength", 0):
            problems.append(f"bufferView {i} overruns its buffer")
    for i, a in enumerate(accessors):
        bv = a.get("bufferView")
        if bv is None:
            continue
        if bv >= len(views):
            problems.append(f"accessor {i} points at missing bufferView")
            continue
        need = a.get("byteOffset", 0) + a.get("count", 0) * COMPONENT_SIZE.get(a.get("componentType"), 4) * \
            TYPE_COUNT.get(a.get("type"), 1)
        if need > views[bv].get("byteLength", 0):
            problems.append(f"accessor {i} overruns bufferView {bv}")
    triangles = 0
    lo = [math.inf] * 3
    hi = [-math.inf] * 3
    prims = 0
    for mesh in doc.get("meshes", []):
        for p in mesh.get("primitives", []):
            prims += 1
            mode = p.get("mode", 4)
            pos = p.get("attributes", {}).get("POSITION")
            count = accessors[p["indices"]]["count"] if "indices" in p and p["indices"] < len(accessors) else (
                accessors[pos]["count"] if pos is not None and pos < len(accessors) else 0)
            if mode == 4:
                triangles += count // 3
            elif mode in (5, 6):
                triangles += max(0, count - 2)
            if pos is not None and pos < len(accessors):
                acc = accessors[pos]
                if "min" in acc and "max" in acc:
                    lo = [min(a, b) for a, b in zip(lo, acc["min"])]
                    hi = [max(a, b) for a, b in zip(hi, acc["max"])]
                else:
                    problems.append(f"POSITION accessor {pos} has no min/max")
    extent = [round(h - l, 6) for l, h in zip(lo, hi)] if all(math.isfinite(v) for v in lo + hi) else None
    return {"asset_version": (doc.get("asset") or {}).get("version"), "meshes": len(doc.get("meshes", [])),
            "primitives": prims, "nodes": len(doc.get("nodes", [])), "materials": len(doc.get("materials", [])),
            "textures": len(doc.get("textures", [])), "scenes": len(doc.get("scenes", [])),
            "animations": len(doc.get("animations", [])), "triangles": triangles, "extent": extent,
            "problems": problems}


@register("gltf_checks")
def gltf_checks(params: dict, ctx: EvalContext) -> EvalResult:
    path = ctx.resolve(params["file"])
    data = path.read_bytes()
    if path.suffix.lower() == ".glb":
        doc, binchunk = parse_glb(data)
        stats = gltf_stats(doc, len(binchunk) if binchunk is not None else None)
    else:
        doc = json.loads(data.decode("utf-8"))
        stats = gltf_stats(doc, None)
        for b in doc.get("buffers", []):
            uri = b.get("uri", "")
            if uri and not uri.startswith("data:") and not (path.parent / _safe_rel(uri)).exists():
                stats["problems"].append(f"external buffer {uri} is missing")
    checks = [
        {"name": "gltf_2", "passed": str(stats["asset_version"]).startswith("2."), "detail": str(stats["asset_version"])},
        {"name": "structure", "passed": not stats["problems"], "detail": "; ".join(stats["problems"][:5]) or "ok"},
        {"name": "has_mesh", "passed": stats["meshes"] > 0, "detail": f"{stats['meshes']} mesh(es)"},
    ]
    if "max_triangles" in params:
        checks.append({"name": "max_triangles", "passed": stats["triangles"] <= params["max_triangles"],
                       "detail": f"{stats['triangles']} (max {params['max_triangles']})"})
    if "min_triangles" in params:
        checks.append({"name": "min_triangles", "passed": stats["triangles"] >= params["min_triangles"],
                       "detail": f"{stats['triangles']}"})
    if params.get("require_materials"):
        checks.append({"name": "materials", "passed": stats["materials"] > 0, "detail": f"{stats['materials']}"})
    if "max_bytes" in params:
        checks.append({"name": "max_bytes", "passed": len(data) <= params["max_bytes"], "detail": f"{len(data)}"})
    if "max_extent" in params or "min_extent" in params:
        ext = stats["extent"]
        ok = ext is not None and all(e <= params.get("max_extent", math.inf) for e in ext) and \
            max(ext) >= params.get("min_extent", 0)
        checks.append({"name": "extent", "passed": ok, "detail": f"{ext} (units as authored; glTF metres)"})
    return _checks_result(checks, {"stats": stats})


# --------------------------------------------------------------------------- JSON schema

@register("json_schema")
def json_schema_eval(params: dict, ctx: EvalContext) -> EvalResult:
    import jsonschema  # type: ignore

    instance = json.loads(ctx.resolve(params["file"]).read_text(encoding="utf-8"))
    schema = json.loads(ctx.resolve(params["schema"]).read_text(encoding="utf-8"))
    cls = jsonschema.validators.validator_for(schema, default=jsonschema.Draft202012Validator)
    errors = sorted(cls(schema).iter_errors(instance), key=lambda e: list(e.absolute_path))
    msgs = [f"{'/'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}" for e in errors[:20]]
    return EvalResult(1.0 if not errors else 0.0, not errors, {"errors": msgs, "error_count": len(errors)})


# --------------------------------------------------------------------------- citations

URL_RE = re.compile(r"https?://[^\s<>\"'\])}]+")
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+[A-Za-z0-9])")


def extract_citations(text: str) -> dict:
    urls = [u.rstrip(".,;:!?") for u in URL_RE.findall(text)]
    dois = [d for d in DOI_RE.findall(text) if not any(d in u for u in urls)]
    return {"urls": urls, "dois": dois}


def _norm_ref(x: str) -> str:
    x = x.strip().lower()
    x = re.sub(r"^https?://(dx\.)?doi\.org/", "doi:", x)
    if DOI_RE.fullmatch(x):
        x = "doi:" + x
    x = re.sub(r"^https?://(www\.)?", "", x)
    return x.rstrip("/")


def _check_url(url: str, timeout: float) -> int | None:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "baltor-showcase-citation-check/1.0"})
    for method in ("HEAD", "GET"):
        req.method = method
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - URLs come from the evaluated doc
                return resp.status
        except urllib.error.HTTPError as exc:
            if method == "HEAD" and exc.code in (403, 405, 501):
                continue
            return exc.code
        except Exception:  # noqa: BLE001
            if method == "HEAD":
                continue
            return None
    return None


@register("citations", network=True)
def citations(params: dict, ctx: EvalContext) -> EvalResult:
    text = ctx.resolve(params["file"]).read_text(encoding="utf-8")
    cites = extract_citations(text)
    refs = [*cites["urls"], *("https://doi.org/" + d for d in cites["dois"])]
    unique = list(dict.fromkeys(refs))
    details: dict = {"citations": len(refs), "unique": len(unique), "duplicates": len(refs) - len(unique)}
    checks = []
    if "min_citations" in params:
        checks.append({"name": "min_citations", "passed": len(unique) >= params["min_citations"],
                       "detail": f"{len(unique)} unique (min {params['min_citations']})"})
    if params.get("require_per_paragraph"):
        paras = [p for p in re.split(r"\n\s*\n", text) if len(p.split()) >= params.get("paragraph_min_words", 25)
                 and not p.lstrip().startswith("#")]
        uncited = [i for i, p in enumerate(paras) if not (URL_RE.search(p) or DOI_RE.search(p)
                                                          or re.search(r"\[\d+\]", p))]
        checks.append({"name": "cited_paragraphs", "passed": not uncited,
                       "detail": f"{len(paras) - len(uncited)}/{len(paras)} substantive paragraphs cite a source"})
    value: float | None
    if params.get("reference_set"):
        rp = ctx.resolve(params["reference_set"])
        raw = json.loads(rp.read_text(encoding="utf-8")) if rp.suffix == ".json" else \
            [ln for ln in rp.read_text(encoding="utf-8").splitlines() if ln.strip()]
        allowed = {_norm_ref(x if isinstance(x, str) else x.get("url") or x.get("doi")) for x in raw}
        matched = [u for u in unique if _norm_ref(u) in allowed]
        details.update({"mode": "offline reference set", "in_reference_set": len(matched),
                        "not_in_reference_set": [u for u in unique if _norm_ref(u) not in allowed][:30]})
        value = len(matched) / len(unique) if unique else 0.0
    elif params.get("network") and ctx.network:
        timeout = float(params.get("timeout_s", 10))
        limit = int(params.get("max_urls", 60))
        statuses = {u: _check_url(u, timeout) for u in unique[:limit]}
        ok = [u for u, s in statuses.items() if s is not None and s < 400]
        details.update({"mode": "online", "checked": len(statuses), "resolvable": len(ok),
                        "broken": {u: s for u, s in statuses.items() if u not in ok}})
        value = len(ok) / len(statuses) if statuses else 0.0
    else:
        well_formed = [u for u in unique if re.match(r"^https?://[a-z0-9.-]+\.[a-z]{2,}(/|$)", u, re.I)]
        details.update({"mode": "offline syntax only" + (" (network requested but not allowed)"
                                                          if params.get("network") else "")})
        value = len(well_formed) / len(unique) if unique else 0.0
    passed = all(c["passed"] for c in checks) if checks else None
    if "threshold" in params:
        passed = (passed is not False) and value >= params["threshold"]
    return EvalResult(value, passed, dict(details, checks=checks))


# --------------------------------------------------------------------------- blind judging

@register("blind_judge", kind="llm-judge")
def blind_judge(params: dict, ctx: EvalContext) -> EvalResult:
    merged_path = ctx.extras.get("judging_merged")
    if not merged_path or not Path(merged_path).exists():
        return EvalResult(None, None, {}, "judgements not merged yet (run showcase_blind_judge_pack merge)")
    merged = json.loads(Path(merged_path).read_text(encoding="utf-8"))
    rid = (ctx.run or {}).get("run_id")
    row = merged.get("runs", {}).get(rid)
    if not row or row.get("appearances", 0) == 0:
        return EvalResult(None, None, {}, f"{rid} was not in any judged packet")
    field_ = params.get("field", "score")
    return EvalResult(float(row[field_]), None, {k: row[k] for k in ("appearances", "wins", "losses", "ties", "score",
                                                                       "win_share") if k in row})


# --------------------------------------------------------------------------- scoring runs

def canonical_hash(spec: dict) -> str:
    body = {k: v for k, v in spec.items() if k != "spec_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def _sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_registered(task_dir: Path) -> dict:
    spec = json.loads((task_dir / "spec.json").read_text(encoding="utf-8"))
    if canonical_hash(spec) != spec.get("spec_sha256"):
        raise SystemExit(f"{task_dir}/spec.json was edited after registration")
    for rel, want in (spec.get("files_sha256") or {}).items():
        p = task_dir / rel
        if not p.exists() or _sha256_file(p) != want:
            raise SystemExit(f"{task_dir}/{rel} differs from its registered hash (evaluator assets changed?)")
    return spec


def threshold_met(value: float | None, thr: dict) -> bool | None:
    if value is None:
        return None
    op, v = thr["op"], thr["value"]
    return {">=": value >= v, ">": value > v, "<=": value <= v, "<": value < v}[op]


def weighted_score(spec: dict, values: dict[str, float | None]) -> float | None:
    metrics = spec["metrics"]
    if not metrics or not all("range" in m for m in metrics):
        return None
    total = sum(m["weight"] for m in metrics)
    acc = 0.0
    for m in metrics:
        v = values.get(m["name"])
        if v is None:
            return None
        lo, hi = m["range"]
        x = 0.0 if hi == lo else min(1.0, max(0.0, (v - lo) / (hi - lo)))
        acc += m["weight"] * (x if m["direction"] == "higher" else 1.0 - x)
    return acc / total


def score_run(spec: dict, rec: dict, ctx: EvalContext, now: str | None = None) -> dict:
    status = rec["exit"]["status"]
    over = status in ("timeout", "budget-exceeded") or bool(rec["budget"].get("exceeded"))
    fail = status == "not-run" or (over and spec.get("over_budget", "score-as-failure") == "score-as-failure")
    results = []
    values: dict[str, float | None] = {}
    for m in spec["metrics"]:
        ev = m["evaluator"]
        if fail:
            reason = "run not executed" if status == "not-run" else f"over budget ({status}); policy score-as-failure"
            results.append({"metric": m["name"], "value": float(m["on_missing"]), "passed": False,
                            "scored_as": "failure", "evaluator": ev["type"], "details": {"reason": reason},
                            "error": None})
            values[m["name"]] = float(m["on_missing"])
            continue
        res = run_evaluator(ev["type"], ev.get("params", {}), ctx)
        if res.value is None:
            results.append({"metric": m["name"], "value": float(m["on_missing"]), "passed": False,
                            "scored_as": "error", "evaluator": ev["type"], "details": res.details,
                            "error": res.error or "no value"})
            values[m["name"]] = float(m["on_missing"])
        else:
            results.append({"metric": m["name"], "value": res.value, "passed": res.passed, "scored_as": "evaluated",
                            "evaluator": ev["type"], "details": res.details, "error": None})
            values[m["name"]] = res.value
    ws = weighted_score(spec, values)
    if ws is not None:
        results.append({"metric": "weighted_score", "value": round(ws, 6), "passed": None, "scored_as": "derived",
                        "evaluator": "derived", "details": {"formula": "sum(weight * normalised value) / sum(weight)"},
                        "error": None})
        values["weighted_score"] = ws
    thr = spec["success_threshold"]
    success = False if fail else threshold_met(values.get(thr["metric"]), thr)
    rec["evaluation"] = {"status": "done", "evaluated_at": now or _now(), "evaluator_version": VERSION,
                         "network_used": bool(ctx.network), "results": results, "success": success}
    return rec


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def evaluate_task(root: Path, task_id: str, *, network: bool = False, now: str | None = None,
                  only: list[str] | None = None) -> list[dict]:
    root = Path(root)
    tdir = root / "tasks" / task_id
    spec = verify_registered(tdir)
    if network:
        allowed = any((m["evaluator"].get("params") or {}).get("network") for m in spec["metrics"])
        if not allowed:
            raise SystemExit("--network given but no metric in the registered spec declares network: true")
    staging = root / ".cache" / task_id / spec["spec_sha256"][:12]
    privates = [tdir / "private", staging / "private"]
    merged = root / "runs" / task_id / "_judging" / "merged.json"
    out = []
    for p in sorted((root / "runs" / task_id).glob("*/*/run.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec["spec_sha256"] != spec["spec_sha256"]:
            raise SystemExit(f"{p}: run belongs to spec {rec['spec_sha256'][:12]}")
        if only and rec["run_id"] not in only:
            continue
        ctx = EvalContext(workspace=p.parent / rec.get("workspace", "workspace"), task_dir=tdir,
                          private_dirs=privates, network=network, run=rec, extras={"judging_merged": merged})
        score_run(spec, rec, ctx, now)
        p.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        out.append(rec)
    return out


# --------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plugin", action="append", default=[], help="python file that registers more evaluators")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("evaluate", help="score every run of a registered task")
    e.add_argument("--root", type=Path, default=Path("showcases"))
    e.add_argument("--task", required=True)
    e.add_argument("--network", action="store_true", help="allow evaluators that declare network use")
    e.add_argument("--only", action="append")
    e.add_argument("--now")
    c = sub.add_parser("check", help="run one evaluator on a directory")
    c.add_argument("type")
    c.add_argument("--workspace", type=Path, default=Path("."))
    c.add_argument("--private", type=Path, action="append", default=[])
    c.add_argument("--params", default="{}")
    c.add_argument("--network", action="store_true")
    sub.add_parser("list")
    a = ap.parse_args(argv)
    for p in a.plugin:
        load_plugin(p)
    if a.cmd == "list":
        for name, fn in sorted(REGISTRY.items()):
            print(f"{name:<18} kind={fn.kind:<14} network={'yes' if fn.network else 'no'}")
        return 0
    if a.cmd == "check":
        res = run_evaluator(a.type, json.loads(a.params), EvalContext(a.workspace, private_dirs=a.private,
                                                                       network=a.network))
        print(json.dumps({"value": res.value, "passed": res.passed, "details": res.details, "error": res.error},
                         indent=2, default=str))
        return 0 if res.error is None else 1
    recs = evaluate_task(a.root, a.task, network=a.network, now=a.now, only=a.only)
    for r in recs:
        vals = ", ".join(f"{x['metric']}={x['value']:.4g}" + ("" if x["scored_as"] in ("evaluated", "derived")
                                                               else f"[{x['scored_as']}]")
                         for x in r["evaluation"]["results"])
        print(f"{r['run_id']}: {vals}; success={r['evaluation']['success']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
