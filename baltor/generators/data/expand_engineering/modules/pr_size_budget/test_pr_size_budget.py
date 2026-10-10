import json

import pr_size_budget as ps

NUMSTAT = "\n".join([
    "120\t30\tsrc/app/service.py",
    "40\t2\ttests/test_service.py",
    "900\t850\tpackage-lock.json",
    "-\t-\tdocs/diagram.png",
    "10\t0\tsrc/{old => new}/util.py",
    "3\t3\tweb/__snapshots__/App.test.js.snap",
    "5\t1\tREADME.md",
])


def test_parse_and_exclusions():
    ch = ps.parse_numstat(NUMSTAT)
    by = {c.path: c for c in ch}
    assert by["package-lock.json"].excluded
    assert by["web/__snapshots__/App.test.js.snap"].excluded
    assert by["docs/diagram.png"].binary
    assert "src/new/util.py" in by


def test_summary_within_budget():
    s = ps.summarize(ps.parse_numstat(NUMSTAT))
    assert s.reviewable_lines == 120 + 30 + 40 + 2 + 10 + 5 + 1
    assert s.tests_touched and s.source_touched and not s.over_budget
    assert s.top_directories[0][0] == "src"


def test_over_budget_message():
    big = "\n".join(f"50\t0\tpkg{i}/mod.py" for i in range(12))
    s = ps.summarize(ps.parse_numstat(big), max_lines=400)
    assert s.over_budget and "splitting" in s.messages[0]
    assert any("no test files" in m for m in s.messages)


def test_rename_arrow_form():
    assert ps._new_path("a.py => b.py") == "b.py"
    assert ps._new_path("src/{a => b}/c.py") == "src/b/c.py"


def test_cli_stdin(monkeypatch, capsys):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO(NUMSTAT))
    assert ps.main(["-", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["reviewable_files"] == 5
