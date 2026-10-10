from datetime import datetime, timezone

import page_change_watcher as w

V1 = """<html><head><style>.x{}</style><script>var t=1</script></head><body>
<nav>Home | Help</nav><header>Cookie banner</header>
<h1>Channel monetization policies</h1>
<p>Repetitious content is not eligible. Content must be original.</p>
<p>Updated 2025-07-01</p>
<footer>Footer links</footer></body></html>"""
V2 = V1.replace("Repetitious content is not eligible.", "Inauthentic content is not eligible.")
V1_NEW_DATE_ONLY = V1.replace("<p>Updated 2025-07-01</p>", "<p>2025-07-15</p>")


def test_extract_text_drops_chrome_and_scripts():
    text = w.extract_text(V1)
    assert "Cookie banner" not in text and "var t" not in text and "Home | Help" not in text
    assert text.splitlines()[0] == "Channel monetization policies"
    assert w.extract_text(V1, selector_text="content must").startswith("Repetitious content")


def test_fingerprint_ignores_whitespace_and_number_only_lines():
    assert w.fingerprint("A  b\n\nC") == w.fingerprint("a b\nc")
    assert w.fingerprint(w.extract_text(V1.replace("Updated 2025-07-01", "2025-07-01"))) == \
        w.fingerprint(w.extract_text(V1_NEW_DATE_ONLY))
    assert w.fingerprint("a") != w.fingerprint("b")


def test_diff_summary_reports_changed_sentences():
    d = w.diff_summary(w.extract_text(V1), w.extract_text(V2))
    assert d["added"] == ["Inauthentic content is not eligible."]
    assert d["removed"] == ["Repetitious content is not eligible."]


class FakeFetcher:
    def __init__(self, pages):
        self.pages = list(pages)
        self.calls = []

    def __call__(self, url, etag, last_modified):
        self.calls.append((url, etag, last_modified))
        return self.pages.pop(0)


def test_check_first_seen_then_unchanged_then_changed_then_304_and_errors():
    url = "https://support.example.com/policy"
    state = {}
    t = datetime(2026, 10, 10, tzinfo=timezone.utc)
    f = FakeFetcher([
        {"status": 200, "html": V1, "etag": '"a"', "last_modified": None},
        {"status": 200, "html": V1, "etag": '"a"', "last_modified": None},
        {"status": 200, "html": V2, "etag": '"b"', "last_modified": None},
        {"status": 304, "html": None, "etag": '"b"', "last_modified": None},
        {"status": 503, "html": None, "etag": '"b"', "last_modified": None},
    ])
    first = w.check(url, state, f, t)
    assert first["first_check"] and not first["changed"]
    assert not w.check(url, state, f, t)["changed"]
    changed = w.check(url, state, f, t)
    assert changed["changed"] and changed["diff"]["added"] == ["Inauthentic content is not eligible."]
    assert f.calls[2][1] == '"a"'  # conditional request used the stored ETag
    assert w.check(url, state, f, t)["status"] == 304
    err = w.check(url, state, f, t)
    assert err["error"] == "HTTP 503" and state[url]["last_error"] == "HTTP 503"
    assert state[url]["last_changed"] == "2026-10-10T00:00:00Z"


def test_http_fetcher_refuses_non_http():
    import pytest
    with pytest.raises(ValueError):
        w.http_fetcher("file:///etc/hosts", None, None)
