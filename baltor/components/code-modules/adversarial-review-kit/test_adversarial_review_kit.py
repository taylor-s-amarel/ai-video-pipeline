import json
import math

import pytest

import adversarial_review_kit as k

SHA_FILM = "a" * 64
SHA_OTHER = "b" * 64
SHA_SHEET = "c" * 64

BANK = {
    "AVQ-006-002": {"id": "AVQ-006-002", "area": "contact and props", "domain_id": "D006", "severity": "high",
                    "modes": ["visual"], "stages": ["storyboard", "production", "final-encode"],
                    "style_filters": ["any"]},
    "AVQ-022-001": {"id": "AVQ-022-001", "area": "music composition", "domain_id": "D022", "severity": "medium",
                    "modes": ["auditory", "human-audience"], "stages": ["edit", "final-encode"],
                    "style_filters": ["any"]},
    "AVQ-029-001": {"id": "AVQ-029-001", "area": "decoding and delivery", "domain_id": "D029", "severity": "high",
                    "modes": ["machine"], "stages": ["final-encode", "delivery"], "style_filters": ["any"]},
    "AVQ-030-005": {"id": "AVQ-030-005", "area": "audience value", "domain_id": "D030", "severity": "medium",
                    "modes": ["human-audience"], "stages": ["delivery"], "style_filters": ["fiction"]},
}
PASSES = {"tiny": {"purpose": "test", "declared_count": 2, "question_ids": ["AVQ-029-001", "AVQ-006-002"]}}

# The record shown in the guide's "Evidence states" section, verbatim.
GUIDE_EXAMPLE = {
    "question_id": "AVQ-006-002",
    "target_artifact": "final.mp4",
    "target_sha256": "COMPUTED_FINAL_HASH",
    "status": "untested",
    "finding_type": "none",
    "review_mode": "visual",
    "scope": {"start_frame": None, "end_frame": None, "coverage": "not_observed"},
    "evidence": [],
    "rationale": "Awaiting matching encoded interval",
    "required_recheck_after": ["rig_change", "prop_attachment_change", "camera_change"],
}


def evidence(**over):
    ev = {"evidence_sha256": SHA_SHEET, "target_sha256": SHA_FILM, "method": "ffmpeg decode of frames 120-180",
          "locator": "frames 120-180", "coverage": "interval", "limitations": "hands only; no audio",
          "observation": "frame-inspection"}
    ev.update(over)
    return ev


def observed(**over):
    rec = dict(GUIDE_EXAMPLE, target_sha256=SHA_FILM, status="observed-pass",
               scope={"start_frame": 120, "end_frame": 180, "coverage": "interval"},
               evidence=[evidence()], rationale="Grip holds through the hand-off")
    rec.update(over)
    return rec


def test_guide_example_record_is_valid():
    assert k.validate_result(GUIDE_EXAMPLE, BANK["AVQ-006-002"]) == []


def test_observed_pass_with_matching_interval_evidence_is_valid():
    assert k.validate_result(observed(), BANK["AVQ-006-002"], SHA_FILM) == []


def test_demonstrated_defect_requires_observed_fail():
    probs = k.validate_result(dict(GUIDE_EXAMPLE, finding_type="demonstrated_defect"))
    assert any("demonstrated_defect" in p for p in probs)
    assert k.validate_result(observed(status="observed-fail", finding_type="demonstrated_defect")) == []


def test_observed_status_without_evidence_fails():
    probs = k.validate_result(observed(evidence=[]))
    assert any("at least one evidence item" in p for p in probs)


def test_placeholder_target_hash_cannot_back_an_observation():
    probs = k.validate_result(observed(target_sha256="COMPUTED_FINAL_HASH"))
    assert any("computed SHA-256" in p for p in probs)


def test_stale_target_hash_fails():
    probs = k.validate_result(observed(), current_target_sha256=SHA_OTHER)
    assert any("stale target hash" in p for p in probs)


def test_retargeted_contact_sheet_fails():
    probs = k.validate_result(observed(evidence=[evidence(target_sha256=SHA_OTHER)]))
    assert any("different target" in p for p in probs)


def test_nonfinite_numbers_fail():
    probs = k.validate_result(observed(scope={"start_frame": 0, "end_frame": 10, "coverage": "interval",
                                              "mean_offset_ms": math.nan}))
    assert any("nonfinite" in p for p in probs)
    parsed = json.loads('{"x": Infinity}')
    assert k._nonfinite(parsed)


