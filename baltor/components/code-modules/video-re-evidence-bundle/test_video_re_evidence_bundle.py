import json
import shutil

import numpy as np
import pytest

import video_re_common as common
import video_re_evidence_bundle as m
import video_re_synth as synth


def siblings_available():
    try:
        for name in m.MODULES:
            common.import_sibling(name)
    except ImportError:
        return False
    return True


FAKE = {
    "probe": {"source": {"reference": "x.mp4", "duration_s": 4.0, "width": 1080, "height": 1920, "fps": 30.0,
                         "has_audio": True}},
    "shots": {"shots": [{"index": 0, "start_s": 0.0, "end_s": 2.0, "duration_s": 2.0},
                        {"index": 1, "start_s": 2.0, "end_s": 4.0, "duration_s": 2.0}]},
    "shot_stats": {"count": 2, "median_s": 2.0, "mean_s": 2.0, "cut_rate_per_min": 15.0, "cv": 0.0},
    "keyframes": {"keyframes": [{"index": 0, "path": "keyframes/shot_000.jpg"}]},
    "palette": {"shots": [{"index": 0, "palette": ["#FFD21F"]}, {"index": 1, "palette": ["#0A1428", "#FFFFFF"]}]},
    "motion": {"shots": [{"index": 0, "center": 1.5, "border": 3.0}, {"index": 1, "center": None, "border": None}]},
    "camera": {"shots": [{"index": 0, "pan_x": 0.1, "pan_y": 0.0, "zoom": 0.02}]},
    "text": {"regions": [{"t_s": 0.0, "bbox": [100, 300, 800, 160], "area_ratio": 0.06, "y_center_ratio": 0.2,
                          "score": 0.9}]},
    "captions": {"captions": [{"start_s": 0.5, "end_s": 1.5, "text": "FACT 1: 14 days"}]},
    "loudness": {"integrated_lufs": -14.2, "loudness_range": 5.1},
    "speech": {"segments": [{"start_s": 0.2, "end_s": 3.8, "syllabic_modulation": 9.0}]},
    "beats": {"onsets_s": [0.5, 1.0], "tempo_bpm": 120.0},
    "rate": {"speech_wpm": 150.0},
    "alignment": {"cuts_on_beat_ratio": 1.0},
    "overlay": {"semi_transparent_ratio": 1.0},
    "safe_area": {"violations": [{"t_s": 0.0, "zone": "top-ui", "bbox": [0, 0, 100, 50], "overlap_ratio": 1.0}]},
}


def test_assembled_evidence_matches_the_schema_exactly():
    ev = m.assemble(m.empty_evidence("x.mp4"), FAKE)
    ev["tools"] = {"ffmpeg": "6.1"}
    assert m.validate(common.clean(ev)) == []
    assert ev["shots"][0] == {"index": 0, "start_s": 0.0, "end_s": 2.0, "duration_s": 2.0,
                              "keyframe": "keyframes/shot_000.jpg", "palette": ["#FFD21F"],
                              "motion_energy": {"center": 1.5, "border": 3.0},
                              "camera": {"pan_x": 0.1, "pan_y": 0.0, "zoom": 0.02}}
    assert ev["shots"][1]["keyframe"] is None and ev["shots"][1]["camera"] is None
    assert set(ev["text_regions"][0]) == {"t_s", "bbox", "area_ratio", "y_center_ratio"}
    assert ev["audio"]["speech_segments"] == [{"start_s": 0.2, "end_s": 3.8}]


def test_missing_results_stay_null_and_valid():
    ev = m.assemble(m.empty_evidence("y.mp4"), {"probe": FAKE["probe"]})
    assert m.validate(ev) == []
    assert ev["audio"]["tempo_bpm"] is None and ev["shots"] == [] and ev["overlay"]["semi_transparent_ratio"] is None


def test_schema_rejects_extra_or_invented_fields():
    ev = m.assemble(m.empty_evidence("x.mp4"), FAKE)
    ev["audio"]["mood"] = "upbeat"
    assert m.validate(ev)


def test_share_safe_masks_words_and_drops_frames():
    ev = m.assemble(m.empty_evidence("x.mp4"), FAKE)
    safe = m.share_safe(ev)
    assert safe["captions"][0]["text"] == "WORD {n}: {n} word"
    assert safe["shots"][0]["keyframe"] is None
    assert ev["captions"][0]["text"] == "FACT 1: 14 days"  # original untouched


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_skipped_modules_are_reported_not_guessed(tmp_path):
    path, _ = synth.lavfi_cuts_video(tmp_path / "v.mp4", 0.5, (160, 90), 25)
    ev = m.build(str(path), tmp_path / "ev", skip=set(m.SKIP_ALIASES) - {"probe_metadata"})
    assert ev["source"]["width"] == 160 and ev["shots"] == []
    assert any(e["message"] == "skipped by request" for e in ev["errors"])
    assert m.validate(ev) == []
    assert json.loads((tmp_path / "ev" / "evidence.json").read_text())["spec"] == m.SPEC


@pytest.mark.skipif(not shutil.which("ffmpeg") or not siblings_available(),
                    reason="ffmpeg or sibling video_re_* packages not available")
def test_full_bundle_on_synthetic_video(tmp_path):
    fps, size = 25, (160, 288)

    def frames():
        for seed, dx in ((1, 2.0), (2, -2.0), (3, 0.0)):
            yield from synth.pan_frames(25, size, dx_per_frame=dx, seed=seed)

    audio = synth.clicks(list(np.arange(0.0, 3.0, 0.5)), 3.0, 48000, noise=0.002)
    video = synth.make_av(tmp_path / "v.mp4", frames, fps, size, audio=audio, sr=48000)
    ev = m.build(str(video), tmp_path / "ev", fast=True, text_mode="masked")
    assert m.validate(ev) == []
    assert [round(s["start_s"], 2) for s in ev["shots"]] == [0.0, 1.0, 2.0]
    assert ev["shot_stats"]["count"] == 3
    assert ev["shots"][0]["camera"]["pan_x"] > 0 > ev["shots"][1]["camera"]["pan_x"]
    assert all(s["keyframe"] and (tmp_path / "ev" / s["keyframe"]).exists() for s in ev["shots"])
    assert ev["audio"]["tempo_bpm"] == pytest.approx(120, abs=3)
    assert ev["audio"]["cuts_on_beat_ratio"] == 1.0
    assert "ffmpeg" in ev["tools"] and ev["tools"]["video_re_detect_shots"] == "1.0.0"
    for e in ev["errors"]:
        assert e["module"] and e["message"]
    assert (tmp_path / "ev" / "details" / "video_re_detect_shots.json").exists()
    run = json.loads((tmp_path / "ev" / "details" / "_run.json").read_text())
    assert run["schema_problems"] == [] and run["options"]["text_mode"] == "masked"
