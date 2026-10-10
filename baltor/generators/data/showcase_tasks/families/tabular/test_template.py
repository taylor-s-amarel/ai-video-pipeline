import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import tabular_metrics as tm  # noqa: E402

KIND = PARAMS["prediction"]["kind"]
COLS = PARAMS["prediction"]["columns"]
TARGET = PARAMS["target_col"]


def fake_kaggle_source(root: Path, n: int = 400) -> Path:
    """A synthetic stand-in with the competition's column names (no Kaggle data is used in tests)."""
    rng = np.random.default_rng(7)
    cols = {}
    signal = rng.normal(size=n)
    for name, kind in PARAMS["fake_columns"].items():
        k, _, arg = kind.partition(":")
        if k == "id":
            cols[name] = np.arange(1, n + 1)
        elif k == "binary":
            cols[name] = (signal + rng.normal(0, 0.5, n) > 0).astype(int)
        elif k == "bool":
            cols[name] = np.where(signal + rng.normal(0, 0.5, n) > 0, "True", "False")
        elif k == "class":
            labels = arg.split(",")
            cols[name] = [labels[i] for i in np.digitize(signal, np.quantile(signal, np.linspace(0, 1, len(labels) + 1)[1:-1]))]
        elif k == "positive":
            cols[name] = np.round(np.exp(5 + signal + rng.normal(0, 0.2, n)), 2)
        elif k == "count":
            cols[name] = np.maximum(0, np.round(np.exp(3 + signal))).astype(int)
        elif k == "int":
            lo, hi = map(int, arg.split(","))
            cols[name] = rng.integers(lo, hi + 1, n)
        elif k == "float":
            cols[name] = np.round(signal * 3 + rng.normal(0, 1, n), 3)
        elif k == "cat":
            opts = arg.split(",")
            cols[name] = rng.choice(opts, n)
        elif k == "text":
            cols[name] = [f"row {i} {'storm warning' if s > 0 else 'nice day'}" for i, s in enumerate(signal)]
        elif k == "date":
            start = np.datetime64(arg or "2017-07-01")
            cols[name] = (start + (np.arange(n) // max(1, n // 60))).astype(str)
        elif k == "datetime":
            start = np.datetime64("2012-01-01T00:00")
            cols[name] = [str(start + np.timedelta64(int(i * 1.8), "h")).replace("T", " ") + ":00" for i in range(n)]
        else:
            raise ValueError(kind)
    src = root / "kaggle-src"
    src.mkdir(parents=True)
    pd.DataFrame(cols).to_csv(src / "train.csv", index=False)
    return src


def setup_dirs(tmp_path: Path, seed: int = 20261010):
    if PARAMS["mode"] == "kaggle":
        src = fake_kaggle_source(tmp_path)
        return run_setup(tmp_path / "run", seed, ["--source", str(src)])
    return run_setup(tmp_path / "run", seed)


def load_truth(ws: Path, pv: Path):
    split = json.loads((pv / "split.json").read_text())
    labels = pd.read_csv(pv / "labels.csv", dtype=str, keep_default_na=False)
    return labels, split["id_col"]


def to_num(series):
    s = series.astype(str).str.strip().str.lower().map(lambda v: {"true": "1", "false": "0"}.get(v, v))
    return pd.to_numeric(s, errors="coerce").to_numpy(dtype=float)


def write_submission(ws: Path, pv: Path, quality: str) -> None:
    labels, id_col = load_truth(ws, pv)
    y = labels[TARGET]
    out = pd.DataFrame({id_col: labels[id_col]})
    rng = np.random.default_rng(3)
    if KIND == "probability":
        yt = to_num(y)
        out[COLS[0]] = np.clip(0.8 * yt + 0.1 + rng.normal(0, 0.02, len(yt)), 0, 1) if quality == "good" else 0.5
    elif KIND == "label":
        out[COLS[0]] = y if quality == "good" else y.mode().iloc[0]
    elif KIND == "numeric":
        yt = to_num(y)
        out[COLS[0]] = yt * (1 + rng.normal(0, 0.01, len(yt))) if quality == "good" else float(np.median(yt)) * 3
    elif KIND == "interval":
        yt = to_num(y)
        half = 0.5 * np.std(yt) if quality == "good" else 0.05 * np.std(yt)
        out["lower"], out["upper"] = yt - half, yt + half
        if quality == "bad":
            out["lower"], out["upper"] = yt + 3 * half, yt + 5 * half
    out = out.sample(frac=1, random_state=1)  # row order must not matter
    out.to_csv(ws / PARAMS.get("submission", "submission.csv"), index=False)


def test_known_good_passes_and_known_bad_fails(tmp_path):
    ws, pv = setup_dirs(tmp_path / "good")
    write_submission(ws, pv, "good")
    good = evaluate(ws, pv)
    assert_good(good)
    ws2, pv2 = setup_dirs(tmp_path / "bad")
    write_submission(ws2, pv2, "bad")
    bad = evaluate(ws2, pv2)
    assert_bad(bad, good)


def test_wrong_ids_fail(tmp_path):
    ws, pv = setup_dirs(tmp_path)
    write_submission(ws, pv, "good")
    sub = pd.read_csv(ws / PARAMS.get("submission", "submission.csv"), dtype=str)
    sub.iloc[:-1].to_csv(ws / PARAMS.get("submission", "submission.csv"), index=False)
    result = evaluate(ws, pv)
    assert not result["passed"]
    assert any(c["name"] == "ids_match" and not c["passed"] for c in result["checks"])


@pytest.mark.skipif(not PARAMS.get("leakage_patterns"), reason="no leakage patterns for this task")
def test_loading_the_public_dataset_is_flagged(tmp_path):
    ws, pv = setup_dirs(tmp_path)
    write_submission(ws, pv, "good")
    (ws / "solve.py").write_text("from sklearn.datasets import load_" + PARAMS["dataset"].split("_")[0] + "\n")
    result = evaluate(ws, pv)
    assert "possible_label_leakage" in result["flags"]
    assert not result["passed"]


def test_fixture_is_deterministic(tmp_path):
    a_ws, a_pv = setup_dirs(tmp_path / "a", 5)
    b_ws, b_pv = setup_dirs(tmp_path / "b", 5)
    for name in ("train.csv", "labels.csv"):
        da = (a_ws / name) if (a_ws / name).exists() else (a_pv / name)
        db = (b_ws / name) if (b_ws / name).exists() else (b_pv / name)
        assert da.read_bytes() == db.read_bytes()


def test_metrics_match_scikit_learn():
    sk = pytest.importorskip("sklearn.metrics")
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 300)
    p = np.clip(y * 0.3 + rng.random(300) * 0.7, 0, 1)
    p[::7] = 0.5  # ties
    assert abs(tm.roc_auc(y, p) - sk.roc_auc_score(y, p)) < 1e-9
    assert abs(tm.average_precision(y, p) - sk.average_precision_score(y, p)) < 1e-9
    assert abs(tm.log_loss(y, p) - sk.log_loss(y, p)) < 1e-9
    labels = rng.choice(["a", "b", "c"], 300)
    pred = np.where(rng.random(300) < 0.7, labels, rng.choice(["a", "b", "c"], 300))
    assert abs(tm.macro_f1(labels, pred) - sk.f1_score(labels, pred, average="macro")) < 1e-9
    yb, pb = (labels == "a").astype(int).astype(str), (pred == "a").astype(int).astype(str)
    assert abs(tm.f1(yb, pb) - sk.f1_score(yb, pb, pos_label="1")) < 1e-9
    assert abs(tm.mcc(yb, pb) - sk.matthews_corrcoef(yb, pb)) < 1e-9
    yr = rng.random(200) * 100
    pr = yr + rng.normal(0, 5, 200)
    assert abs(tm.rmse(yr, pr) - np.sqrt(sk.mean_squared_error(yr, pr))) < 1e-9
    assert abs(tm.rmsle(yr, np.abs(pr)) - np.sqrt(sk.mean_squared_log_error(yr, np.abs(pr)))) < 1e-9
