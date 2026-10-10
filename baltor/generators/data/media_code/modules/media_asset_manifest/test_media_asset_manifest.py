from media_asset_manifest import Asset, credits_block, default_credit, file_sha256, to_records, validate

MUSIC = Asset("music/hands.mp3", "audio", "CC-BY-4.0", author="Scott Buckley", title="With These Hands",
              source_url="https://www.scottbuckley.com.au/library/with-these-hands/")


def test_valid_cc_by_passes_and_credit():
    assert validate([MUSIC]) == []
    c = default_credit(MUSIC)
    assert "Scott Buckley" in c and "CC BY 4.0" in c and "With These Hands" in c
    assert credits_block([MUSIC, MUSIC]).count("Scott Buckley") == 1


def test_rejects_fair_use_and_flags_nc_nd():
    probs = validate([Asset("a.jpg", "image", "fair use"),
                      Asset("b.jpg", "image", "CC-BY-NC-4.0", author="x", title="t", source_url="https://e.org"),
                      Asset("c.jpg", "image", "CC-BY-ND-4.0", author="x", title="t", source_url="https://e.org")])
    text = " ".join(probs)
    assert "not a licence" in text and "commercial" in text and "edited" in text


def test_missing_attribution_and_unknown():
    probs = validate([Asset("d.jpg", "image", "CC-BY-4.0", source_url="https://e.org"), Asset("e.jpg", "image", "MIT-ish")])
    assert any("requires attribution" in p for p in probs) and any("unknown licence" in p for p in probs)


def test_sha_and_records(tmp_path):
    p = tmp_path / "f.bin"
    p.write_bytes(b"abc")
    assert file_sha256(str(p)) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert to_records([MUSIC])[0]["licence"] == "CC-BY-4.0"
