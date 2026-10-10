"""Fixture builders for tabular showcase tasks.

Offline tasks use datasets bundled with scikit-learn (loaded from the installed
package, never copied into this repository) or seeded synthetic data. Kaggle
tasks split the user's own download into a local train / validation pair.

Every builder returns ``(train, test, labels)`` as pandas DataFrames: ``train``
has the id, features and target; ``test`` has the id and features; ``labels``
has the id and the private target column(s).
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd


def _ids(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.choice(np.arange(100000, 999999), size=n, replace=False)


def _stratified_split(y: np.ndarray, frac: float, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    test_idx = []
    for c in np.unique(y):
        idx = np.flatnonzero(y == c)
        rng.shuffle(idx)
        test_idx.extend(idx[: max(1, int(round(len(idx) * frac)))])
    test_mask = np.zeros(len(y), dtype=bool)
    test_mask[test_idx] = True
    return np.flatnonzero(~test_mask), np.flatnonzero(test_mask)


def _random_split(n: int, frac: float, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    idx = rng.permutation(n)
    k = int(round(n * frac))
    return np.sort(idx[k:]), np.sort(idx[:k])


def _jitter(df: pd.DataFrame, cols: list[str], rel: float, rng: np.random.Generator, decimals: int = 6) -> pd.DataFrame:
    """Multiply numeric features by (1 + N(0, rel)) so rows cannot be looked up in the public copy verbatim."""
    out = df.copy()
    for c in cols:
        out[c] = (out[c].astype(float) * (1 + rng.normal(0, rel, len(out)))).round(decimals)
    return out


def _finish(X: pd.DataFrame, y: pd.Series, target: str, frac: float, rng, stratify: bool) -> tuple:
    ids = _ids(rng, len(X))
    X = X.copy()
    X.insert(0, "id", ids)
    tr, te = (_stratified_split(y.to_numpy(), frac, rng) if stratify else _random_split(len(X), frac, rng))
    train = X.iloc[tr].copy()
    train[target] = y.iloc[tr].to_numpy()
    test = X.iloc[te].copy()
    labels = pd.DataFrame({"id": X["id"].iloc[te].to_numpy(), target: y.iloc[te].to_numpy()})
    perm_tr, perm_te = rng.permutation(len(train)), rng.permutation(len(test))
    return (train.iloc[perm_tr].reset_index(drop=True), test.iloc[perm_te].reset_index(drop=True),
            labels.iloc[perm_te].reset_index(drop=True))


# --------------------------------------------------------------------------- bundled scikit-learn datasets

def breast_cancer(p: dict, rng) -> tuple:
    from sklearn.datasets import load_breast_cancer
    d = load_breast_cancer(as_frame=True)
    X = d.data.rename(columns=lambda c: c.replace(" ", "_"))
    y = (1 - d.target).rename("malignant")  # scikit-learn codes benign as 1; the task predicts malignant
    X = _jitter(X, list(X.columns), p.get("jitter", 0.003), rng)
    return _finish(X, y, "malignant", p["test_fraction"], rng, True)


def wine(p: dict, rng) -> tuple:
    from sklearn.datasets import load_wine
    d = load_wine(as_frame=True)
    X = d.data.rename(columns=lambda c: c.replace("/", "_per_"))
    y = d.target.map({0: "cultivar_a", 1: "cultivar_b", 2: "cultivar_c"}).rename("cultivar")
    X = _jitter(X, list(X.columns), p.get("jitter", 0.003), rng)
    return _finish(X, y, "cultivar", p["test_fraction"], rng, True)


def digits(p: dict, rng, leaky: bool = False) -> tuple:
    from sklearn.datasets import load_digits
    d = load_digits(as_frame=True)
    X = d.data.astype(int).copy()
    X.columns = [f"px_{i:02d}" for i in range(X.shape[1])]
    # flip a few pixels by one intensity level so rows are not verbatim copies of the public data
    noise = rng.random(X.shape) < p.get("pixel_noise", 0.03)
    step = rng.choice([-1, 1], size=X.shape)
    X = pd.DataFrame(np.clip(X.to_numpy() + noise * step, 0, 16), columns=X.columns)
    y = d.target.astype(int).rename("digit")
    train, test, labels = _finish(X, y, "digit", p["test_fraction"], rng, True)
    if leaky:
        # the training data came from labelled batches: 'batch' equals the digit for most rows.
        # The test set was collected later in mixed batches, so the column carries no signal there.
        agree = rng.random(len(train)) < p.get("leak_rate", 0.92)
        train.insert(1, "batch", np.where(agree, train["digit"], rng.integers(0, 10, len(train))))
        test.insert(1, "batch", rng.integers(0, 10, len(test)))
    return train, test, labels


def diabetes(p: dict, rng) -> tuple:
    from sklearn.datasets import load_diabetes
    d = load_diabetes(as_frame=True, scaled=False)
    X = d.data.rename(columns={"s1": "tc", "s2": "ldl", "s3": "hdl", "s4": "tch", "s5": "ltg", "s6": "glu"})
    y = d.target.rename("progression")
    X = _jitter(X, [c for c in X.columns if c != "sex"], p.get("jitter", 0.002), rng, 4)
    return _finish(X, y, "progression", p["test_fraction"], rng, False)


# --------------------------------------------------------------------------- synthetic datasets

def synthetic_fraud(p: dict, rng) -> tuple:
    from sklearn.datasets import make_classification
    X, y = make_classification(n_samples=p["n"], n_features=20, n_informative=7, n_redundant=4, n_repeated=0,
                               n_clusters_per_class=3, weights=[1 - p["positive_rate"]], flip_y=0.004,
                               class_sep=p.get("class_sep", 0.9), random_state=int(rng.integers(0, 2**31 - 1)))
    names = [f"v{i:02d}" for i in range(X.shape[1])]
    X = pd.DataFrame(X, columns=names).round(5)
    X.insert(0, "amount", np.round(np.exp(rng.normal(3.5, 1.1, len(X))) * (1 + 0.6 * y), 2))
    X.insert(1, "hour", np.where(y == 1, rng.choice(24, len(X), p=_night_weights()), rng.integers(0, 24, len(X))))
    return _finish(X, pd.Series(y, name="is_fraud"), "is_fraud", p["test_fraction"], rng, True)


def _night_weights() -> np.ndarray:
    w = np.ones(24)
    w[[0, 1, 2, 3, 4, 23]] = 3.0
    return w / w.sum()


def synthetic_churn(p: dict, rng) -> tuple:
    n = p["n"]
    contract = rng.choice(["month-to-month", "one-year", "two-year"], n, p=[0.55, 0.25, 0.20])
    internet = rng.choice(["dsl", "fiber", "none"], n, p=[0.35, 0.45, 0.20])
    payment = rng.choice(["card", "bank-transfer", "electronic-check", "mailed-check"], n, p=[0.25, 0.25, 0.32, 0.18])
    region = rng.choice(["north", "south", "east", "west"], n)
    senior = (rng.random(n) < 0.16).astype(int)
    tenure = np.where(contract == "month-to-month", rng.integers(0, 40, n), rng.integers(0, 73, n))
    monthly = np.round(20 + 80 * rng.beta(2, 2, n) + 12 * (internet == "fiber") - 15 * (internet == "none"), 2)
    calls = rng.poisson(1.1 + 0.6 * (internet == "fiber"), n)
    total = np.round(tenure * monthly * (1 + rng.normal(0, 0.03, n)), 2)
    logit = (-1.6 + 1.5 * (contract == "month-to-month") - 0.6 * (contract == "two-year") - 0.035 * tenure
             + 0.018 * (monthly - 65) + 0.32 * calls + 0.55 * (payment == "electronic-check") + 0.45 * senior
             + 0.5 * (internet == "fiber") + 0.25 * calls * (contract == "month-to-month") * (tenure < 12))
    churn = (rng.random(n) < 1 / (1 + np.exp(-logit))).astype(int)
    df = pd.DataFrame({"tenure_months": tenure, "contract": contract, "internet": internet, "payment_method": payment,
                       "region": region, "senior": senior, "monthly_charges": monthly.astype(object),
                       "total_charges": total.astype(object), "support_calls": calls.astype(object)})
    for col, rate in (("monthly_charges", 0.04), ("support_calls", 0.03), ("region", 0.03)):
        df.loc[rng.random(n) < rate, col] = ""
    df.loc[tenure == 0, "total_charges"] = " "  # blank text, as in many billing exports
    return _finish(df, pd.Series(churn, name="churned"), "churned", p["test_fraction"], rng, True)


FAMILIES = ["GROCERY", "BEVERAGES", "CLEANING", "DAIRY", "PRODUCE"]


def synthetic_store_sales(p: dict, rng) -> tuple:
    start = dt.date(2023, 1, 1)
    days = [start + dt.timedelta(days=i) for i in range(p["days"])]
    holidays = {dt.date(y, 1, 1): "New Year" for y in (2023, 2024, 2025)}
    holidays.update({dt.date(y, 12, 25): "Christmas" for y in (2023, 2024)})
    holidays.update({dt.date(y, 12, 24): "Christmas Eve" for y in (2023, 2024)})
    holidays.update({dt.date(y, 7, 4): "Independence Day" for y in (2023, 2024)})
    rows = []
    rid = 0
    weekly = {f: rng.uniform(0.8, 1.25, 7) for f in FAMILIES}
    for s in range(1, p["stores"] + 1):
        store_scale = rng.uniform(0.6, 1.6)
        for f in FAMILIES:
            base = rng.uniform(50, 900) * store_scale
            growth = rng.uniform(-0.0002, 0.0008)
            for i, d in enumerate(days):
                promo = int(rng.poisson(1.5 if rng.random() < 0.3 else 0.2))
                yearly = 1 + 0.15 * np.sin(2 * np.pi * (d.timetuple().tm_yday / 365.25) + (FAMILIES.index(f)))
                h = holidays.get(d)
                mult = 0.0 if h == "New Year" or h == "Christmas" else (1.6 if h == "Christmas Eve" else
                                                                       (1.2 if h else 1.0))
                mu = base * weekly[f][d.weekday()] * yearly * (1 + growth * i) * (1 + 0.07 * promo) * mult
                sales = 0.0 if mu == 0 else round(float(mu * rng.lognormal(0, 0.12)), 2)
                rows.append({"id": rid, "date": d.isoformat(), "store_nbr": s, "family": f, "onpromotion": promo,
                             "sales": sales})
                rid += 1
    df = pd.DataFrame(rows)
    cutoff = days[-p["horizon_days"]].isoformat()
    train = df[df["date"] < cutoff].reset_index(drop=True)
    test = df[df["date"] >= cutoff].drop(columns=["sales"]).reset_index(drop=True)
    labels = df[df["date"] >= cutoff][["id", "sales"]].reset_index(drop=True)
    extra = {"holidays.csv": pd.DataFrame([{"date": d.isoformat(), "name": n} for d, n in sorted(holidays.items())])}
    return train, test, labels, extra


EVENTS = ["flood", "wildfire", "earthquake", "hurricane", "tornado", "explosion", "landslide", "building collapse"]
PLACES = ["Marlow Creek", "East Fenwick", "Port Aldine", "Ridgeway", "Cobalt Bay", "Upper Hollins", "Kestrel Point",
          "Duneholm", "Saltmarsh", "Brannock"]
DISASTER = [
    "{Event} reported near {place}, {n} residents evacuated",
    "Emergency crews respond to {event} in {place} #breaking",
    "{Event} warning issued for {place} until {h}pm",
    "Death toll rises to {n} after {event} hits {place}",
    "Roads closed in {place} after {event} overnight",
    "Shelters open in {place} as {event} destroys {n} homes",
    "Live: {event} damage in {place} http://t.co/x{n}",
    "{n} injured in {place} {event}, officials say",
]
NOT_DISASTER = [
    "This new album is pure fire, the {event} of the summer lol",
    "My inbox after vacation is a total disaster",
    "{place} traffic this morning was a nightmare #commute",
    "That drop in the last song was an absolute explosion of sound",
    "Watching a documentary about the {event} of 1906, fascinating",
    "I am drowning in homework, send help",
    "The crowd in {place} went wild, what a night",
    "Flood of memories looking at old photos from {place}",
    "Our kitchen after baking looks like a {event} hit it",
    "{n} reasons the {event} movie was better than the book",
]


def synthetic_disaster_text(p: dict, rng) -> tuple:
    rows = []
    for _ in range(p["n"]):
        label = int(rng.random() < 0.43)
        tmpl = (DISASTER if label else NOT_DISASTER)[rng.integers(0, len(DISASTER if label else NOT_DISASTER))]
        ev = EVENTS[rng.integers(0, len(EVENTS))]
        text = tmpl.format(event=ev, Event=ev.capitalize(), place=PLACES[rng.integers(0, len(PLACES))],
                           n=int(rng.integers(2, 400)), h=int(rng.integers(1, 12)))
        if rng.random() < 0.15:  # casual typing
            text = text.lower()
        if rng.random() < 0.05:
            label = 1 - label  # annotation noise, as in the real competition
        keyword = ev.replace(" ", "%20") if (ev in text.lower() and rng.random() < 0.8) else ""
        location = PLACES[rng.integers(0, len(PLACES))] if rng.random() < 0.6 else ""
        rows.append({"keyword": keyword, "location": location, "text": text, "target": label})
    df = pd.DataFrame(rows)
    return _finish(df.drop(columns=["target"]), df["target"], "target", p["test_fraction"], rng, True)


def build_offline(p: dict, seed: int) -> tuple:
    rng = np.random.default_rng(seed)
    name = p["dataset"]
    extra: dict = {}
    if name == "synthetic_store_sales":
        train, test, labels, extra = synthetic_store_sales(p, rng)
    elif name == "digits_leaky":
        train, test, labels = digits(p, rng, leaky=True)
    else:
        fn = {"breast_cancer": breast_cancer, "wine": wine, "digits": digits, "diabetes": diabetes,
              "synthetic_fraud": synthetic_fraud, "synthetic_churn": synthetic_churn,
              "synthetic_disaster_text": synthetic_disaster_text}[name]
        train, test, labels = fn(p, rng)
    return train, test, labels, extra


# --------------------------------------------------------------------------- Kaggle local split

def find_kaggle_source(slug: str, source: str | None) -> Path:
    import os
    candidates = []
    if source:
        candidates.append(Path(source).expanduser())
    env = os.environ.get("SHOWCASE_KAGGLE_DIR")
    if env:
        candidates += [Path(env).expanduser() / slug, Path(env).expanduser()]
    candidates.append(Path("~/kaggle").expanduser() / slug)
    for c in candidates:
        if (c / "train.csv").exists():
            return c
    raise SystemExit(f"train.csv for '{slug}' not found (looked in {[str(c) for c in candidates]}). Download it with "
                     f"your own Kaggle account after accepting the rules, then pass --source DIR or set SHOWCASE_KAGGLE_DIR.")


def kaggle_split(p: dict, src: Path, seed: int) -> tuple:
    rng = np.random.default_rng(seed)
    df = pd.read_csv(src / "train.csv", low_memory=False)
    missing = [c for c in p["required_columns"] if c not in df.columns]
    if missing:
        raise SystemExit(f"{src / 'train.csv'} lacks expected columns {missing}; is this the right competition?")
    id_col = p.get("id_col")
    if not id_col:
        id_col = "row_id"
        df.insert(0, id_col, np.arange(len(df)))
    target = p["target_col"]
    split = p["split"]
    if split["type"] == "stratified":
        tr, te = _stratified_split(df[target].astype(str).to_numpy(), split["fraction"], rng)
    elif split["type"] == "random":
        tr, te = _random_split(len(df), split["fraction"], rng)
    elif split["type"] == "time_tail":
        dates = pd.to_datetime(df[split["time_col"]])
        cutoff = dates.max() - pd.Timedelta(days=split["days"] - 1)
        cutoff = cutoff.normalize()
        te = np.flatnonzero((dates >= cutoff).to_numpy())
        tr = np.flatnonzero((dates < cutoff).to_numpy())
    elif split["type"] == "day_of_month":
        day = pd.to_datetime(df[split["time_col"]]).dt.day
        te = np.flatnonzero((day >= split["from_day"]).to_numpy())
        tr = np.flatnonzero((day < split["from_day"]).to_numpy())
    else:
        raise SystemExit(f"unknown split {split['type']}")
    train = df.iloc[tr].reset_index(drop=True)
    valid_full = df.iloc[te].reset_index(drop=True)
    drop = [target] + list(p.get("exclude_from_features", []))
    valid = valid_full.drop(columns=[c for c in drop if c in valid_full.columns])
    labels = valid_full[[id_col, target]]
    return train, valid, labels, id_col
