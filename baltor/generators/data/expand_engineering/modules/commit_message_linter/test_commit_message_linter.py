import commit_message_linter as cml


def msgs(findings):
    return " | ".join(f.message for f in findings)


def test_clean_message_passes():
    text = ("Add retry budget to the HTTP client\n\n"
            "Requests now stop retrying after 3 attempts or 10 seconds,\n"
            "whichever comes first.\n\n"
            "Co-authored-by: Ada Lovelace <ada@example.org>\n"
            "Signed-off-by: Grace Hopper <grace@example.org>")
    assert cml.lint(text) == []


def test_conventional_commit_lowercase_is_fine():
    assert cml.lint("fix(parser): handle empty input") == []


def test_long_subject_and_period():
    f = cml.lint("This subject line is intentionally far too long to be useful in git log output.")
    assert any(x.severity == "error" and "under 72" in x.message for x in f)
    assert any("period" in x.message for x in f)


def test_soft_limit_warning_only():
    f = cml.lint("Add a reasonably descriptive subject that is 60 chars")
    assert [x.severity for x in f] == ["warning"]


def test_missing_blank_line_and_non_imperative():
    f = cml.lint("Added caching\nBody without blank line")
    text = msgs(f)
    assert "blank line" in text and "imperative" in text


def test_body_wrap_ignores_urls_code_and_trailers():
    long_url = "https://example.org/" + "a" * 90
    text = ("Fix flaky upload test\n\n"
            f"{long_url}\n"
            "    indented code line that is very very very very very very very very very long\n\n"
            "Co-authored-by: Someone With A Very Long Name Indeed <someone.with.long.name@example.org>")
    assert cml.lint(text) == []
    f = cml.lint("Fix it\n\n" + "word " * 20)
    assert any("wrap" in x.message for x in f)


def test_trailer_without_email_is_error():
    f = cml.lint("Fix it\n\nSome context.\n\nSigned-off-by: Grace Hopper")
    assert any(x.severity == "error" and "Name <email>" in x.message for x in f)


def test_wip_and_empty():
    assert any("work-in-progress" in x.message for x in cml.lint("WIP stuff"))
    assert cml.lint("")[0].severity == "error"


def test_cli(tmp_path, capsys):
    p = tmp_path / "m"
    p.write_text("Add thing\n")
    assert cml.main([str(p)]) == 0
    p.write_text("Add a reasonably descriptive subject that is 60 chars\n")
    assert cml.main([str(p)]) == 0 and cml.main([str(p), "--strict"]) == 1
