import gha_workflow_security_lint as m

SHA = "0123456789abcdef0123456789abcdef01234567"

GOOD = f"""
name: ci
on:
  pull_request:
  push:
    branches: [main]
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@{SHA} # v6
        with:
          persist-credentials: false
      - run: make test
"""


def rules(text):
    return {(f.rule, f.severity) for f in m.lint_text(text)}


def test_good_workflow_is_clean():
    assert m.lint_text(GOOD) == []


def test_on_key_parsed_as_bool_is_handled():
    assert m._triggers(m._load("on: [push, pull_request]\njobs: {}\n")) == {"push", "pull_request"}


def test_tag_pinned_action_and_missing_permissions():
    text = "on: push\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/setup-node@v6\n"
    r = rules(text)
    assert ("GA001", "medium") in r and ("GA002", "medium") in r and ("GA006", "low") in r


def test_script_injection_detected():
    text = GOOD.replace("- run: make test", '- run: echo "${{ github.event.pull_request.title }}"')
    assert ("GA005", "high") in rules(text)


def test_env_indirection_is_not_injection():
    text = GOOD.replace("- run: make test", '- run: echo "$TITLE"\n        env:\n          TITLE: ${{ github.event.pull_request.title }}')
    assert not any(r[0] == "GA005" for r in rules(text))


def test_pull_request_target_checkout_of_head():
    text = f"""
on: pull_request_target
permissions: {{contents: read}}
jobs:
  build:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@{SHA}
        with:
          ref: ${{{{ github.event.pull_request.head.sha }}}}
          persist-credentials: false
"""
    assert ("GA004", "high") in rules(text)


def test_write_all_and_secrets_inherit_and_reusable_pin():
    text = """
on: push
permissions: write-all
jobs:
  call:
    uses: org/repo/.github/workflows/deploy.yml@main
    secrets: inherit
"""
    r = rules(text)
    assert ("GA003", "high") in r and ("GA007", "low") in r and ("GA001", "medium") in r


def test_self_hosted_on_pr_and_docker_digest():
    text = f"""
on: pull_request
permissions: {{contents: read}}
jobs:
  a:
    runs-on: [self-hosted, linux]
    timeout-minutes: 5
    steps:
      - uses: docker://alpine:3.20
      - uses: docker://alpine@sha256:{'a'*64}
"""
    r = [f for f in m.lint_text(text)]
    assert any(f.rule == "GA008" for f in r)
    assert sum(f.rule == "GA001" for f in r) == 1


def test_cli(tmp_path):
    p = tmp_path / "ci.yml"
    p.write_text(GOOD)
    assert m.main([str(p)]) == 0
    p.write_text(GOOD.replace("- run: make test", "- run: echo ${{ github.head_ref }}"))
    assert m.main([str(p), "--json"]) == 1
