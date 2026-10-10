import hook


def manifest(*assets):
    return {"spec": "baltor.media-pack/v1", "pack_id": "p", "assets": list(assets)}


def test_unlisted_media_is_blocked_and_code_is_ignored():
    problems = hook.classify([("art/hero.png", "a" * 64), ("src/main.py", None)], [manifest()])
    assert len(problems) == 1 and "not listed" in problems[0]


def test_listed_by_name_or_hash_passes():
    m = manifest({"file_name": "hero.png", "redistribution": "allowed", "licence": "CC0-1.0"},
                 {"sha256": "b" * 64, "redistribution": "allowed-with-licence", "licence": "CC-BY-4.0"})
    assert hook.classify([("art/hero.png", "c" * 64), ("models/renamed.glb", "b" * 64)], [m]) == []


def test_project_only_files_are_blocked_even_when_listed():
    m = manifest({"file_name": "Running.fbx", "redistribution": "forbidden", "licence": "Adobe Mixamo terms"})
    problems = hook.classify([("anim/Running.fbx", None)], [m])
    assert problems and "does not allow redistributing" in problems[0]
