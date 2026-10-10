"""Tests for the challenger's mechanical pre-pass (data/video_re_swarm/challenge_prepass.py).

Run: python3 -m pytest -q <directory holding this file>
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # generator data layout: tests/ next to challenge_prepass.py
sys.path.insert(0, str(HERE))  # package layout: the script sits next to this test

import challenge_prepass as cp  # noqa: E402

EVIDENCE = {
    "spec": "baltor.video-evidence/v1",
    "source": {"reference": "clip.mp4", "duration_s": 10.0, "width": 1080, "height": 1920, "fps": 30, "has_audio": True},
    "captions": [
        {"start_s": 0.5, "end_s": 2.0, "text": "seven ordinary words make a source sentence here today"},
        {"start_s": 2.0, "end_s": 3.0, "text": "Word {n}, word word word word word word"},
    ],
}
BANK = [
    {"id": "pacing_cut_rhythm-001", "ir_path": "/timeline/median_shot_s", "answer_type": "seconds"},
    {"id": "pacing_cut_rhythm-016", "ir_path": "/generation_rules/-", "answer_type": "enum",
     "choices": ["on-action", "on-stillness", "mixed"]},
    {"id": "color_grade-001", "ir_path": "/visual/palette", "answer_type": "palette"},
]


def answer(qid, value, ir_path, **ev):
    lens = qid.rsplit("-", 1)[0]
    evidence = {"method": "measured", "confidence": 0.9, "timestamps_s": [1.0], "tool": "video_re_shot_stats",
                "note": "median of 12 shots"}
    evidence.update(ev)
    return {"lens": lens, "question_id": qid, "answer": value, "ir_path": ir_path, "evidence": evidence}


def bank():
    return {q["id"]: {"ir_path": q["ir_path"], "answer_type": q["answer_type"], "choices": q.get("choices")}
            for q in BANK}


def run(a):
    return cp.check(a, EVIDENCE["source"]["duration_s"], bank(), cp.caption_ngrams(EVIDENCE))


def test_clean_measured_answer_passes():
    row = run(answer("pacing_cut_rhythm-001", {"value": 2.1, "unit": "s"}, "/timeline/median_shot_s"))
    assert row["verdict"] == "pass", row


def test_timestamp_outside_video_is_rejected():
    row = run(answer("pacing_cut_rhythm-001", {"value": 2.1, "unit": "s"}, "/timeline/median_shot_s",
                     timestamps_s=[12.0]))
    assert row["verdict"] == "reject"
    assert any("timestamps outside" in i for i in row["issues"])


def test_copied_caption_words_are_rejected_but_masked_captions_are_ignored():
    copied = answer("pacing_cut_rhythm-001", {"value": 2.1, "unit": "s"}, "/timeline/median_shot_s",
                    note="cut after seven ordinary words make a source sentence here")
    assert run(copied)["verdict"] == "reject"
    masked = answer("pacing_cut_rhythm-001", {"value": 2.1, "unit": "s"}, "/timeline/median_shot_s",
                    note="word word word word word word word")
    assert run(masked)["verdict"] == "pass"


def test_long_quote_is_rejected():
    row = run(answer("pacing_cut_rhythm-001", {"value": 2.1, "unit": "s"}, "/timeline/median_shot_s",
                     note='title reads "one two three four five six seven" at the top'))
    assert row["verdict"] == "reject"


def test_confidence_above_method_band_and_missing_tool_are_flagged():
    row = run(answer("pacing_cut_rhythm-001", {"value": 2.1, "unit": "s"}, "/timeline/median_shot_s",
                     method="inferred", confidence=0.9, tool=""))
    assert row["verdict"] == "flag"
    assert any("band cap 0.65" in i for i in row["issues"])


def test_shape_checks_against_bank():
    bad_enum = run(answer("pacing_cut_rhythm-016", "on-motion", "/generation_rules/-", method="observed", confidence=0.6))
    assert any("not in choices" in i for i in bad_enum["issues"])
    bad_palette = run(answer("color_grade-001", ["blue"], "/visual/palette"))
    assert any("palette" in i for i in bad_palette["issues"])
    wrong_path = run(answer("pacing_cut_rhythm-001", {"value": 2.1}, "/timeline/cut_rate_per_min"))
    assert any("differs from the bank" in i for i in wrong_path["issues"])


def test_not_determinable_needs_low_confidence():
    ok = run(answer("pacing_cut_rhythm-001", "not determinable", "/timeline/median_shot_s",
                    method="assumed", confidence=0, timestamps_s=[], tool=""))
    assert ok["verdict"] == "pass", ok
    high = run(answer("pacing_cut_rhythm-001", "not determinable", "/timeline/median_shot_s",
                      method="assumed", confidence=0.6, timestamps_s=[]))
    assert any("not determinable" in i for i in high["issues"])


def test_taste_and_identity_words_are_flagged():
    row = run(answer("pacing_cut_rhythm-001", {"value": 2.1, "unit": "s"}, "/timeline/median_shot_s",
                     note="a stunning cut rhythm from a female narrator"))
    joined = " ".join(row["issues"])
    assert "taste word" in joined and "identity" in joined


def test_bank_loads_from_rules_markdown_and_questions_json(tmp_path):
    md = tmp_path / "video-re-questions-x.md"
    md.write_text("# bank\n\n<!-- machine-readable bank -->\n```json\n" + json.dumps(BANK[:1]) + "\n```\n")
    qj = tmp_path / "questions.json"
    qj.write_text(json.dumps({"spec": "baltor.video-re-questions/v1", "questions": BANK[1:]}))
    (tmp_path / "other.json").write_text(json.dumps({"questions": [{"id": "x-001"}]}))
    loaded = cp.load_bank([str(tmp_path)])
    assert set(loaded) == {q["id"] for q in BANK}


def test_cli_writes_report(tmp_path):
    ev = tmp_path / "evidence.json"
    ev.write_text(json.dumps(EVIDENCE))
    ans = tmp_path / "answers.json"
    ans.write_text(json.dumps({"surviving": [answer("pacing_cut_rhythm-001", {"value": 2.1, "unit": "s"},
                                                    "/timeline/median_shot_s")] * 2}))
    out = tmp_path / "report.json"
    assert cp.main([str(ans), "--evidence", str(ev), "--out", str(out)]) == 0
    report = json.loads(out.read_text())
    assert report["answers"] == 2
    assert all("answered more than once" in " ".join(r["issues"]) for r in report["rows"])
