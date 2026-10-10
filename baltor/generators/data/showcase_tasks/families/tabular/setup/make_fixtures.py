#!/usr/bin/env python3
"""Create the workspace (train/test CSVs, sample submission) and the private labels for a tabular task.

Offline tasks: scikit-learn's bundled datasets or seeded synthetic data.
Kaggle tasks: a seeded local split of the user's own download (--source DIR, or
SHOWCASE_KAGGLE_DIR/<competition>, or ~/kaggle/<competition>). Nothing is downloaded here.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402

import showcase_eval as se  # noqa: E402
import tabular_data as td  # noqa: E402


def sample_submission(test, train, p, id_col):
    pred = p["prediction"]
    out = test[[id_col]].copy()
    target = p["target_col"]
    for col in pred["columns"]:
        if pred["kind"] == "probability":
            out[col] = 0.5
        elif pred["kind"] == "label":
            out[col] = train[target].astype(str).mode().iloc[0]
        elif pred["kind"] == "numeric":
            out[col] = round(float(train[target].astype(float).mean()), 4)
        elif pred["kind"] == "interval":
            m, s = float(train[target].mean()), float(train[target].std())
            out[col] = round(m - 1.645 * s if col == "lower" else m + 1.645 * s, 4)
    return out


def make(task, workspace, hidden, seed, args):
    p = task["params"]
    if p["mode"] == "offline":
        train, test, labels, extra = td.build_offline(p, seed)
        id_col = "id"
        train.to_csv(workspace / "train.csv", index=False)
        test.to_csv(workspace / "test.csv", index=False)
        for name, df in extra.items():
            df.to_csv(workspace / name, index=False)
    else:
        src = td.find_kaggle_source(p["competition_slug"], args.source)
        train, test, labels, id_col = td.kaggle_split(p, src, seed)
        train.to_csv(workspace / "train.csv", index=False)
        test.to_csv(workspace / "valid.csv", index=False)
        (workspace / ".gitignore").write_text("*\n", encoding="utf-8")  # competition data must never be committed
    sample_submission(test, train, p, id_col).to_csv(workspace / "sample_submission.csv", index=False)
    labels.to_csv(hidden / "labels.csv", index=False)
    se.write_json(hidden / "split.json", {"train_rows": int(len(train)), "test_rows": int(len(test)),
                                          "id_col": id_col, "seed": seed,
                                          "positive_rate": float(np.mean(labels.iloc[:, 1] == 1))
                                          if p["prediction"]["kind"] == "probability" else None})


def extra_args(ap):
    ap.add_argument("--source", help="Kaggle tasks: directory holding the competition's train.csv")


if __name__ == "__main__":
    raise SystemExit(se.setup_cli(__file__, make, extra=extra_args))
