import json
import math
from pathlib import Path

import pytest

import showcase_stats as st

HERE = Path(__file__).resolve().parent


def test_bootstrap_is_deterministic_and_brackets_estimate():
    a, b = [0.60, 0.62, 0.58, 0.61, 0.59], [0.70, 0.72, 0.69, 0.75, 0.71]
    r1 = st.bootstrap_diff(a, b, resamples=4000, seed=7)
    r2 = st.bootstrap_diff(a, b, resamples=4000, seed=7)
    assert r1 == r2
    est, lo, hi = r1
    assert lo <= est <= hi
    assert math.isclose(est, sum(b) / 5 - sum(a) / 5)
    assert lo > 0


def test_paired_bootstrap_uses_differences():
    a, b = [1.0, 2.0, 3.0], [1.5, 2.5, 3.5]
    est, lo, hi = st.bootstrap_diff(a, b, paired=True, resamples=500, seed=1)
    assert est == pytest.approx(0.5) and lo == pytest.approx(0.5) and hi == pytest.approx(0.5)


def test_exact_permutation_p_values_match_combinatorics():
    sep3 = st.permutation_test([1, 2, 3], [4, 5, 6])
    assert sep3["method"] == "exact" and sep3["permutations"] == 20
    assert sep3["p"] == pytest.approx(0.1)
    sep5 = st.permutation_test([1, 2, 3, 4, 5], [6, 7, 8, 9, 10])
    assert sep5["p"] == pytest.approx(2 / 252)
    same = st.permutation_test([1, 1, 1], [1, 1, 1])
    assert same["p"] == 1.0


def test_min_achievable_p():
    assert st.min_achievable_p(3, 3) == pytest.approx(0.1)
    assert st.min_achievable_p(5, 5) == pytest.approx(2 / 252)
    assert st.min_achievable_p(5, 5, paired=True) == pytest.approx(2 / 32)


def test_holm_is_monotone_and_capped():
    adj = st.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert adj["a"] == pytest.approx(0.03)
    assert adj["c"] == pytest.approx(0.06)
    assert adj["b"] == pytest.approx(0.06)
    assert st.holm({"x": 0.9, "y": 0.8})["x"] == 1.0


def test_cliffs_delta_and_win_rate_orientation():
    a, b = [1, 2, 3], [2, 3, 4]
    d = st.cliffs_delta(a, b)
    assert d == pytest.approx((6 - 1) / 9)
    assert st.delta_magnitude(d) == "large"
    w = st.win_rate(a, b)
    assert w["baltor_wins"] == 6 and w["baseline_wins"] == 1 and w["ties"] == 2
    assert w["rate"] == pytest.approx((6 + 1) / 9)
    w_low = st.win_rate(a, b, higher_is_better=False)
    assert w_low["baltor_wins"] == 1


def test_verdicts():
    rules = st.load_rules()
    a, b = [0.50, 0.52, 0.49, 0.51, 0.50], [0.70, 0.72, 0.69, 0.71, 0.73]
    cmp = st.compare_samples(a, b, seed=3, rules=rules)
    assert st.verdict(cmp, direction="higher", p_adjusted=cmp["p_value"], rules=rules, paired=False) == "baltor-better"
    cmp_low = st.compare_samples(a, b, direction="lower", seed=3, rules=rules)
    assert st.verdict(cmp_low, direction="lower", p_adjusted=cmp_low["p_value"], rules=rules,
                      paired=False) == "baseline-better"
    three = st.compare_samples(a[:3], b[:3], seed=3, rules=rules)
    assert st.verdict(three, direction="higher", p_adjusted=three["p_value"], rules=rules,
                      paired=False) == "insufficient-data"
    flat = st.compare_samples([0.5, 0.6, 0.5, 0.6, 0.55], [0.6, 0.5, 0.55, 0.5, 0.6], seed=3, rules=rules)
    assert st.verdict(flat, direction="higher", p_adjusted=flat["p_value"], rules=rules,
                      paired=False) == "no-clear-difference"
    assert st.verdict(cmp, direction="higher", p_adjusted=cmp["p_value"], rules=rules, paired=False,
                      minimum_effect=0.5) == "no-clear-difference"


def _run(arm, trial, f1, success, wall, tokens, included=True, status="completed"):
    return {
        "run_id": f"t/{arm}/{trial}", "arm": arm, "trial": trial, "spec_sha256": "x" * 64,
        "adapter": "claude-code", "harness": {"name": "claude-code", "version": "2.1.0"},
        "model": {"requested": "m", "reported": "m"},
        "wall_s": wall, "usage": {"tool_calls": 10, "tokens_total": tokens, "cost_usd": None},
        "included": included, "exclusion_reason": None if included else "contaminated",
        "exit": {"status": status},
        "catalogue": {"mode": "search-read" if arm == "baltor" else "none",
                      "calls": [{"op": "search"}] if arm == "baltor" else [],
                      "downloaded": [{"identity": "dedupe_helper", "version": "1.0.0", "digest": "d" * 64}]
                      if arm == "baltor" else [], "preplaced": []},
        "evaluation": {"status": "done", "success": success,
                       "results": [{"metric": "pair_f1", "value": f1, "scored_as": "evaluated"},
                                   {"metric": "tests_passed", "value": 1.0 if success else 0.5,
                                    "scored_as": "evaluated"}]},
    }


