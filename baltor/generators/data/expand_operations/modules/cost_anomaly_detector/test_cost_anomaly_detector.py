import datetime as dt
import random

import cost_anomaly_detector as m


def rows(service, base, days=30, spikes=None, start=dt.date(2026, 9, 1), noise=0.03, seed=1):
    rnd = random.Random(seed)
    out = []
    for i in range(days):
        d = start + dt.timedelta(i)
        cost = base * (1 + rnd.uniform(-noise, noise))
        if spikes and i in spikes:
            cost *= spikes[i]
        out.append({"date": d.isoformat(), "service": service, "cost": f"{cost:.2f}"})
    return out


def test_detects_spike_and_ignores_noise():
    data = rows("EC2", 400, spikes={25: 2.0}) + rows("S3", 50, seed=2)
    found = m.detect(m.load(data, "date", "service", "cost"))
    assert [(a.group, a.date) for a in found] == [("EC2", "2026-09-26")]
    assert found[0].ratio > 1.8


def test_small_service_needs_min_delta():
    data = rows("Lambda", 2, spikes={20: 5.0})
    assert m.detect(m.load(data, "date", "service", "cost")) == []
    assert len(m.detect(m.load(data, "date", "service", "cost"), min_delta=1)) == 1


def test_missing_days_are_zero_and_flat_history():
    data = [{"date": f"2026-09-{d:02d}", "service": "X", "cost": "100"} for d in range(1, 15)]
    data.append({"date": "2026-09-20", "service": "X", "cost": "300"})
    found = m.detect(m.load(data, "date", "service", "cost"))
    assert found and found[0].date == "2026-09-20" and found[0].robust_z == float("inf")


def test_weekday_seasonality():
    data = []
    for i in range(56):
        d = dt.date(2026, 8, 3) + dt.timedelta(i)  # starts on a Monday
        data.append({"date": d.isoformat(), "service": "Batch", "cost": "500" if d.weekday() == 0 else "100"})
    assert m.detect(m.load(data, "date", "service", "cost"), weekday=True) == []
    assert m.detect(m.load(data, "date", "service", "cost"), weekday=False) != []


def test_focus_column_names_and_cli(tmp_path):
    p = tmp_path / "focus.csv"
    lines = ["ChargePeriodStart,ServiceName,EffectiveCost"]
    for r in rows("Compute", 300, spikes={28: 3}):
        lines.append(f"{r['date']}T00:00:00Z,{r['service']},{r['cost']}")
    p.write_text("\n".join(lines) + "\n")
    assert m.main([str(p), "--date-col", "ChargePeriodStart", "--group-col", "ServiceName", "--cost-col", "EffectiveCost"]) == 1
