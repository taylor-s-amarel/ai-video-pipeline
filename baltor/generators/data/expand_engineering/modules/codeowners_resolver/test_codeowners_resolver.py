import json

import pytest

import codeowners_resolver as co

SAMPLE = r"""
# Default owners
*       @org/core
*.js    @js-owner
/build/logs/ @doctocat
docs/*  docs@example.com
apps/   @octocat
/docs/  @doctocat
/scripts/ @doctocat @octocat
**/logs @octocat
/apps/github
\#file_with_pound.rb @octocat
"""


@pytest.fixture
def rules():
    r, problems = co.parse(SAMPLE)
    assert problems == []
    return r


@pytest.mark.parametrize("path,owners", [
    ("README.md", ["@org/core"]),
    ("src/app.js", ["@js-owner"]),
    ("build/logs/today.txt", ["@octocat"]),          # later '**/logs' wins over '/build/logs/'
    ("docs/getting-started.md", ["@doctocat"]),      # '/docs/' is later than 'docs/*'
    ("docs/build-app/troubleshooting.md", ["@doctocat"]),
    ("deep/apps/x.py", ["@octocat"]),                # 'apps/' matches anywhere
    ("apps/github/main.py", []),                     # explicitly unowned
    ("scripts/deploy.sh", ["@doctocat", "@octocat"]),
    ("#file_with_pound.rb", ["@octocat"]),
])
def test_last_match_wins(rules, path, owners):
    assert co.owners_for(path, rules)[0] == owners


def test_star_does_not_cross_directories():
    r, _ = co.parse("docs/*  @a\n")
    assert co.owners_for("docs/x.md", r)[0] == ["@a"]
    assert co.owners_for("docs/sub/x.md", r)[0] == []


def test_lint_problems():
    _, problems = co.parse("!secret.txt @a\nsrc/[ab].py @a\nlib/ notanowner\n")
    text = " ".join(problems)
    assert "negation" in text and "ranges" in text and "notanowner" in text


def test_review_plan(rules):
    plan = co.review_plan(["src/app.js", "apps/github/x", "README.md"], rules)
    assert plan["owners"]["@js-owner"] == ["src/app.js"] and plan["unowned"] == ["apps/github/x"]


def test_cli(tmp_path, capsys):
    f = tmp_path / "CODEOWNERS"
    f.write_text("* @org/core\n")
    assert co.main(["--codeowners", str(f), "a.py"]) == 0
    assert json.loads(capsys.readouterr().out)["owners"]["@org/core"] == ["a.py"]
    assert co.main(["--codeowners", str(f), "--lint"]) == 0