def test_absent_interval_fails():
    probs = k.validate_result(observed(scope={"start_frame": None, "end_frame": None, "coverage": "interval"}))
    assert any("absent interval" in p for p in probs)


def test_reversed_interval_fails():
    probs = k.validate_result(observed(scope={"start_frame": 50, "end_frame": 10, "coverage": "interval"}))
    assert any("before start_frame" in p for p in probs)


def test_unsupported_full_coverage_fails():
    probs = k.validate_result(observed(scope={"start_frame": 0, "end_frame": 2999, "coverage": "full"},
                                       evidence=[evidence(coverage="sampled")]))
    assert any("not supported by the evidence" in p for p in probs)


def test_listening_question_not_passed_on_waveform_statistic():
    rec = observed(question_id="AVQ-022-001", review_mode="auditory",
                   evidence=[evidence(observation="waveform-statistic", method="ffmpeg astats")])
    probs = k.validate_result(rec, BANK["AVQ-022-001"])
    assert any("waveform statistic is not listening" in p for p in probs)
    ok = observed(question_id="AVQ-022-001", review_mode="auditory",
                  evidence=[evidence(observation="listening", method="full listen on headphones")])
    assert k.validate_result(ok, BANK["AVQ-022-001"]) == []


def test_blocked_and_not_applicable_need_reasons():
    for status in ("blocked", "not-applicable"):
        probs = k.validate_result(dict(GUIDE_EXAMPLE, status=status, rationale=" "))
        assert any("stated reason" in p for p in probs)


def test_unknown_values_fail():
    probs = k.validate_result(dict(GUIDE_EXAMPLE, status="passed", finding_type="bug", review_mode="vibes",
                                   question_id="Q1"))
    assert len(probs) == 4


def test_validate_results_flags_unknown_and_duplicate_records():
    probs = k.validate_results([GUIDE_EXAMPLE, GUIDE_EXAMPLE, dict(GUIDE_EXAMPLE, question_id="AVQ-099-001")], BANK)
    assert any("recorded twice" in p for p in probs)
    assert any("not a question in the loaded bank" in p for p in probs)


def test_select_by_pass_keeps_guide_order_and_rejects_unknown_pass():
    assert [q["id"] for q in k.select(BANK, "tiny", passes=PASSES)] == ["AVQ-029-001", "AVQ-006-002"]
    with pytest.raises(k.BankError):
        k.select(BANK, "nope", passes=PASSES)


def test_select_filters_are_candidate_filters():
    assert [q["id"] for q in k.select(BANK, stage="delivery")] == ["AVQ-029-001", "AVQ-030-005"]
    assert "AVQ-030-005" not in [q["id"] for q in k.select(BANK, style="educational")]
    assert [q["id"] for q in k.select(BANK, min_severity="high")] == ["AVQ-006-002", "AVQ-029-001"]
    assert [q["id"] for q in k.select(BANK, area="D022")] == ["AVQ-022-001"]


def test_plan_pass_is_honest_about_planning_and_missing_listening():
    recs = {r["question_id"]: r for r in k.plan_pass(list(BANK.values()), "board.pdf", SHA_FILM, "storyboard",
                                                     ["visual", "machine"])}
    assert recs["AVQ-029-001"]["status"] == "untested"
    assert "remains untested during planning" in recs["AVQ-029-001"]["rationale"]
    assert recs["AVQ-022-001"]["status"] == "blocked"
    assert recs["AVQ-006-002"]["status"] == "untested"
    assert all(k.validate_result(r) == [] for r in recs.values())


def test_needs_recheck_and_summary():
    recs = [GUIDE_EXAMPLE, observed(question_id="AVQ-029-001", required_recheck_after=["encode_change"]),
            observed(status="observed-fail", finding_type="demonstrated_defect", required_recheck_after=["rig_change"])]
    assert k.needs_recheck(recs, ["camera_change"]) == ["AVQ-006-002"]
    s = k.summarise(recs)
    assert s["by_status"]["untested"] == 1 and s["by_status"]["observed-pass"] == 1
    assert s["demonstrated_defects"] == ["AVQ-006-002"]
    assert s["not_checked"] == ["AVQ-006-002"]


