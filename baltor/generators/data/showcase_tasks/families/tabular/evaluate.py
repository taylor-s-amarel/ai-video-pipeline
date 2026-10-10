#!/usr/bin/env python3
"""Deterministic evaluator for tabular showcase tasks: scores submission.csv against private labels."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import showcase_eval as se  # noqa: E402
import tabular_metrics as tm  # noqa: E402

TRUE = {"true", "1", "1.0", "yes"}
FALSE = {"false", "0", "0.0", "no"}


def norm_label(v: str, binary: bool) -> str:
    v = str(v).strip()
    if binary:
        if v.lower() in TRUE:
            return "1"
        if v.lower() in FALSE:
            return "0"
    return v


def evaluate(detail, ws: Path, pv: Path):
    p = detail["params"]
    split = se.load_json_file(pv / "split.json")
    id_col = split["id_col"]
    target = p["target_col"]
    pred = p["prediction"]
    labels = pd.read_csv(pv / "labels.csv", dtype=str, keep_default_na=False)
    checks, flags, details = [], [], {"rows_expected": int(len(labels))}
    hits = se.leakage_scan(ws, p.get("leakage_patterns", [])) if p.get("leakage_patterns") else []
    checks.append(se.check("no_label_leakage", not hits, "; ".join(hits[:5]) or "no forbidden data access found"))
    if hits:
        flags.append("possible_label_leakage")
    sub_path = ws / p.get("submission", "submission.csv")
    if not sub_path.exists():
        checks.append(se.check("submission_exists", False, f"{sub_path.name} missing"))
        return {}, checks, flags, details
    sub = pd.read_csv(sub_path, dtype=str, keep_default_na=False)
    sub.columns = [c.strip() for c in sub.columns]
    need = [id_col] + pred["columns"]
    missing = [c for c in need if c not in sub.columns]
    checks.append(se.check("columns_present", not missing, f"missing {missing}" if missing else ", ".join(need)))
    if missing:
        return {}, checks, flags, details
    sub[id_col] = sub[id_col].str.strip()
    dupes = int(sub[id_col].duplicated().sum())
    checks.append(se.check("ids_unique", dupes == 0, f"{dupes} duplicate ids"))
    want, got = set(labels[id_col]), set(sub[id_col])
    ids_ok = want == got
    checks.append(se.check("ids_match", ids_ok, f"{len(want - got)} missing, {len(got - want)} unexpected"))
    if not ids_ok or dupes:
        return {}, checks, flags, details
    m = labels.merge(sub[need], on=id_col, how="left", suffixes=("_true", ""))
    tcol = target + "_true" if target in pred["columns"] else target
    values_ok, why = True, ""
    preds = {}
    for c in pred["columns"]:
        if pred["kind"] == "label":
            preds[c] = m[c].map(lambda v: norm_label(v, p.get("binary_labels", False)))
        else:
            vals = pd.to_numeric(m[c], errors="coerce").to_numpy(dtype=float)
            if np.any(~np.isfinite(vals)):
                values_ok, why = False, f"{c}: {int(np.sum(~np.isfinite(vals)))} non-numeric or missing values"
            if pred["kind"] == "probability" and np.any((vals < 0) | (vals > 1)):
                values_ok, why = False, f"{c}: probabilities outside [0, 1]"
            preds[c] = vals
    if pred["kind"] == "interval" and values_ok and np.any(preds["lower"] > preds["upper"]):
        values_ok, why = False, "some lower bounds exceed upper bounds"
    checks.append(se.check("values_valid", values_ok, why or "all predictions parse"))
    if not values_ok:
        return {}, checks, flags, details
    y_raw = m[tcol]
    metrics = {}
    for spec in detail["metrics"]:
        name = spec["name"]
        if name == "checks_pass_rate":
            continue
        if name in tm.PROBABILITY:
            y = y_raw.map(lambda v: norm_label(v, True)).astype(int).to_numpy()
            metrics[name] = tm.PROBABILITY[name](y, preds[pred["columns"][0]])
        elif name in tm.LABEL:
            y = y_raw.map(lambda v: norm_label(v, p.get("binary_labels", False))).to_numpy()
            metrics[name] = tm.LABEL[name](y, preds[pred["columns"][0]].to_numpy())
        elif name in tm.NUMERIC:
            metrics[name] = tm.NUMERIC[name](y_raw.astype(float).to_numpy(), preds[pred["columns"][0]])
        elif name in tm.INTERVAL:
            metrics[name] = tm.INTERVAL[name](y_raw.astype(float).to_numpy(), preds["lower"], preds["upper"])
        else:
            raise ValueError(f"unknown metric {name}")
        if isinstance(metrics[name], float) and math.isnan(metrics[name]):
            checks.append(se.check(f"{name}_defined", False, "metric undefined (e.g. negative values for a log metric)"))
    return metrics, checks, flags, details


if __name__ == "__main__":
    raise SystemExit(se.evaluate_cli(__file__, evaluate))
