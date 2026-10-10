import datetime as dt

import pytest

import slo_burn_rate_alerts as m


def test_allowed_downtime_known_values():
    assert m.allowed_downtime(0.999, 30) == dt.timedelta(minutes=43, seconds=12)
    assert m.allowed_downtime(0.99, 30) == dt.timedelta(hours=7, minutes=12)
    assert m.allowed_downtime(0.9999, 30) == dt.timedelta(minutes=4, seconds=19)


def test_burn_rate_and_budget_fraction_match_workbook():
    assert m.burn_rate(0.0144, 0.999) == pytest.approx(14.4)
    fr = [round(w.budget_fraction(30), 3) for w in m.DEFAULT_POLICY]
    assert fr == [0.02, 0.05, 0.1]
    assert m.threshold_for_budget(0.02, "1h") == pytest.approx(14.4)


def test_budget_status():
    s = m.budget_status(good=99_950, total=100_000, target=0.999)
    assert s["allowed_bad"] == pytest.approx(100)
    assert s["consumed"] == pytest.approx(0.5) and s["remaining"] == pytest.approx(0.5)
    assert m.budget_status(0, 0, 0.99)["remaining"] == 1.0


def test_evaluate_requires_both_windows():
    ratios = {"5m": 0.02, "1h": 0.02, "30m": 0.0, "6h": 0.0, "6h_": 0, "3d": 0.0}
    firing = m.evaluate(ratios, 0.999)
    assert [w.long for w in firing] == ["1h"]
    ratios["5m"] = 0.0001  # problem already over: short window recovered
    assert m.evaluate(ratios, 0.999) == []
    with pytest.raises(KeyError):
        m.evaluate({"1h": 0.1}, 0.999)


def test_durations():
    assert m.parse_duration("1h30m") == dt.timedelta(minutes=90)
    assert m.format_duration(dt.timedelta(days=3)) == "3d"
    with pytest.raises(ValueError):
        m.parse_duration("5 minutes")


def test_rules_yaml_structure():
    yaml = pytest.importorskip("yaml")
    text = m.prometheus_rules("checkout-availability", 0.999,
                              'sum(rate(http_requests_total{code=~"5.."}[{w}]))',
                              "sum(rate(http_requests_total[{w}]))", runbook_url="https://runbooks.example/slo")
    doc = yaml.safe_load(text)
    rec, alerts = doc["groups"][0]["rules"], doc["groups"][1]["rules"]
    assert {r["record"] for r in rec} == {f"slo:checkout_availability:error_ratio_rate{w}" for w in ["5m", "30m", "1h", "6h", "3d"]}
    assert len(alerts) == 3 and alerts[0]["labels"]["severity"] == "page"
    assert "14.4 * 0.001" in alerts[0]["expr"]
    assert "[1h]" in next(r["expr"] for r in rec if r["record"].endswith("rate1h"))
    assert all("runbook_url" in a["annotations"] for a in alerts)


def test_rules_reject_missing_placeholder_and_bad_target():
    with pytest.raises(ValueError):
        m.prometheus_rules("x", 0.999, "rate(a[5m])", "rate(b[{w}])")
    with pytest.raises(ValueError):
        m.allowed_downtime(1.0)


def test_cli(capsys):
    assert m.main(["table", "--target", "0.995"]) == 0
    assert "allowed downtime" in capsys.readouterr().out
