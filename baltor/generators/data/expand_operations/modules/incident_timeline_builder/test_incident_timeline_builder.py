import datetime as dt
import json

import pytest

import incident_timeline_builder as m

NOTES = """# checkout incident
2026-10-10 14:02 UTC [detected] HighErrorRate fired
14:05 [ack] on-call acked
13:52 [started] v1.4.2 rolled out
14:20 [mitigated] rolled back
2026-10-10T15:00:00Z [resolved] baseline for 30 min
14:30 status page updated
"""


def test_sorted_with_aliases():
    ev = m.parse(NOTES)
    assert [e.tag for e in ev] == ["started", "detected", "acknowledged", "mitigated", "note", "resolved"]
    assert ev[0].at == dt.datetime(2026, 10, 10, 13, 52, tzinfo=dt.timezone.utc)


def test_metrics():
    mt = m.metrics(m.parse(NOTES))
    assert mt == {"time_to_detect_min": 10.0, "time_to_acknowledge_min": 3.0, "time_to_mitigate_min": 28.0,
                  "time_to_resolve_min": 68.0, "customer_impact_min": 28.0}


def test_timezone_offsets_converted():
    ev = m.parse("2026-10-10T10:00:00-04:00 [detected] x\n")
    assert ev[0].at.hour == 14


def test_midnight_rollover():
    ev = m.parse("2026-10-10 23:50 [detected] a\n00:10 [mitigated] b\n")
    assert ev[1].at.date() == dt.date(2026, 10, 11)
    assert m.metrics(ev)["time_to_mitigate_min"] == 20.0


def test_errors_and_gaps():
    with pytest.raises(ValueError):
        m.parse("14:00 [detected] x\n")
    ev = m.parse("14:00 [detected] x\n", dt.date(2026, 10, 10))
    assert "no [mitigated] event" in m.problems(ev)
    with pytest.raises(ValueError):
        m.parse("detected at two\n", dt.date(2026, 10, 10))


def test_markdown_and_cli(tmp_path, capsys):
    md = m.to_markdown(m.parse(NOTES))
    assert "| 2026-10-10 13:52:00 | started |" in md and "time to detect | 10.0" in md
    p = tmp_path / "n.txt"
    p.write_text(NOTES)
    assert m.main([str(p), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["events"][0]["at"] == "2026-10-10T13:52:00Z" and out["problems"] == []
