import pytest

from caption_gap_fixer import fix_timing, problems, snap


def test_overlap_and_flicker_fixed():
    cues = [{"start": 0.0, "end": 1.2, "text": "a"}, {"start": 1.0, "end": 2.0, "text": "b"},
            {"start": 2.1, "end": 3.0, "text": "c"}, {"start": 4.0, "end": 5.0, "text": "d"}]
    assert problems(cues)
    out = fix_timing(cues, fps=30)
    assert not problems(out)
    assert out[0]["end"] == pytest.approx(1.0 - 2 / 30, abs=1e-6)
    assert out[1]["end"] == pytest.approx(2.1 - 2 / 30, abs=1e-6)  # 0.1 s flicker gap closed
    assert out[2]["end"] == 3.0  # 1 s real gap kept


def test_snapping_and_min_duration():
    out = fix_timing([{"start": 0.011, "end": 0.05, "text": "x"}], fps=25, min_duration_frames=5)
    assert out[0]["start"] == 0.0 and out[0]["end"] == pytest.approx(0.2)
    assert snap(1.03, 25) == pytest.approx(1.04) and snap(1.019, 25) == pytest.approx(1.0)


def test_sorting_and_validation():
    out = fix_timing([{"start": 2, "end": 3}, {"start": 0, "end": 1}])
    assert out[0]["start"] == 0
    with pytest.raises(ValueError):
        fix_timing([], fps=0)
