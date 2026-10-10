import pytest

import prometheus_rules_lint as m

GOOD = {"groups": [{"name": "api", "rules": [
    {"record": "job:http_requests:rate5m", "expr": "sum by (job) (rate(http_requests_total[5m]))"},
    {"alert": "HighErrorRate", "expr": "job:http_errors:ratio_rate5m > 0.05", "for": "5m",
     "labels": {"severity": "page"},
     "annotations": {"summary": "5xx above 5%", "description": "Users see errors", "runbook_url": "https://runbooks.example/api"}},
]}]}


def codes(doc):
    return {(f.rule, f.severity) for f in m.lint_rules(doc)}


def test_good_rules_clean():
    assert m.lint_rules(GOOD) == []


def test_missing_metadata():
    doc = {"groups": [{"name": "g", "rules": [{"alert": "high_cpu", "expr": "x > 1"}]}]}
    r = codes(doc)
    assert ("PR001", "low") in r and ("PR002", "medium") in r and ("PR003", "medium") in r and ("PR005", "info") in r


def test_page_needs_runbook():
    doc = {"groups": [{"name": "g", "rules": [{"alert": "Down", "expr": "up == 0", "for": "2m", "labels": {"severity": "page"},
                                               "annotations": {"summary": "s", "description": "d"}}]}]}
    assert any(f.rule == "PR003" and "runbook" in f.message for f in m.lint_rules(doc))


def test_rate_on_gauge_and_short_range():
    doc = {"groups": [{"name": "g", "rules": [{"record": "bad_name", "expr": "rate(memory_bytes[30s])"}]}]}
    r = {f.rule for f in m.lint_rules(doc)}
    assert {"PR004", "PR006", "PR008"} <= r


def test_structure_errors_and_duplicates():
    assert m.lint_rules({})[0].severity == "high"
    doc = {"groups": [{"rules": [{"alert": "A", "expr": ""}, {"alert": "A", "expr": "1"}, {"expr": "1"}]}]}
    r = codes(doc)
    assert ("PR007", "high") in r and ("PR007", "medium") in r


def test_metric_names():
    text = """# HELP x
# TYPE http_requests counter
# TYPE request_latency_milliseconds histogram
# TYPE queue_depth_total gauge
# TYPE job:foo:sum gauge
# TYPE http_get_200_total counter
# TYPE process_cpu_seconds_total counter
"""
    r = {(f.rule, f.location) for f in m.lint_metric_names(text)}
    assert ("PM002", "http_requests") in r and ("PM003", "request_latency_milliseconds") in r
    assert ("PM002", "queue_depth_total") in r and ("PM001", "job:foo:sum") in r and ("PM004", "http_get_200_total") in r
    assert not any(loc == "process_cpu_seconds_total" for _, loc in r)


def test_cli(tmp_path):
    yaml = pytest.importorskip("yaml")
    p = tmp_path / "r.yml"
    p.write_text(yaml.safe_dump(GOOD))
    assert m.main([str(p)]) == 0
    mp = tmp_path / "metrics.txt"
    mp.write_text("# TYPE x_ms gauge\n")
    assert m.main([str(mp), "--metrics", "--fail-on", "low"]) == 1
