from caption_linter import lint, summary


def cue(s, e, t):
    return {"start": s, "end": e, "text": t}


def test_clean_track_passes():
    cues = [cue(0.1, 1.5, "In 1970, five scientists"), cue(1.6, 3.0, "lived underwater for 14 days")]
    words = [{"start": 0.1}, {"start": 1.62}]
    assert lint(cues, video_duration=64, words=words) == []


def test_all_rules_fire():
    cues = [cue(0, 0.2, "one two three four five six seven eight"), cue(0.1, 9, "FACT 1\nsecond line"),
            cue(9, 10, "███░░"), cue(10, 70, "")]
    rules = summary(lint(cues, video_duration=64, words=[{"start": 5.0}]))["by_rule"]
    for r in ("max_words", "min_duration", "overlap", "label_in_caption", "max_lines", "max_duration",
              "progress_bar", "empty", "bounds", "sync"):
        assert r in rules, r


def test_summary_pass():
    assert summary([]) == {"passed": True, "count": 0, "by_rule": {}}
