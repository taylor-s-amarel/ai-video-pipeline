import json

import pytest

from render_manifest_writer import build_manifest, find_duplicates, verify, write_manifest


def make(tmp_path, name, content):
    p = tmp_path / name
    p.write_bytes(content)
    return str(p)


def test_build_write_verify(tmp_path):
    a = make(tmp_path, "photo.jpg", b"jpegdata")
    o = make(tmp_path, "out.mp4", b"videodata")
    m = build_manifest("job-1", {"photo": a}, {"video": o}, params={"fps": 30}, tools={"ffmpeg": "6.1"},
                       credits=["Music: X, CC BY 4.0"], created="2026-10-10")
    assert m["inputs"][0]["bytes"] == 8 and len(m["inputs"][0]["sha256"]) == 64
    out = tmp_path / "m.json"
    write_manifest(m, str(out))
    assert json.loads(out.read_text())["job_id"] == "job-1"
    assert verify(m) == []
    (tmp_path / "out.mp4").write_bytes(b"changed")
    assert verify(m) == [f"changed video: {o}"]


def test_duplicates_and_validation(tmp_path):
    o = make(tmp_path, "v.mp4", b"same")
    m1 = build_manifest("door-v1", {}, {"video": o})
    m2 = build_manifest("new-topic-v1", {}, {"video": o})
    assert find_duplicates([m1, m2])[0][1:] == ("door-v1", "new-topic-v1")
    with pytest.raises(ValueError):
        build_manifest("bad id", {}, {})
    with pytest.raises(FileNotFoundError):
        build_manifest("x", {"a": str(tmp_path / "missing")}, {})
