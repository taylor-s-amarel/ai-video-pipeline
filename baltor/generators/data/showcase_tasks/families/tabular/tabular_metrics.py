"""Competition metrics in plain numpy, matching the usual Kaggle / scikit-learn definitions.

Every function takes the true values first and predictions second. They are
checked against scikit-learn in the package self-test where scikit-learn exists.
"""

from __future__ import annotations

import numpy as np


def _rankdata(x: np.ndarray) -> np.ndarray:
    """Average ranks (1-based), ties share the mean rank."""
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x), dtype=float)
    sx = x[order]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and sx[j + 1] == sx[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def roc_auc(y, p) -> float:
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    pos, neg = int((y == 1).sum()), int((y == 0).sum())
    if pos == 0 or neg == 0:
        return float("nan")
    r = _rankdata(p)
    return float((r[y == 1].sum() - pos * (pos + 1) / 2) / (pos * neg))


def average_precision(y, p) -> float:
    """Area under the precision-recall curve as scikit-learn defines it (step interpolation over distinct scores)."""
    y, p = np.asarray(y, dtype=int), np.asarray(p, dtype=float)
    order = np.argsort(-p, kind="mergesort")
    y, p = y[order], p[order]
    distinct = np.where(np.diff(p))[0]
    idx = np.r_[distinct, len(y) - 1]
    tps = np.cumsum(y)[idx]
    fps = (idx + 1) - tps
    total_pos = y.sum()
    if total_pos == 0:
        return float("nan")
    precision = tps / (tps + fps)
    recall = tps / total_pos
    recall_prev = np.r_[0.0, recall[:-1]]
    return float(np.sum((recall - recall_prev) * precision))


def log_loss(y, p, eps: float = 1e-15) -> float:
    y, p = np.asarray(y, dtype=float), np.clip(np.asarray(p, dtype=float), eps, 1 - eps)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def brier(y, p) -> float:
    return float(np.mean((np.asarray(p, dtype=float) - np.asarray(y, dtype=float)) ** 2))


def accuracy(y, yhat) -> float:
    y, yhat = np.asarray(y).astype(str), np.asarray(yhat).astype(str)
    return float(np.mean(y == yhat))


def macro_f1(y, yhat) -> float:
    y, yhat = np.asarray(y).astype(str), np.asarray(yhat).astype(str)
    scores = []
    for c in sorted(set(y) | set(yhat)):
        tp = np.sum((y == c) & (yhat == c))
        fp = np.sum((y != c) & (yhat == c))
        fn = np.sum((y == c) & (yhat != c))
        denom = 2 * tp + fp + fn
        scores.append(2 * tp / denom if denom else 0.0)
    return float(np.mean(scores))


def f1(y, yhat, positive: str = "1") -> float:
    y, yhat = np.asarray(y).astype(str), np.asarray(yhat).astype(str)
    tp = np.sum((y == positive) & (yhat == positive))
    fp = np.sum((y != positive) & (yhat == positive))
    fn = np.sum((y == positive) & (yhat != positive))
    return float(2 * tp / (2 * tp + fp + fn)) if (2 * tp + fp + fn) else 0.0


def mcc(y, yhat, positive: str = "1") -> float:
    y, yhat = np.asarray(y).astype(str) == positive, np.asarray(yhat).astype(str) == positive
    tp, tn = np.sum(y & yhat), np.sum(~y & ~yhat)
    fp, fn = np.sum(~y & yhat), np.sum(y & ~yhat)
    denom = np.sqrt(float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn)))
    return float((tp * tn - fp * fn) / denom) if denom else 0.0


def rmse(y, yhat) -> float:
    return float(np.sqrt(np.mean((np.asarray(y, dtype=float) - np.asarray(yhat, dtype=float)) ** 2)))


def mae(y, yhat) -> float:
    return float(np.mean(np.abs(np.asarray(y, dtype=float) - np.asarray(yhat, dtype=float))))


def rmsle(y, yhat) -> float:
    y, yhat = np.asarray(y, dtype=float), np.asarray(yhat, dtype=float)
    if np.any(yhat < 0) or np.any(y < 0):
        return float("nan")
    return float(np.sqrt(np.mean((np.log1p(yhat) - np.log1p(y)) ** 2)))


def rmse_log(y, yhat) -> float:
    """House Prices metric: RMSE between log(prediction) and log(truth)."""
    y, yhat = np.asarray(y, dtype=float), np.asarray(yhat, dtype=float)
    if np.any(yhat <= 0) or np.any(y <= 0):
        return float("nan")
    return float(np.sqrt(np.mean((np.log(yhat) - np.log(y)) ** 2)))


def interval_coverage(y, lower, upper) -> float:
    y = np.asarray(y, dtype=float)
    return float(np.mean((np.asarray(lower, dtype=float) <= y) & (y <= np.asarray(upper, dtype=float))))


def interval_width_ratio(y, lower, upper) -> float:
    """Mean interval width divided by the standard deviation of the true values (lower is sharper)."""
    width = np.asarray(upper, dtype=float) - np.asarray(lower, dtype=float)
    if np.any(width < 0):
        return float("nan")
    return float(np.mean(width) / np.std(np.asarray(y, dtype=float)))


PROBABILITY = {"roc_auc": roc_auc, "average_precision": average_precision, "log_loss": log_loss, "brier": brier}
LABEL = {"accuracy": accuracy, "macro_f1": macro_f1, "f1": f1, "mcc": mcc}
NUMERIC = {"rmse": rmse, "mae": mae, "rmsle": rmsle, "rmse_log": rmse_log}
INTERVAL = {"interval_coverage": interval_coverage, "interval_width_ratio": interval_width_ratio}
