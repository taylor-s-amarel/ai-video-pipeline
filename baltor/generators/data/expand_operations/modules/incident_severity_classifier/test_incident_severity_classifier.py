import json

import incident_severity_classifier as m


def test_security_exposure_is_sev1():
    r = m.classify({"security_exposure": True})
    assert r["severity"] == "SEV1" and "confirmed security exposure" in r["reasons"]


def test_core_down_threshold():
    assert m.classify({"core_function_down": True, "users_affected_pct": 30})["severity"] == "SEV1"
    assert m.classify({"core_function_down": True, "users_affected_pct": 10})["severity"] == "SEV2"


def test_revenue_path_workaround_matters():
    assert m.classify({"revenue_path_impacted": True, "workaround": False})["severity"] == "SEV1"
    assert m.classify({"revenue_path_impacted": True, "workaround": True})["severity"] == "SEV2"
    # unknown workaround is not treated as "no workaround"
    assert m.classify({"revenue_path_impacted": True})["severity"] == "SEV2"


def test_low_impact_and_default():
    assert m.classify({"users_affected_pct": 1})["severity"] == "SEV3"
    r = m.classify({"internal_only": True})
    assert r["severity"] == "SEV4" and r["reasons"] == ["internal-only impact"]
    assert m.classify({})["severity"] == "SEV4"


def test_unknown_facts_reported():
    r = m.classify({"users_affected_pct": 50})
    assert "security_exposure" in r["unknown_facts"] and "users_affected_pct" not in r["unknown_facts"]


def test_custom_matrix_and_cli(tmp_path, capsys):
    matrix = {"facts": {"x": ""}, "levels": [{"name": "P1", "rules": [{"reason": "x", "when": {"fact": "x", "op": ">", "value": 3}}]},
                                           {"name": "P2", "default": True, "rules": []}]}
    assert m.classify({"x": 5}, matrix)["severity"] == "P1"
    assert m.classify({"x": 1}, matrix)["severity"] == "P2"
    f = tmp_path / "f.json"
    f.write_text(json.dumps({"data_loss": True}))
    assert m.main(["--facts", str(f)]) == 0
    assert json.loads(capsys.readouterr().out)["response"]["update_interval_min"] == 30
