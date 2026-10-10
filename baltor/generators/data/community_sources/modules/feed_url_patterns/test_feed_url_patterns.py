import pytest

import feed_url_patterns as p


def test_reddit():
    assert p.reddit("godot") == "https://www.reddit.com/r/godot/.rss"
    assert p.reddit("r/3Dprinting", sort="new") == "https://www.reddit.com/r/3Dprinting/new/.rss"
    assert p.reddit("AI_Agents", sort="top", period="week") == "https://www.reddit.com/r/AI_Agents/top/.rss?t=week"
    for bad in ("", "bad name", "x" * 30, "../etc"):
        with pytest.raises(ValueError):
            p.reddit(bad)
    with pytest.raises(ValueError):
        p.reddit("godot", period="week")


def test_github():
    assert p.github("godotengine/godot") == "https://github.com/godotengine/godot/releases.atom"
    assert p.github("FFmpeg/FFmpeg", "tags") == "https://github.com/FFmpeg/FFmpeg/tags.atom"
    assert p.github("hexgrad/kokoro", "commits", "main") == "https://github.com/hexgrad/kokoro/commits/main.atom"
    for bad in ("nogood", "a/b/c", "a/../b"):
        with pytest.raises(ValueError):
            p.github(bad)
    with pytest.raises(ValueError):
        p.github("a/b", "issues")
    with pytest.raises(ValueError):
        p.github("a/b", "commits", "../../x")


def test_youtube_channel_needs_real_channel_id():
    cid = "UCxboW7x0jZqFdvMdCFKTMsQ"
    assert p.youtube_channel(cid).endswith(f"channel_id={cid}")
    for bad in ("@gdquest", "UCshort", "XX" + cid[2:]):
        with pytest.raises(ValueError):
            p.youtube_channel(bad)


def test_arxiv():
    assert p.arxiv("cs.AI") == "https://rss.arxiv.org/rss/cs.AI"
    assert p.arxiv("cs.SD", "eess.AS", fmt="atom") == "https://rss.arxiv.org/atom/cs.SD+eess.AS"
    with pytest.raises(ValueError):
        p.arxiv()
    with pytest.raises(ValueError):
        p.arxiv("cs AI")


def test_discourse_mastodon_bluesky():
    assert p.discourse("forum.godotengine.org") == "https://forum.godotengine.org/latest.rss"
    assert p.discourse("https://devtalk.blender.org/", "top") == "https://devtalk.blender.org/top.rss"
    assert p.discourse("meta.discourse.org", category=("feature", 2)) == "https://meta.discourse.org/c/feature/2.rss"
    with pytest.raises(ValueError):
        p.discourse("localhost")
    assert p.mastodon("mastodon.social", "@someone@mastodon.social") == "https://mastodon.social/@someone.rss"
    assert p.bluesky("@example.bsky.social") == "https://bsky.app/profile/example.bsky.social/rss"
    with pytest.raises(ValueError):
        p.bluesky("not a handle")


def test_hnrss_substack_itch_wikipedia():
    assert p.hnrss("godot", "blender") == "https://hnrss.org/newest?q=godot+OR+blender"
    assert p.hnrss(endpoint="show", points=50) == "https://hnrss.org/show?points=50"
    assert p.hnrss("Claude Code") == "https://hnrss.org/newest?q=Claude+Code"
    assert p.substack("importai") == "https://importai.substack.com/feed"
    assert p.substack("https://www.oneusefulthing.org/p/x") == "https://www.oneusefulthing.org/feed"
    assert p.itch_devlog("Daxior", "fit-in") == "https://daxior.itch.io/fit-in/devlog.rss"
    assert p.wikipedia_featured() == \
        "https://en.wikipedia.org/w/api.php?action=featuredfeed&feed=onthisday&feedformat=atom"
    with pytest.raises(ValueError):
        p.wikipedia_featured("random")


@pytest.mark.parametrize("builder,args,platform", [
    (p.reddit, ("godot", "top", "day"), "reddit"),
    (p.github, ("a/b", "commits", "dev/next"), "github"),
    (p.youtube_channel, ("UCxboW7x0jZqFdvMdCFKTMsQ",), "youtube"),
    (p.arxiv, ("cs.GR", "cs.CV"), "arxiv"),
    (p.discourse, ("blenderartists.org",), "discourse"),
    (p.mastodon, ("mastodon.gamedev.place", "godot"), "mastodon"),
    (p.bluesky, ("example.com",), "bluesky"),
    (p.hnrss, ("ffmpeg",), "hnrss"),
    (p.substack, ("interconnects",), "substack"),
    (p.itch_devlog, ("dev", "game"), "itch"),
    (p.wikipedia_featured, ("potd", "de"), "wikipedia"),
])
def test_identify_round_trips(builder, args, platform):
    assert p.identify(builder(*args))[0] == platform


def test_identify_details_and_unknown():
    assert p.identify("https://github.com/a/b/commits/dev/next.atom")[1] == \
        {"repo": "a/b", "kind": "commits", "branch": "dev/next"}
    assert p.identify("https://rss.arxiv.org/rss/cs.SD+eess.AS")[1]["categories"] == ["cs.SD", "eess.AS"]
    assert p.identify("https://example.org/blog") == ("unknown", {})
