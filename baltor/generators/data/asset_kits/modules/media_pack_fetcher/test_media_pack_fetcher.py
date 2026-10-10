import hashlib
import json

import pytest

import media_pack_fetcher as m

PNG = b"\x89PNG\r\n\x1a\n" + b"pixels" * 10
GLB = b"glTF" + b"\x02\x00\x00\x00" + b"x" * 32


def manifest():
    return {
        "spec": "baltor.media-pack/v1",
        "pack_id": "test-pack",
        "title": "Test pack",
        "status": "manifest-only",
        "assets": [
            {"id": "tiles", "title": "Tiles", "creator": "Kenney", "source_url": "https://kenney.nl/assets/tiny-town",
             "download_url": "https://raw.githubusercontent.com/example/repo/main/tiles.png",
             "licence": "CC0-1.0", "licence_url": "https://creativecommons.org/publicdomain/zero/1.0/deed.en",
             "attribution": "Tiles by Kenney (CC0)", "attribution_required": False, "format": "png",
             "fetch": {"method": "direct", "status": "to-fetch"}},
            {"id": "icon", "title": "Crossed swords", "creator": "Lorc",
             "source_url": "https://game-icons.net/about.html",
             "download_url": "https://raw.githubusercontent.com/game-icons/icons/master/lorc/crossed-swords.svg",
             "licence": "CC-BY-3.0", "licence_url": "https://creativecommons.org/licenses/by/3.0/deed.en",
             "attribution": "Icon by Lorc, game-icons.net, CC BY 3.0", "attribution_required": True,
             "format": "svg", "sha256": hashlib.sha256(b"<svg/>").hexdigest(),
             "fetch": {"method": "direct", "status": "to-fetch"}},
            {"id": "hero-anim", "title": "Run cycle", "source_url": "https://www.mixamo.com/",
             "licence": "Adobe Mixamo terms", "licence_url": "https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html",
             "attribution": "", "attribution_required": False, "format": "fbx", "redistribution": "forbidden",
             "fetch": {"method": "manual-page", "status": "manual"}},
        ],
    }


def fake(mapping):
    calls = []

    def fetch(url, max_bytes):
        calls.append(url)
        if url not in mapping:
            raise m.FetchError(f"404 {url}")
        return mapping[url]

    fetch.calls = calls
    return fetch


def test_host_allow_list_requires_https_and_exact_or_wildcard():
    allowed = ["raw.githubusercontent.com", "*.example.org"]
    assert m.host_allowed("https://raw.githubusercontent.com/a/b", allowed)
    assert not m.host_allowed("http://raw.githubusercontent.com/a/b", allowed)
    assert not m.host_allowed("https://evil.com/raw.githubusercontent.com", allowed)
    assert not m.host_allowed("https://raw.githubusercontent.com.evil.com/x", allowed)
    assert m.host_allowed("https://cdn.example.org/x", allowed)
    assert not m.host_allowed("https://example.org/x", allowed)


def test_safe_name_blocks_traversal():
    assert m.safe_name("../../etc/passwd") == "passwd"
    assert m.safe_name("..") == "asset.bin"
    assert "/" not in m.safe_name("a/b\\c.png")


def test_fetch_records_hash_and_verifies_known_hash(tmp_path):
    f = fake({"https://raw.githubusercontent.com/example/repo/main/tiles.png": PNG,
              "https://raw.githubusercontent.com/game-icons/icons/master/lorc/crossed-swords.svg": b"<svg/>"})
    updated, report = m.fetch_pack(manifest(), tmp_path, fetcher=f, today="2026-10-10")
    actions = {r.asset_id: r.action for r in report.results}
    assert actions == {"tiles": "fetched", "icon": "verified", "hero-anim": "skipped-manual"}
    tiles = next(a for a in updated["assets"] if a["id"] == "tiles")
    assert tiles["sha256"] == hashlib.sha256(PNG).hexdigest()
    assert tiles["bytes"] == len(PNG)
    assert (tmp_path / "tiles" / "tiles.png").read_bytes() == PNG
    assert updated["status"] == "partially-fetched"
    assert report.ok


def test_hash_mismatch_is_rejected_and_not_written(tmp_path):
    f = fake({"https://raw.githubusercontent.com/example/repo/main/tiles.png": PNG,
              "https://raw.githubusercontent.com/game-icons/icons/master/lorc/crossed-swords.svg": b"<svg>tampered"})
    updated, report = m.fetch_pack(manifest(), tmp_path, fetcher=f)
    icon = next(r for r in report.results if r.asset_id == "icon")
    assert icon.action == "failed" and "mismatch" in icon.detail
    assert not (tmp_path / "icon").exists()
    assert not report.ok


def test_blocked_host_is_never_requested(tmp_path):
    man = manifest()
    man["assets"][0]["download_url"] = "https://downloads.example.net/tiles.zip"
    f = fake({})
    _, report = m.fetch_pack(man, tmp_path, fetcher=f, allowed=["raw.githubusercontent.com"])
    assert "https://downloads.example.net/tiles.zip" not in f.calls
    assert {r.asset_id: r.action for r in report.results}["tiles"] == "blocked"


def test_forbidden_redistribution_with_direct_method_is_blocked(tmp_path):
    man = manifest()
    man["assets"][2]["fetch"] = {"method": "direct"}
    man["assets"][2]["download_url"] = "https://raw.githubusercontent.com/x/y/z.fbx"
    _, report = m.fetch_pack(man, tmp_path, fetcher=fake({}))
    assert {r.asset_id: r.action for r in report.results}["hero-anim"] == "blocked"


def test_size_cap(tmp_path):
    f = fake({"https://raw.githubusercontent.com/example/repo/main/tiles.png": b"x" * 2048,
              "https://raw.githubusercontent.com/game-icons/icons/master/lorc/crossed-swords.svg": b"<svg/>"})
    _, report = m.fetch_pack(manifest(), tmp_path, fetcher=f, max_bytes=1024)
    assert {r.asset_id: r.action for r in report.results}["tiles"] == "failed"


def test_dry_run_writes_nothing(tmp_path):
    f = fake({})
    _, report = m.fetch_pack(manifest(), tmp_path, fetcher=f, dry_run=True)
    assert f.calls == []
    assert not any(tmp_path.iterdir())
    assert {r.action for r in report.results} == {"dry-run", "skipped-manual"}


def test_redirect_to_other_host_is_refused():
    fetcher = m.UrllibFetcher(["raw.githubusercontent.com"], pause_s=0)
    fetcher.check_redirect("https://raw.githubusercontent.com/ok")
    with pytest.raises(m.FetchError):
        fetcher.check_redirect("https://attacker.example/payload")
    with pytest.raises(m.FetchError):
        fetcher("http://raw.githubusercontent.com/insecure", 10)


def test_credits_markdown_sections():
    text = m.credits_markdown(manifest())
    assert "## Attribution required" in text
    assert "Icon by Lorc, game-icons.net, CC BY 3.0" in text
    assert "## No attribution required" in text
    assert "## Restrictions" in text and "do not redistribute" in text
    assert text.index("Attribution required") < text.index("No attribution required")


def test_cli_writes_lock_and_credits(tmp_path, monkeypatch):
    man = manifest()
    man["assets"] = [man["assets"][2]]  # manual only: no network needed
    p = tmp_path / "pack.json"
    p.write_text(json.dumps(man))
    out = tmp_path / "out"
    assert m.main([str(p), "--out", str(out)]) == 0
    assert json.loads((out / "pack.lock.json").read_text())["pack_id"] == "test-pack"
    assert "Run cycle" in (out / "CREDITS.md").read_text()
