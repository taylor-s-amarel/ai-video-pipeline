import json

import pytest

import asset_licence_checker as c


def asset(**kw):
    base = {"id": "a", "title": "A", "source_url": "https://example.org/a", "licence": "CC0-1.0",
            "licence_url": "https://creativecommons.org/publicdomain/zero/1.0/deed.en", "attribution": "",
            "attribution_required": False, "format": "png", "fetch": {"method": "manual-page"}}
    base.update(kw)
    return base


def pack(*assets):
    return {"spec": "baltor.media-pack/v1", "pack_id": "p", "title": "P", "status": "manifest-only", "assets": list(assets)}


def rules(findings, level="error"):
    return {f.rule for f in findings if f.level == level}


def test_cc0_passes_everywhere():
    for use in c.PROFILES:
        assert rules(c.check_manifest(pack(asset()), use)) == set()


def test_non_commercial_blocked_for_monetised_video_only():
    a = asset(licence="CC-BY-NC-SA-4.0", attribution="Model by X (CC BY-NC-SA 4.0)", attribution_required=True)
    assert "non-commercial" in rules(c.check_manifest(pack(a), "monetised-video"))
    assert "non-commercial" not in rules(c.check_manifest(pack(a), "personal-study"))


def test_no_derivatives_only_when_modified():
    a = asset(id="nd", licence="CC-BY-ND-4.0", attribution="Scan by Y", attribution_required=True)
    assert "no-derivatives" not in rules(c.check_manifest(pack(a), "monetised-video"))
    assert "no-derivatives" in rules(c.check_manifest(pack(a), "monetised-video", {"nd"}))


def test_mixamo_raw_files_cannot_go_in_repo_or_package():
    a = asset(id="run", licence="Adobe Mixamo terms", licence_url="https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html",
              redistribution="forbidden", ai_training="forbidden")
    assert "redistribution" in rules(c.check_manifest(pack(a), "open-source-repo"))
    assert "redistribution" in rules(c.check_manifest(pack(a), "baltor-package"))
    assert "redistribution" not in rules(c.check_manifest(pack(a), "monetised-video"))
    assert "ai-training" in rules(c.check_manifest(pack(a), "ai-training"))
    assert "custom-terms" in rules(c.check_manifest(pack(a), "monetised-video"), "warning")


def test_missing_credit_line():
    a = asset(licence="CC-BY-3.0", attribution="", attribution_required=True)
    assert "attribution" in rules(c.check_manifest(pack(a), "monetised-video"))
    a["attribution"] = "Icon by Lorc, game-icons.net, CC BY 3.0"
    assert "attribution" not in rules(c.check_manifest(pack(a), "monetised-video"))


def test_drm_platform_flags_cc_by_3_but_not_oga_by():
    by3 = asset(id="by3", licence="CC-BY-3.0", attribution="x", attribution_required=True)
    oga = asset(id="oga", licence="OGA-BY-3.0", attribution="y", attribution_required=True)
    found = c.check_manifest(pack(by3, oga), "drm-platform-game")
    assert {f.asset_id for f in found if f.rule == "no-drm"} == {"by3"}


def test_share_alike_warning_when_modified():
    a = asset(id="sa", licence="CC-BY-SA-4.0", attribution="z", attribution_required=True)
    assert "share-alike" in rules(c.check_manifest(pack(a), "monetised-video", {"sa"}), "warning")


def test_missing_licence_is_error_and_unknown_profile_raises():
    a = asset(licence="", licence_url="")
    assert "licence-recorded" in rules(c.check_manifest(pack(a), "personal-study"))
    with pytest.raises(KeyError):
        c.check_manifest(pack(a), "anything-goes")


def test_cli(tmp_path, capsys):
    p = tmp_path / "pack.json"
    p.write_text(json.dumps(pack(asset(), asset(id="nc", licence="CC-BY-NC-4.0", attribution="n", attribution_required=True))))
    assert c.main([str(p), "--use", "personal-study"]) == 0
    assert c.main([str(p), "--use", "monetised-video", "--json"]) == 1
    assert '"errors": 1' in capsys.readouterr().out
