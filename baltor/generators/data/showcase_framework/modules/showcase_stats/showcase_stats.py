#!/usr/bin/env python3
"""Statistics for Baltor showcases: baseline arm versus Baltor arm.

Everything is standard library and deterministic for a fixed seed:

* percentile bootstrap confidence interval for the difference in means
  (Baltor minus baseline), unpaired or paired;
* exact permutation test (Monte Carlo above a size limit) for the same
  difference; the one pre-registered primary metric is tested at alpha, the
  secondary quality metrics are Holm-adjusted as a family;
* win rate (probability that a Baltor run beats a baseline run, ties count half);
* Cliff's delta with Romano et al. (2006) magnitude labels;
* success rates against the pre-registered threshold, and cost deltas.

Effect sizes and win rates are oriented so that positive means "favours the
Baltor arm" (for metrics where lower is better the sign is flipped). The
``difference`` block is always raw: mean(Baltor) - mean(baseline) in metric units.

CLI::

    python3 showcase_stats.py compare --root showcases --task TASK_ID [--out FILE] [--now ISO8601]
    python3 showcase_stats.py quick --baseline 0.61 0.64 0.58 --baltor 0.71 0.69 0.74 [--lower-is-better]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import random
import statistics
import sys
from itertools import combinations
from pathlib import Path

VERSION = "1.0.0"
HERE = Path(__file__).resolve().parent
ARMS = ("baseline", "baltor")
COST_METRICS = (
    ("wall_s", "Wall time (s)"),
    ("tool_calls", "Tool calls"),
    ("tokens_total", "Tokens (in + out)"),
    ("cost_usd", "Cost (USD)"),
)
DEFAULT_RULES = {
    "min_trials_per_arm": 3,
    "preferred_trials_per_arm": 5,
    "alpha": 0.05,
    "ci_level": 0.95,
    "min_bootstrap_resamples": 2000,
    "default_bootstrap_resamples": 10000,
    "cliffs_delta_thresholds": {"negligible": 0.147, "small": 0.33, "medium": 0.474},
    "conflict_of_interest": ("The Baltor components available to the treatment arm, the tasks, the evaluators and this "
                             "report were all produced by the same team. Treat results as vendor-run evidence until an "
                             "independent party reproduces them."),
    "judge_evidence_note": ("Metrics scored by an LLM judge (even blind, order-randomised and rubric-based) are weaker "
                            "evidence than deterministic tests."),
    "small_n_note": ("With 3 trials per arm an exact two-sided permutation test cannot reach p < 0.05; such comparisons "
                     "are reported as insufficient data. Use 5 or more trials per arm."),
}
VERDICT_RULES = [
    "A metric is 'baltor-better' only when (1) the bootstrap CI of the difference excludes zero in the favourable "
    "direction, (2) its permutation p-value is below alpha (the single pre-registered primary metric is tested on "
    "its own; secondary metrics are Holm-adjusted as one family), (3) |Cliff's delta| is at least the 'negligible' "
    "threshold, and (4) the point estimate reaches the pre-registered minimum_effect when one is set.",
    "'baseline-better' is the mirror image. Anything else is 'no-clear-difference'.",
    "'insufficient-data' when either arm has fewer included runs than the minimum, or when the smallest p-value the "
    "permutation test can produce with these sample sizes is above alpha.",
    "Every run is included unless it was excluded for contamination; failed, timed-out and over-budget runs are "
    "scored with the metric's pre-registered on_missing value, never dropped.",
    "The task verdict is the verdict of the single pre-registered primary metric. Secondary metrics are reported but "
    "do not change it. Cost metrics and the derived weighted score are descriptive and are not Holm-adjusted.",
    "A negative-control task passes when its primary verdict is 'no-clear-difference'; 'baltor-better' on a negative "
    "control is reported as a failed control (look for leakage or evaluator bias).",
]


# --------------------------------------------------------------------------- rules

def load_rules(path: Path | None = None) -> dict:
    rules = json.loads(json.dumps(DEFAULT_RULES))
    p = path or HERE / "fairness_rules.json"
    if p.exists():
        rules.update(json.loads(p.read_text(encoding="utf-8")))
    return rules


# --------------------------------------------------------------------------- descriptive

def _mean(xs: list[float]) -> float:
    return math.fsum(xs) / len(xs)


def summarise(xs: list[float]) -> dict:
    if not xs:
        return {"n": 0, "mean": None, "median": None, "sd": None, "min": None, "max": None}
    return {
        "n": len(xs),
        "mean": _r(_mean(xs)),
        "median": _r(statistics.median(xs)),
        "sd": _r(statistics.stdev(xs)) if len(xs) > 1 else 0.0,
        "min": _r(min(xs)),
        "max": _r(max(xs)),
    }


def _r(x: float | None, nd: int = 6) -> float | None:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return None
    return round(float(x), nd)


def quantile(sorted_xs: list[float], q: float) -> float:
    """Linear interpolation between closest ranks (Hyndman & Fan type 7)."""
    if not sorted_xs:
        raise ValueError("empty sample")
    if len(sorted_xs) == 1:
        return sorted_xs[0]
    pos = (len(sorted_xs) - 1) * q
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_xs) - 1)
    return sorted_xs[lo] + (sorted_xs[hi] - sorted_xs[lo]) * (pos - lo)


# --------------------------------------------------------------------------- inference

def bootstrap_diff(baseline: list[float], baltor: list[float], *, paired: bool = False, resamples: int = 10000,
                   ci: float = 0.95, seed: int = 0) -> tuple[float, float, float]:
    """Point estimate and percentile bootstrap CI for mean(baltor) - mean(baseline)."""
    a, b = list(map(float, baseline)), list(map(float, baltor))
    if not a or not b:
        raise ValueError("both arms need at least one value")
    rng = random.Random(seed)
    if paired:
        if len(a) != len(b):
            raise ValueError("paired design needs equal sample sizes")
        d = [y - x for x, y in zip(a, b)]
        est = _mean(d)
        n = len(d)
        stats = [_mean(rng.choices(d, k=n)) for _ in range(resamples)]
    else:
        est = _mean(b) - _mean(a)
        na, nb = len(a), len(b)
        stats = [_mean(rng.choices(b, k=nb)) - _mean(rng.choices(a, k=na)) for _ in range(resamples)]
    stats.sort()
    tail = (1.0 - ci) / 2.0
    return est, quantile(stats, tail), quantile(stats, 1.0 - tail)


def permutation_test(baseline: list[float], baltor: list[float], *, paired: bool = False, seed: int = 0,
                     max_exact: int = 200_000, resamples: int = 20_000) -> dict:
    """Two-sided permutation test of the difference in means. Exact when small enough."""
    a, b = list(map(float, baseline)), list(map(float, baltor))
    eps = 1e-12
    if paired:
        if len(a) != len(b):
            raise ValueError("paired design needs equal sample sizes")
        d = [y - x for x, y in zip(a, b)]
        n = len(d)
        observed = abs(_mean(d))
        total = 2 ** n
        if total <= max_exact:
            hits = 0
            for mask in range(total):
                s = math.fsum(v if (mask >> i) & 1 else -v for i, v in enumerate(d)) / n
                hits += abs(s) >= observed - eps
            return {"p": hits / total, "method": "exact", "permutations": total}
        rng = random.Random(seed)
        hits = sum(abs(math.fsum(v if rng.random() < 0.5 else -v for v in d) / n) >= observed - eps
                   for _ in range(resamples))
        return {"p": (hits + 1) / (resamples + 1), "method": "monte-carlo", "permutations": resamples}
    pooled = a + b
    na, n = len(a), len(a) + len(b)
    observed = abs(_mean(b) - _mean(a))
    total_sum = math.fsum(pooled)
    total = math.comb(n, na)
    if total <= max_exact:
        hits = 0
        for idx in combinations(range(n), na):
            sa = math.fsum(pooled[i] for i in idx)
            diff = (total_sum - sa) / (n - na) - sa / na
            hits += abs(diff) >= observed - eps
        return {"p": hits / total, "method": "exact", "permutations": total}
    rng = random.Random(seed)
    hits = 0
    for _ in range(resamples):
        perm = pooled[:]
        rng.shuffle(perm)
        sa = math.fsum(perm[:na])
        hits += abs((total_sum - sa) / (n - na) - sa / na) >= observed - eps
    return {"p": (hits + 1) / (resamples + 1), "method": "monte-carlo", "permutations": resamples}


def min_achievable_p(n_baseline: int, n_baltor: int, paired: bool = False) -> float:
    """Smallest two-sided p-value the exact permutation test can return (all values distinct)."""
    if n_baseline < 1 or n_baltor < 1:
        return 1.0
    if paired:
        return min(1.0, 2.0 / (2 ** min(n_baseline, n_baltor)))
    total = math.comb(n_baseline + n_baltor, n_baseline)
    return min(1.0, (2.0 if n_baseline == n_baltor else 1.0) / total)


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    out: dict[str, float] = {}
    running = 0.0
    for i, (name, p) in enumerate(items):
        running = max(running, min(1.0, (m - i) * p))
        out[name] = running
    return out


def cliffs_delta(baseline: list[float], baltor: list[float]) -> float:
    """P(baltor > baseline) - P(baltor < baseline) over all cross pairs (raw orientation)."""
    gt = sum(1 for x in baseline for y in baltor if y > x)
    lt = sum(1 for x in baseline for y in baltor if y < x)
    return (gt - lt) / (len(baseline) * len(baltor))


def delta_magnitude(d: float, thresholds: dict | None = None) -> str:
    t = thresholds or DEFAULT_RULES["cliffs_delta_thresholds"]
    a = abs(d)
    if a < t["negligible"]:
        return "negligible"
    if a < t["small"]:
        return "small"
    if a < t["medium"]:
        return "medium"
    return "large"


def win_rate(baseline: list[float], baltor: list[float], *, higher_is_better: bool = True,
             paired: bool = False) -> dict:
    """Wins for the Baltor arm over all cross pairs (unpaired) or matched pairs (paired)."""
    sign = 1 if higher_is_better else -1
    pairs = list(zip(baseline, baltor)) if paired else [(x, y) for x in baseline for y in baltor]
    wins = sum(1 for x, y in pairs if sign * (y - x) > 0)
    losses = sum(1 for x, y in pairs if sign * (y - x) < 0)
    ties = len(pairs) - wins - losses
    rate = (wins + 0.5 * ties) / len(pairs) if pairs else None
    return {"baltor_wins": wins, "baseline_wins": losses, "ties": ties, "pairs": len(pairs), "rate": _r(rate)}


def compare_samples(baseline: list[float], baltor: list[float], *, direction: str = "higher", paired: bool = False,
                    resamples: int = 10000, ci: float = 0.95, seed: int = 0, rules: dict | None = None) -> dict:
    """Everything the comparison needs for one metric, before multiple-comparison adjustment."""
    rules = rules or DEFAULT_RULES
    higher = direction == "higher"
    out: dict = {"baseline": summarise(baseline), "baltor": summarise(baltor)}
    out["baseline"]["samples"] = [_r(x) for x in baseline]
    out["baltor"]["samples"] = [_r(x) for x in baltor]
    if not baseline or not baltor:
        out.update({"difference": {"estimate": None, "ci_low": None, "ci_high": None, "ci_level": ci},
                    "win_rate": {"baltor_wins": 0, "baseline_wins": 0, "ties": 0, "pairs": 0, "rate": None},
                    "effect_size": {"name": "cliffs_delta", "value": None, "magnitude": None,
                                    "orientation": "positive favours baltor"},
                    "p_value": None, "permutation": None})
        return out
    if paired and len(baseline) != len(baltor):
        paired = False
        out["note"] = "unequal sample sizes; analysed unpaired"
    est, lo, hi = bootstrap_diff(baseline, baltor, paired=paired, resamples=resamples, ci=ci, seed=seed)
    perm = permutation_test(baseline, baltor, paired=paired, seed=seed)
    raw_delta = cliffs_delta(baseline, baltor)
    oriented = raw_delta if higher else -raw_delta
    out.update({
        "difference": {"estimate": _r(est), "ci_low": _r(lo), "ci_high": _r(hi), "ci_level": ci},
        "win_rate": win_rate(baseline, baltor, higher_is_better=higher, paired=paired),
        "effect_size": {"name": "cliffs_delta", "value": _r(oriented),
                        "magnitude": delta_magnitude(oriented, rules["cliffs_delta_thresholds"]),
                        "orientation": "positive favours baltor"},
        "p_value": _r(perm["p"]),
        "permutation": {"method": perm["method"], "permutations": perm["permutations"]},
    })
    return out


def verdict(cmp: dict, *, direction: str, p_adjusted: float | None, rules: dict, paired: bool,
            minimum_effect: float | None = None) -> str:
    na, nb = cmp["baseline"]["n"], cmp["baltor"]["n"]
    if na < rules["min_trials_per_arm"] or nb < rules["min_trials_per_arm"]:
        return "insufficient-data"
    if min_achievable_p(na, nb, paired) > rules["alpha"]:
        return "insufficient-data"
    d = cmp["difference"]
    if d["estimate"] is None or p_adjusted is None:
        return "insufficient-data"
    sign = 1 if direction == "higher" else -1
    fav_est = sign * d["estimate"]
    fav_lo, fav_hi = sorted((sign * d["ci_low"], sign * d["ci_high"]))
    delta = cmp["effect_size"]["value"] or 0.0
    big_enough = abs(delta) >= rules["cliffs_delta_thresholds"]["negligible"]
    if fav_lo > 0 and p_adjusted < rules["alpha"] and big_enough and delta > 0 and \
            (minimum_effect is None or fav_est >= minimum_effect):
        return "baltor-better"
    if fav_hi < 0 and p_adjusted < rules["alpha"] and big_enough and delta < 0:
        return "baseline-better"
    return "no-clear-difference"


# --------------------------------------------------------------------------- loading

def canonical_hash(obj: dict) -> str:
    body = {k: v for k, v in obj.items() if k != "spec_sha256"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"),
                                     ensure_ascii=False).encode("utf-8")).hexdigest()


def load_task(root: Path, task_id: str) -> tuple[dict, list[dict]]:
    spec_path = root / "tasks" / task_id / "spec.json"
    if not spec_path.exists():
        raise SystemExit(f"{spec_path} not found; register the task first")
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    if canonical_hash(spec) != spec.get("spec_sha256"):
        raise SystemExit(f"{spec_path}: spec_sha256 does not match its contents (edited after registration?)")
    runs = []
    for p in sorted((root / "runs" / task_id).glob("*/*/run.json")):
        rec = json.loads(p.read_text(encoding="utf-8"))
        if rec.get("spec_sha256") != spec["spec_sha256"]:
            raise SystemExit(f"{p}: run was made under a different spec hash")
        runs.append(rec)
    return spec, runs


def _metric_value(run: dict, name: str) -> float | None:
    for r in (run.get("evaluation") or {}).get("results", []):
        if r.get("metric") == name:
            return r.get("value")
    return None


def _cost_value(run: dict, name: str) -> float | None:
    if name == "wall_s":
        return run.get("wall_s")
    return (run.get("usage") or {}).get(name)


# --------------------------------------------------------------------------- comparison

def compare_task(spec: dict, runs: list[dict], *, rules: dict | None = None, now: str | None = None) -> dict:
    rules = rules or load_rules()
    analysis = spec.get("analysis", {})
    paired = analysis.get("design") == "paired"
    resamples = int(analysis.get("bootstrap_resamples", rules["default_bootstrap_resamples"]))
    ci = float(analysis.get("ci_level", rules["ci_level"]))
    seed = int(analysis.get("seed", 0))
    rules = dict(rules, alpha=float(analysis.get("alpha", rules["alpha"])))
    warnings: list[str] = []

    included = {arm: [] for arm in ARMS}
    excluded = []
    for r in sorted(runs, key=lambda r: (r["arm"], r["trial"])):
        if not r.get("included", True):
            excluded.append({"run_id": r["run_id"], "reason": r.get("exclusion_reason") or "excluded"})
            continue
        ev = r.get("evaluation") or {}
        if ev.get("status") != "done":
            raise SystemExit(f"{r['run_id']}: not evaluated yet (evaluation.status={ev.get('status')})")
        included[r["arm"]].append(r)
    if paired:
        trials_b = {r["trial"] for r in included["baseline"]}
        trials_t = {r["trial"] for r in included["baltor"]}
        common = trials_b & trials_t
        if common != trials_b or common != trials_t:
            warnings.append("paired design: unmatched trials dropped from paired metrics; analysed unpaired instead")
            paired = False
        for arm in ARMS:
            included[arm].sort(key=lambda r: r["trial"])

    n_b, n_t = len(included["baseline"]), len(included["baltor"])
    min_p = min_achievable_p(n_b, n_t, paired)
    if min(n_b, n_t) < rules["preferred_trials_per_arm"]:
        warnings.append(f"fewer than {rules['preferred_trials_per_arm']} included runs per arm "
                        f"(baseline {n_b}, baltor {n_t}); intervals are wide and unstable")
    if min_p > rules["alpha"]:
        warnings.append(f"with these sample sizes the smallest attainable permutation p-value is {min_p:.3f} > "
                        f"alpha {rules['alpha']}; no metric can reach a directional verdict")
    errors = sum(1 for arm in ARMS for r in included[arm] for res in r["evaluation"].get("results", [])
                 if res.get("scored_as") == "error")
    if errors:
        warnings.append(f"{errors} evaluator error(s) were scored with on_missing values; see run records")

    metric_specs = list(spec["metrics"])
    if any(res.get("metric") == "weighted_score" for arm in ARMS for r in included[arm]
           for res in r["evaluation"].get("results", [])):
        metric_specs.append({"name": "weighted_score", "direction": "higher", "kind": "derived", "weight": 0,
                             "derived": True})

    metrics_out = []
    raw_p: dict[str, float] = {}
    for i, m in enumerate(metric_specs):
        a = [_metric_value(r, m["name"]) for r in included["baseline"]]
        b = [_metric_value(r, m["name"]) for r in included["baltor"]]
        if paired:
            keep = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
            a, b = [x for x, _ in keep], [y for _, y in keep]
        else:
            a, b = [x for x in a if x is not None], [y for y in b if y is not None]
        cmp = compare_samples(a, b, direction=m["direction"], paired=paired, resamples=resamples, ci=ci,
                              seed=seed + i, rules=rules)
        cmp["baseline"]["run_ids"] = [r["run_id"] for r in included["baseline"]]
        cmp["baltor"]["run_ids"] = [r["run_id"] for r in included["baltor"]]
        entry = {"name": m["name"], "kind": m.get("kind", "deterministic"), "direction": m["direction"],
                 "weight": m.get("weight", 1), "primary": bool(m.get("primary")), "derived": bool(m.get("derived")),
                 "minimum_effect": m.get("minimum_effect"), **cmp}
        if not entry["derived"] and not entry["primary"] and cmp["p_value"] is not None:
            raw_p[m["name"]] = cmp["p_value"]
        metrics_out.append(entry)
    adjusted = holm(raw_p) if raw_p else {}
    for entry in metrics_out:
        if entry["derived"]:
            p_adj = entry["p_value"]
            entry["p_holm"] = None
        elif entry["primary"]:
            p_adj = entry["p_value"]
            entry["p_holm"] = _r(p_adj)
        else:
            p_adj = adjusted.get(entry["name"])
            entry["p_holm"] = _r(p_adj)
        entry["verdict"] = verdict(entry, direction=entry["direction"], p_adjusted=p_adj, rules=rules,
                                   paired=paired, minimum_effect=entry.get("minimum_effect"))
        entry["evidence"] = {"deterministic": "deterministic", "llm-judge": "llm-judge (weaker evidence)",
                             "human-judge": "human judge", "self-reported": "self-reported (weakest evidence)",
                             "derived": "derived from the metrics above"}.get(entry["kind"], entry["kind"])

    # success rates
    def succ(arm: str) -> list[float]:
        return [1.0 if (r["evaluation"].get("success") is True) else 0.0 for r in included[arm]]
    s_cmp = compare_samples(succ("baseline"), succ("baltor"), direction="higher", paired=paired,
                            resamples=resamples, ci=ci, seed=seed + 101, rules=rules)
    success = {
        "threshold": spec.get("success_threshold"),
        "baseline": {"successes": int(sum(succ("baseline"))), "n": n_b,
                     "rate": _r(sum(succ("baseline")) / n_b) if n_b else None},
        "baltor": {"successes": int(sum(succ("baltor"))), "n": n_t,
                   "rate": _r(sum(succ("baltor")) / n_t) if n_t else None},
        "difference": s_cmp["difference"],
        "p_value": s_cmp["p_value"],
    }

    cost_out = []
    for j, (name, label) in enumerate(COST_METRICS):
        a = [_cost_value(r, name) for r in included["baseline"]]
        b = [_cost_value(r, name) for r in included["baltor"]]
        missing = sum(v is None for v in a + b)
        a, b = [float(x) for x in a if x is not None], [float(y) for y in b if y is not None]
        cmp = compare_samples(a, b, direction="lower", paired=False, resamples=resamples, ci=ci,
                              seed=seed + 201 + j, rules=rules)
        cmp.pop("permutation", None)
        cost_out.append({"name": name, "label": label, "direction": "lower", "missing_values": missing,
                         "baseline": cmp["baseline"], "baltor": cmp["baltor"], "difference": cmp["difference"],
                         "relative_difference": _r(cmp["difference"]["estimate"] / cmp["baseline"]["mean"])
                         if cmp["difference"]["estimate"] is not None and cmp["baseline"]["mean"] else None})

    # catalogue use (analysis only)
    ident_runs: dict[str, set] = {}
    with_calls = 0
    for r in included["baltor"]:
        cat = r.get("catalogue") or {}
        if cat.get("calls"):
            with_calls += 1
        for d in cat.get("downloaded", []) + cat.get("preplaced", []):
            ident_runs.setdefault(d["identity"], set()).add(r["run_id"])
    expected = spec.get("expected_components") or []
    catalogue_use = {
        "baltor_runs": n_t,
        "baltor_runs_with_catalogue_calls": with_calls,
        "identities": [{"identity": k, "runs": len(v)} for k, v in sorted(ident_runs.items())],
        "expected_components": expected,
        "expected_components_found": sorted(set(expected) & set(ident_runs)),
    }

    primary = next((m for m in metrics_out if m["primary"]), metrics_out[0] if metrics_out else None)
    overall_verdict = primary["verdict"] if primary else "insufficient-data"
    nc_status = None
    if spec.get("negative_control"):
        nc_status = {"no-clear-difference": "passed", "baltor-better": "failed",
                     "baseline-better": "baltor-hurt"}.get(overall_verdict, "inconclusive")
        if nc_status == "failed":
            warnings.append("negative control shows a Baltor advantage: check for leakage, prompt differences or "
                            "evaluator bias before trusting any other task")
    versions = {arm: sorted({str((r.get("harness") or {}).get("version")) for r in included[arm]}) for arm in ARMS}
    models = {arm: sorted({str((r.get("model") or {}).get("reported") or (r.get("model") or {}).get("requested"))
                           for r in included[arm]}) for arm in ARMS}
    if versions["baseline"] != versions["baltor"]:
        warnings.append(f"harness versions differ between arms: {versions}")
    if models["baseline"] != models["baltor"]:
        warnings.append(f"models differ between arms: {models}")
    adapters = sorted({r.get("adapter") for arm in ARMS for r in included[arm]})
    if "manual" in adapters:
        warnings.append("some runs were imported with the manual adapter: their usage and timing are self-reported")

    disclosures = [spec.get("disclosures", {}).get("conflict_of_interest") or rules["conflict_of_interest"]]
    if any(m["kind"] == "llm-judge" for m in metrics_out):
        disclosures.append(rules["judge_evidence_note"])
    if min(n_b, n_t) < rules["preferred_trials_per_arm"]:
        disclosures.append(rules["small_n_note"])
    disclosures += spec.get("disclosures", {}).get("other", [])
    if spec.get("task_type") == "knowledge-access":
        disclosures.append("This is a knowledge-access task: the information needed is in the catalogue and not in "
                           "the prompt, so it measures retrieval, not general capability.")
    if spec.get("purpose") != "study":
        disclosures.insert(0, f"Purpose '{spec.get('purpose')}': not a study result. Do not cite these numbers.")

    return {
        "spec": "baltor.showcase-comparison/v1",
        "task_id": spec["id"],
        "title": spec["title"],
        "domain": spec["domain"],
        "purpose": spec["purpose"],
        "task_type": spec.get("task_type", "capability"),
        "negative_control": bool(spec.get("negative_control")),
        "spec_sha256": spec["spec_sha256"],
        "generated_at": now or dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "generator": {"module": "showcase_stats", "version": VERSION},
        "design": {"analysis": "paired" if paired else "unpaired", "trials_planned": spec["trials"],
                   "alpha": rules["alpha"], "ci_level": ci, "bootstrap_resamples": resamples, "seed": seed,
                   "ci_method": "percentile bootstrap", "test": "two-sided permutation test of the mean difference",
                   "min_achievable_p": _r(min_p)},
        "runs": {arm: {"included": [r["run_id"] for r in included[arm]]} for arm in ARMS},
        "runs_excluded": excluded,
        "metrics": metrics_out,
        "success": success,
        "cost": cost_out,
        "catalogue_use": catalogue_use,
        "multiple_comparisons": {
            "method": "holm", "family": sorted(raw_p),
            "note": ("The pre-registered primary metric is tested at alpha on its own (its p_holm equals its p); "
                     f"Holm adjustment covers the {len(raw_p)} secondary quality metric(s). Tasks in one report "
                     "are not jointly corrected: with m tasks and no true effect, about m x alpha directional "
                     "verdicts are expected by chance."),
        },
        "verdict_rules": VERDICT_RULES,
        "overall": {"primary_metric": primary["name"] if primary else None, "verdict": overall_verdict,
                    "negative_control_status": nc_status, "warnings": warnings},
        "harness_versions": versions,
        "models": models,
        "adapters": adapters,
        "disclosures": disclosures,
    }


def compare(root: Path, task_id: str, out: Path | None = None, now: str | None = None) -> dict:
    spec, runs = load_task(root, task_id)
    if not runs:
        raise SystemExit(f"no run records under {root / 'runs' / task_id}")
    result = compare_task(spec, runs, now=now)
    _validate(result)
    out = out or root / "reports" / f"{task_id}.comparison.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


def _validate(result: dict) -> None:
    schema_path = HERE / "schemas" / "showcase_comparison.schema.json"
    if not schema_path.exists():
        return
    try:
        import jsonschema  # type: ignore
    except ImportError:  # pragma: no cover
        return
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(jsonschema.Draft202012Validator(schema).iter_errors(result), key=lambda e: list(e.path))
    if errors:
        e = errors[0]
        raise SystemExit(f"comparison does not match its schema at {'/'.join(map(str, e.path))}: {e.message}")


# --------------------------------------------------------------------------- CLI

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare", help="compare both arms of one registered task")
    c.add_argument("--root", type=Path, default=Path("showcases"))
    c.add_argument("--task", required=True)
    c.add_argument("--out", type=Path)
    c.add_argument("--now", help="fixed timestamp for reproducible output")
    q = sub.add_parser("quick", help="compare two samples given on the command line")
    q.add_argument("--baseline", type=float, nargs="+", required=True)
    q.add_argument("--baltor", type=float, nargs="+", required=True)
    q.add_argument("--lower-is-better", action="store_true")
    q.add_argument("--paired", action="store_true")
    q.add_argument("--seed", type=int, default=20261010)
    a = ap.parse_args(argv)
    if a.cmd == "compare":
        res = compare(a.root, a.task, a.out, a.now)
        o = res["overall"]
        print(f"{a.task}: primary {o['primary_metric']} -> {o['verdict']}"
              + (f"; negative control {o['negative_control_status']}" if o["negative_control_status"] else ""))
        for w in o["warnings"]:
            print("WARN", w)
        return 0
    direction = "lower" if a.lower_is_better else "higher"
    rules = load_rules()
    cmp = compare_samples(a.baseline, a.baltor, direction=direction, paired=a.paired, seed=a.seed, rules=rules)
    cmp["verdict"] = verdict(cmp, direction=direction, p_adjusted=cmp["p_value"], rules=rules, paired=a.paired)
    print(json.dumps(cmp, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