def test_load_bank_merges_identical_and_rejects_conflicting_duplicates(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    (tmp_path / "a" / "questions.json").write_text(json.dumps([BANK["AVQ-006-002"]]))
    (tmp_path / "b" / "questions.json").write_text(json.dumps({"questions": [BANK["AVQ-006-002"]]}))
    assert list(k.load_bank([tmp_path])) == ["AVQ-006-002"]
    (tmp_path / "b" / "questions.json").write_text(json.dumps([dict(BANK["AVQ-006-002"], severity="low")]))
    with pytest.raises(k.BankError):
        k.load_bank([tmp_path])
    with pytest.raises(k.BankError):
        k.load_bank([tmp_path / "a" / "questions.json", tmp_path / "b" / "questions.json"])


BANK_MD = """# Adversarial review bank: D006 contact and props (32 questions)

Intro text with a period. And another.

## Questions

1. **AVQ-006-002** Does the hand meet the prop before the prop moves?
   - Failure hypothesis: The object responds before physical contact.
   - Check or fix: Inspect approach and first-motion frames.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32, visual_depth_contact.
2. **AVQ-006-003** A second question, e.g. with an abbreviation?
   - Failure hypothesis: Something fails. Then more.
   - Check or fix: Compare frames 1-2.
   - Severity: medium. Modes: visual, machine. Stages: edit. Style filters: 3d, cutout.
"""


def test_parse_bank_markdown_reads_placed_rules():
    qs = k.parse_bank_markdown(BANK_MD)
    assert [q["id"] for q in qs] == ["AVQ-006-002", "AVQ-006-003"]
    assert qs[0]["area"] == "contact and props" and qs[0]["domain_id"] == "D006"
    assert qs[0]["passes"] == ["default_32", "visual_depth_contact"]
    assert qs[1]["failure_hypothesis"] == "Something fails. Then more."
    assert qs[1]["modes"] == ["visual", "machine"] and qs[1]["style_filters"] == ["3d", "cutout"]
    assert qs[1]["passes"] == []
    assert k.parse_bank_markdown("# Something else\n") == []


def test_directory_scan_skips_other_banks_and_counts_duplicates_once(tmp_path):
    rules = tmp_path / ".baltor" / "rules"
    rules.mkdir(parents=True)
    (rules / "review-bank-contact-and-props.md").write_text(BANK_MD)
    other = tmp_path / "pkg" / "other-bank"
    other.mkdir(parents=True)
    (other / "questions.json").write_text(json.dumps([{"id": "background_system-001", "q": "?"}]))
    (other / "notes.md").write_text("# Notes\n")
    same = tmp_path / "pkg" / "review-bank-contact-and-props"
    same.mkdir(parents=True)
    (same / "questions.json").write_text(json.dumps([dict(BANK["AVQ-006-002"], question="Does the hand meet the "
                                                          "prop before the prop moves?",
                                                          failure_hypothesis="The object responds before physical "
                                                                             "contact.",
                                                          check_or_fix="Inspect approach and first-motion frames.")]))
    bank = k.load_bank([tmp_path])
    assert sorted(bank) == ["AVQ-006-002", "AVQ-006-003"]
    with pytest.raises(k.BankError):
        k.load_bank([other / "questions.json"])


def test_conflicting_text_for_one_id_is_an_error(tmp_path):
    (tmp_path / "a.md").write_text(BANK_MD)
    (tmp_path / "b.md").write_text(BANK_MD.replace("Does the hand meet", "Does a hand meet"))
    with pytest.raises(k.BankError):
        k.load_bank([tmp_path])


def test_shipped_passes_match_the_guide_counts():
    passes = k.load_passes()
    assert len(passes) == 9
    for pid, p in passes.items():
        assert len(p["question_ids"]) == p["declared_count"] == len(set(p["question_ids"])), pid
    assert passes["default_32"]["declared_count"] == 32
    assert passes["accessible_text"]["declared_count"] == 50


def test_cli_plan_and_validate(tmp_path, capsys):
    film = tmp_path / "final.mp4"
    film.write_bytes(b"not really a film")
    bank = tmp_path / "questions.json"
    bank.write_text(json.dumps(list(BANK.values())))
    passes = tmp_path / "passes.json"
    passes.write_text(json.dumps(PASSES))
    assert k.main(["plan", "--bank", str(bank), "--passes", str(passes), "--pass", "tiny",
                   "--target", str(film), "--stage", "final-encode", "--modes", "machine"]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert [r["status"] for r in plan] == ["untested", "blocked"]
    out = tmp_path / "results.json"
    out.write_text(json.dumps(plan))
    assert k.main(["validate", str(out), "--bank", str(bank), "--target", str(film)]) == 0
    stale = [dict(observed(question_id="AVQ-029-001"), review_mode="machine")]
    out.write_text(json.dumps(stale))
    assert k.main(["validate", str(out), "--bank", str(bank), "--target", str(film)]) == 1
