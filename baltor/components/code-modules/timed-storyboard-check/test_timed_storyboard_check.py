import copy
import json
from pathlib import Path

import timed_storyboard_check as m

FIXTURES = Path(__file__).with_name("fixtures")


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def errors(board):
    return [f for f in m.check_board(board) if f.level == "error"]


def test_guide_board_has_complete_structure():
    board = load("the_decoy_job.json")
    assert m.check_board(board) == []


def test_guide_pitch_has_complete_structure():
    assert m.check_board(load("front_legs_back_legs.json")) == []


def test_gap_between_shots_is_an_error():
    board = load("the_decoy_job.json")
    board["shots"][3]["start_s"] += 2
    msgs = [f.message for f in errors(board)]
    assert any(msg.startswith("gap") for msg in msgs)


def test_overlap_between_shots_is_an_error():
    board = load("the_decoy_job.json")
    board["shots"][4]["start_s"] -= 1
    assert any(f.message.startswith("overlap") for f in errors(board))


def test_missing_kill_criteria_and_plant_are_errors():
    board = load("the_decoy_job.json")
    del board["kill_criteria"]
    board["planted_details"] = "  "
    fields = {f.field for f in errors(board)}
    assert {"kill_criteria", "planted_details"} <= fields


def test_shot_count_mismatch_is_an_error():
    board = load("the_decoy_job.json")
    board["shots"] = board["shots"][:9]
    fields = {f.field for f in errors(board)}
    assert "shot_count" in fields


def test_duration_mismatch_is_a_warning_not_an_error():
    board = load("the_decoy_job.json")
    board["approx_duration_s"] = 90
    found = m.check_board(board)
    assert [f.field for f in found] == ["approx_duration_s"]
    assert found[0].level == "warning"


def test_single_link_escalation_is_flagged():
    board = load("the_decoy_job.json")
    board["escalation_chain"] = ["The thief tries again"]
    assert any(f.field == "escalation_chain" and f.level == "warning" for f in m.check_board(board))


def test_pitch_missing_visual_test_is_an_error():
    pitch = load("front_legs_back_legs.json")
    pitch.pop("visual_test")
    assert [f.field for f in errors(pitch)] == ["visual_test"]


def test_unknown_board_type_is_rejected():
    board = copy.deepcopy(load("the_decoy_job.json"))
    board["board_type"] = "animatic"
    assert errors(board)[0].field == "board_type"


def test_review_sheet_lists_every_question_as_not_checked():
    sheet = m.review_sheet(load("the_decoy_job.json"))
    for q in m.RULES["storyboard_gate"]["questions"]:
        assert q in sheet
    for q in m.RULES["story_tests"]["questions"]:
        assert q in sheet
    assert sheet.count("not checked") >= len(m.RULES["storyboard_gate"]["questions"]) * 2
    assert "not audience evidence" in sheet
    assert len(m.RULES["storyboard_gate"]["questions"]) == 10
    assert len(m.RULES["story_tests"]["questions"]) == 7


def test_cli_exit_codes(tmp_path, capsys):
    good = tmp_path / "good.json"
    good.write_text(json.dumps(load("the_decoy_job.json")), encoding="utf-8")
    assert m.main([str(good)]) == 0
    bad = load("the_decoy_job.json")
    bad["shots"][2]["end_s"] = bad["shots"][2]["start_s"]
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(bad), encoding="utf-8")
    assert m.main([str(path)]) == 1
    capsys.readouterr()
