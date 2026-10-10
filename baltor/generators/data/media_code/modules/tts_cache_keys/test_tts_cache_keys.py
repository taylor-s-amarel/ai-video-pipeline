import pytest

from tts_cache_keys import TTSCache, cache_key, file_digest


def test_key_is_canonical():
    a = cache_key({"engine": "k", "voice": "v", "text": "hi", "speed": 1.0})
    b = cache_key({"speed": 1.0, "text": "hi", "voice": "v", "engine": "k"})
    assert a == b and len(a) == 64
    assert a != cache_key({"engine": "k", "voice": "v", "text": "hi", "speed": 1.1})
    with pytest.raises(ValueError):
        cache_key({"engine": "k"})


def test_get_or_create_once(tmp_path):
    cache = TTSCache(str(tmp_path))
    calls = []

    def create(p):
        calls.append(p)
        with open(p, "wb") as f:
            f.write(b"RIFF....")

    params = {"engine": "k", "voice": "v", "text": "hello"}
    p1 = cache.get_or_create(params, create)
    p2 = cache.get_or_create(params, create)
    assert p1 == p2 and len(calls) == 1 and p1.parent.name == p1.stem[:2]
    assert file_digest(str(p1)) == file_digest(str(p2))


def test_failed_create_leaves_nothing(tmp_path):
    cache = TTSCache(str(tmp_path))

    def boom(p):
        with open(p, "wb") as f:
            f.write(b"partial")
        raise OSError("engine crashed")

    with pytest.raises(OSError):
        cache.get_or_create({"engine": "k", "voice": "v", "text": "x"}, boom)
    assert cache.get({"engine": "k", "voice": "v", "text": "x"}) is None
    assert not list(tmp_path.rglob("*.part"))
