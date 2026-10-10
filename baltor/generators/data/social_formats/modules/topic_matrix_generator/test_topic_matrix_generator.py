import json
from pathlib import Path

import topic_matrix_generator as m

CONFIG = json.loads((Path(__file__).parent / "examples" / "topic_matrix_config.json").read_text())


def test_same_seed_same_output():
    assert m.generate(CONFIG, 20, seed=3) == m.generate(CONFIG, 20, seed=3)


def test_every_idea_needs_sources_and_has_breakdown():
    ideas = m.generate(CONFIG, 20)
    assert ideas
    for i in ideas:
        assert i["status"] == "needs-sources"
        assert set(i["score_breakdown"]) >= {"specificity", "curiosity", "format_fit", "novelty", "risk"}
        assert "{" not in i["title"]


def test_exclusions_and_angle_niche_limits_respected():
    ideas = m.expand(CONFIG)
    assert not any(i.niche == "money" and i.format == "what-if-scenario" for i in ideas)
    assert not any(i.angle == "what-if" and i.niche == "history" for i in ideas)
    # hooks restricted to formats/angles
    assert all(i.format in ("size-scale-comparison", "versus-comparison") for i in ideas if i.hook == "really")
    assert all(i.angle == "scale" for i in ideas if i.hook == "really")


def test_diversity_caps():
    ideas = m.generate(CONFIG, 50)
    from collections import Counter
    assert max(Counter(i["format"] for i in ideas).values()) <= 3
    assert max(Counter(i["niche"] for i in ideas).values()) <= 4
    assert max(Counter((i["niche"], i["subject"]) for i in ideas).values()) <= 1


def test_risk_flag_penalises_finance():
    ideas = m.expand(CONFIG)
    ctx = m.Context(history_tokens=[], seed=0)
    m.score_all(ideas, ctx, m.DEFAULT_WEIGHTS, m.SCORERS)
    money = [i for i in ideas if i.niche == "money"]
    assert money and all("regulated-finance" in i.risk_flags for i in money)
    assert all(i.score_breakdown["risk"] > 0 for i in money)


def test_dedupe_removes_near_duplicates():
    a = m.Idea("n", "Europa", "x", "f", "h", "How big is Europa, really?", "x")
    b = m.Idea("n", "Europa", "y", "f", "h2", "How big is Europa really", "y")
    c = m.Idea("n", "Io", "x", "f", "h", "How big is Io, really?", "x")
    assert [i.title for i in m.dedupe([a, b, c])] == [a.title, c.title]


def test_history_lowers_novelty():
    fresh = m.generate(CONFIG, 50, seed=1)
    top = fresh[0]
    again = m.generate(CONFIG, 50, seed=1, history=[top["title"] + " " + top["subject"]])
    same = [i for i in again if i["id"] == top["id"]]
    assert not same or same[0]["score"] < top["score"]


def test_custom_scorer_hook_changes_ranking():
    def prefer_animals(idea, ctx):
        return 5.0 if idea.niche == "animals" else 0.0
    ideas = m.generate(CONFIG, 5, scorers={"animals_first": prefer_animals})
    assert ideas[0]["niche"] == "animals"
    assert "animals_first" in ideas[0]["score_breakdown"]


def test_unfilled_placeholder_raises():
    bad = json.loads(json.dumps(CONFIG))
    bad["hooks"].append({"id": "broken", "template": "{subject} and {missing}", "formats": ["*"]})
    try:
        m.expand(bad)
    except ValueError as exc:
        assert "unfilled" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_cli_tsv(capsys):
    path = str(Path(__file__).parent / "examples" / "topic_matrix_config.json")
    assert m.main([path, "--limit", "5", "--format", "tsv"]) == 0
    out = capsys.readouterr().out.splitlines()
    assert out[0].startswith("score\tformat") and len(out) == 6
