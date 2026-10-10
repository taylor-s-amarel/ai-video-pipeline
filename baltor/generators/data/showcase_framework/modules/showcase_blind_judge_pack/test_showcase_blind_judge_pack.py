import json
from pathlib import Path

import pytest

import showcase_blind_judge_pack as bj

SPEC = {
    "id": "poster", "prompt": "Write a one-paragraph product blurb in blurb.md.",
    "analysis": {"seed": 5},
    "outputs": [{"path": "blurb.md", "required": True}],
    "metrics": [{"name": "judged_quality", "direction": "higher", "kind": "llm-judge", "weight": 1, "on_missing": 0,
                 "evaluator": {"type": "blind_judge", "params": {
                     "rubric": "Clear, specific, accurate.", "criteria": ["clarity", "specificity"],
                     "scale": [1, 5]}}}],
}


def make_root(tmp_path, n=2):
    root = tmp_path / "showcases"
    spec = dict(SPEC)
    spec["spec_sha256"] = bj.canonical_hash(spec)
    (root / "tasks" / "poster").mkdir(parents=True)
    (root / "tasks" / "poster" / "spec.json").write_text(json.dumps(spec))
    for arm in ("baseline", "baltor"):
        for t in range(1, n + 1):
            d = root / "runs" / "poster" / arm / str(t)
            (d / "workspace" / ".claude" / "skills").mkdir(parents=True)
            text = f"{arm} blurb {t}." + (" Made with the Baltor blurb_style_guide." if arm == "baltor" else "")
            (d / "workspace" / "blurb.md").write_text(text)
            (d / "workspace" / ".claude" / "skills" / "x.md").write_text("secret skill")
            cat = {"downloaded": [{"identity": "blurb_style_guide", "version": "1.0.0", "digest": "a" * 64}]} \
                if arm == "baltor" else {"downloaded": []}
            (d / "run.json").write_text(json.dumps({"run_id": f"poster/{arm}/{t}", "arm": arm, "trial": t,
                                                    "included": True, "workspace": "workspace",
                                                    "catalogue": dict(cat, preplaced=[])}))
    return root


def test_build_is_blind_and_deterministic(tmp_path):
    root = make_root(tmp_path)
    res = bj.build_packets(root, "poster", now="2026-10-10T00:00:00Z")
    assert res["packets"] == 4
    key = json.loads((root / "runs" / "poster" / "_judging" / "key.json").read_text())
    packets_dir = Path(res["packets_dir"])
    assert not (packets_dir / "key.json").exists()
    sides = []
    for pid, k in key["packets"].items():
        pdir = packets_dir / pid
        packet = json.loads((pdir / "packet.json").read_text())
        assert "baltor" not in json.dumps(packet).lower()
        for side in ("A", "B"):
            text = (pdir / side / "blurb.md").read_text()
            assert "baltor" not in text.lower() and "blurb_style_guide" not in text
            assert not (pdir / side / ".claude").exists()
        sides.append(k["A"].split("/")[1])
    assert set(sides) == {"baseline", "baltor"} or len(sides) == 4
    first = json.dumps(key["packets"], sort_keys=True)
    bj.build_packets(root, "poster", now="2026-10-10T00:00:00Z")
    again = json.loads((root / "runs" / "poster" / "_judging" / "key.json").read_text())
    assert json.dumps(again["packets"], sort_keys=True) == first
    assert "clarity" in (packets_dir / "README.md").read_text()


def _judgement(pid, pref, a, b, judge="j1"):
    return {"spec": "baltor.showcase-judgement/v1", "packet_id": pid, "task_id": "poster",
            "judge": {"id": judge, "type": "llm", "model": "m"}, "preference": pref,
            "scores": {"clarity": {"A": a, "B": b}, "specificity": {"A": a, "B": b}},
            "justification": "A states the price and the battery life; B is generic and repeats itself twice.",
            "confidence": "medium"}


def test_merge_unblinds_and_validates(tmp_path):
    root = make_root(tmp_path)
    bj.build_packets(root, "poster", both_orders=True)
    key = json.loads((root / "runs" / "poster" / "_judging" / "key.json").read_text())
    assert len(key["packets"]) == 8
    jdir = root / "judging" / "poster" / "judgements"
    jdir.mkdir(parents=True)
    out = []
    for pid, k in key["packets"].items():
        baltor_side = "A" if "/baltor/" in k["A"] else "B"
        a, b = (5, 3) if baltor_side == "A" else (3, 5)
        out.append(_judgement(pid, baltor_side, a, b))
    bad = _judgement(next(iter(key["packets"])), "A", 9, 1, judge="j2")
    short = dict(_judgement(next(iter(key["packets"])), "A", 4, 2, judge="j3"), justification="too short")
    (jdir / "j1.json").write_text(json.dumps(out))
    (jdir / "bad.json").write_text(json.dumps([bad, short]))
    merged = bj.merge(root, "poster", now="2026-10-10T00:00:00Z")
    assert merged["judgements"] == 8 and len(merged["rejected"]) == 2
    assert merged["pairwise"] == {"baltor_preferred": 8, "baseline_preferred": 0, "ties": 0}
    assert merged["runs"]["poster/baltor/1"]["score"] == pytest.approx(1.0)
    assert merged["runs"]["poster/baseline/1"]["score"] == pytest.approx(0.5)
    assert merged["runs"]["poster/baltor/2"]["win_share"] == 1.0
    assert merged["position"]["A"] + merged["position"]["B"] == 8
    assert (root / "runs" / "poster" / "_judging" / "merged.json").exists()


def test_needs_a_blind_judge_metric(tmp_path):
    root = make_root(tmp_path, n=1)
    spec = json.loads((root / "tasks" / "poster" / "spec.json").read_text())
    spec["metrics"][0]["evaluator"]["type"] = "files_present"
    spec["spec_sha256"] = bj.canonical_hash(spec)
    (root / "tasks" / "poster" / "spec.json").write_text(json.dumps(spec))
    with pytest.raises(SystemExit):
        bj.build_packets(root, "poster")
