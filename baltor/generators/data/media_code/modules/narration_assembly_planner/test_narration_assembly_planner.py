import shutil
import subprocess
import wave

import pytest

from narration_assembly_planner import ffmpeg_argv, plan


def test_plan_offsets_and_words():
    p = plan([{"file": "a.wav", "duration": 2.0, "boundary": "sentence",
               "words": [{"word": "Hi", "start": 0.1, "end": 0.4}]},
              {"file": "b.wav", "duration": 1.0, "boundary": "paragraph"},
              {"file": "c.wav", "duration": 1.5, "boundary": "end"}])
    assert [c["start"] for c in p["chunks"]] == [0.3, 2.55, 4.15]
    assert p["words"][0] == {"word": "Hi", "start": 0.4, "end": 0.7}
    assert p["duration"] == pytest.approx(6.15)


def test_validation():
    with pytest.raises(ValueError):
        plan([{"duration": 0}])
    with pytest.raises(ValueError):
        plan([{"duration": 1, "boundary": "chapter"}])
    with pytest.raises(ValueError):
        ffmpeg_argv(plan([{"duration": 1}]), "o.wav")


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_mix_renders_expected_length(tmp_path):
    files = []
    for i, d in enumerate((0.5, 0.7)):
        f = tmp_path / f"c{i}.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", f"sine=f=440:d={d}:r=24000",
                        str(f)], check=True, timeout=60)
        files.append({"file": str(f), "duration": d, "boundary": "sentence"})
    p = plan(files, lead_in=0.2, tail=0.3)
    out = tmp_path / "n.wav"
    argv = ffmpeg_argv(p, str(out))
    r = subprocess.run(argv[:1] + ["-v", "error"] + argv[1:], capture_output=True, timeout=60)
    assert r.returncode == 0, r.stderr.decode()
    with wave.open(str(out)) as w:
        assert abs(w.getnframes() / w.getframerate() - p["duration"]) < 0.03