SPEC = {
    "id": "t", "title": "Tiny task", "domain": "data-cleaning", "purpose": "dry-run", "trials": 5,
    "negative_control": False, "spec_sha256": "x" * 64, "task_type": "capability",
    "analysis": {"design": "unpaired", "bootstrap_resamples": 2000, "ci_level": 0.95, "seed": 11, "alpha": 0.05},
    "metrics": [{"name": "pair_f1", "direction": "higher", "kind": "deterministic", "weight": 2, "primary": True},
                {"name": "tests_passed", "direction": "higher", "kind": "deterministic", "weight": 1}],
    "success_threshold": {"metric": "pair_f1", "op": ">=", "value": 0.8},
    "expected_components": ["dedupe_helper"],
    "disclosures": {"conflict_of_interest": "Same team wrote the components and the tasks."},
}


def _runs():
    runs = [_run("baseline", i + 1, f, f >= 0.8, 100 + i, 5000) for i, f in enumerate([0.55, 0.6, 0.0, 0.62, 0.58])]
    runs += [_run("baltor", i + 1, f, f >= 0.8, 120 + i, 7000) for i, f in enumerate([0.9, 0.86, 0.92, 0.88, 0.91])]
    runs.append(_run("baseline", 6, 0.99, True, 50, 100, included=False))
    return runs


def test_compare_task_end_to_end():
    out = st.compare_task(SPEC, _runs(), now="2026-10-10T00:00:00Z")
    assert out["overall"]["primary_metric"] == "pair_f1"
    assert out["overall"]["verdict"] == "baltor-better"
    assert out["runs_excluded"] == [{"run_id": "t/baseline/6", "reason": "contaminated"}]
    f1 = out["metrics"][0]
    assert f1["baseline"]["n"] == 5 and 0.0 in f1["baseline"]["samples"]
    assert f1["p_holm"] == f1["p_value"]  # primary metric: not adjusted
    tests = out["metrics"][1]
    assert out["multiple_comparisons"]["family"] == ["tests_passed"] and tests["p_holm"] == tests["p_value"]
    assert out["success"]["baltor"]["successes"] == 5 and out["success"]["baseline"]["successes"] == 0
    wall = next(c for c in out["cost"] if c["name"] == "wall_s")
    assert wall["difference"]["estimate"] == pytest.approx(20.0)
    cost = next(c for c in out["cost"] if c["name"] == "cost_usd")
    assert cost["missing_values"] == 10 and cost["baseline"]["n"] == 0
    assert out["catalogue_use"]["expected_components_found"] == ["dedupe_helper"]
    assert any("not a study result" in d for d in out["disclosures"])
    st._validate(out)


def test_negative_control_status():
    spec = dict(SPEC, negative_control=True)
    runs = [_run("baseline", i + 1, f, True, 100, 10) for i, f in enumerate([0.9, 0.91, 0.89, 0.9, 0.92])]
    runs += [_run("baltor", i + 1, f, True, 100, 10) for i, f in enumerate([0.91, 0.9, 0.9, 0.89, 0.92])]
    out = st.compare_task(spec, runs, now="2026-10-10T00:00:00Z")
    assert out["overall"]["negative_control_status"] == "passed"


def test_unevaluated_run_is_refused():
    runs = _runs()
    runs[0]["evaluation"] = {"status": "pending", "results": []}
    with pytest.raises(SystemExit):
        st.compare_task(SPEC, runs)


def test_cli_quick(capsys):
    assert st.main(["quick", "--baseline", "1", "2", "3", "--baltor", "4", "5", "6"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["verdict"] == "insufficient-data"
    assert data["p_value"] == pytest.approx(0.1)


def test_compare_reads_registered_task(tmp_path):
    spec = dict(SPEC)
    spec["spec_sha256"] = st.canonical_hash(spec)
    (tmp_path / "tasks" / "t").mkdir(parents=True)
    (tmp_path / "tasks" / "t" / "spec.json").write_text(json.dumps(spec))
    for r in _runs():
        r["spec_sha256"] = spec["spec_sha256"]
        d = tmp_path / "runs" / "t" / r["arm"] / str(r["trial"])
        d.mkdir(parents=True)
        (d / "run.json").write_text(json.dumps(r))
    res = st.compare(tmp_path, "t", now="2026-10-10T00:00:00Z")
    assert (tmp_path / "reports" / "t.comparison.json").exists()
    assert res["overall"]["verdict"] == "baltor-better"
    spec["title"] = "edited after registration"
    (tmp_path / "tasks" / "t" / "spec.json").write_text(json.dumps(spec))
    with pytest.raises(SystemExit):
        st.compare(tmp_path, "t")
