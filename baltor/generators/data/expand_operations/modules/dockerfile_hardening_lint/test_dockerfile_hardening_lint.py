import dockerfile_hardening_lint as m

GOOD = """# syntax=docker/dockerfile:1
FROM python:3.13-slim@sha256:%s AS build
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache pip install uv && uv sync --frozen --no-dev
COPY src ./src

FROM gcr.io/distroless/python3-debian12:nonroot@sha256:%s
WORKDIR /app
COPY --from=build /app /app
USER nonroot
ENTRYPOINT ["python3", "-m", "app"]
""" % ("a" * 64, "b" * 64)


def rules(text):
    return {f.rule for f in m.lint(text)}


def test_hardened_multistage_has_no_high_or_medium():
    findings = m.lint(GOOD)
    assert all(f.severity in {"info", "low"} for f in findings), findings


def test_root_and_latest_flagged():
    r = m.lint("FROM ubuntu:latest\nRUN echo hi\nCMD [\"bash\"]\n")
    assert {"DF001", "DF003"} <= {f.rule for f in r}
    assert any(f.rule == "DF003" and f.severity == "high" for f in r)


def test_explicit_root_user_flagged():
    assert "DF003" in rules("FROM alpine:3.20\nUSER app\nUSER root\n")


def test_curl_pipe_shell_is_high():
    r = m.lint("FROM alpine:3.20\nRUN curl -fsSL https://example.com/install.sh | sh\nUSER 10001\n")
    assert any(f.rule == "DF005" and f.severity == "high" for f in r)


def test_secret_env_and_arg():
    r = m.lint("FROM alpine:3.20\nARG NPM_TOKEN\nENV DB_PASSWORD=hunter2\nUSER 1000\n")
    sev = {(f.rule, f.severity) for f in r}
    assert ("DF007", "high") in sev and ("DF007", "medium") in sev


def test_apt_rules_and_continuations():
    text = "FROM debian:12\nRUN apt-get update && \\\n    apt-get install -y curl\nUSER 1000\n"
    r = [f for f in m.lint(text) if f.rule == "DF006"]
    msgs = " ".join(f.message for f in r)
    assert "--no-install-recommends" in msgs and "apt lists" in msgs
    assert r[0].line == 2


def test_apt_update_alone():
    assert any(f.severity == "medium" for f in m.lint("FROM debian:12\nRUN apt-get update\nUSER 1\n") if f.rule == "DF006")


def test_add_url_and_copy_order():
    text = "FROM node:22\nADD https://x.example/a.tgz /tmp/\nWORKDIR /app\nCOPY . .\nRUN npm ci\nUSER node\nCMD node server.js\n"
    r = rules(text)
    assert {"DF004", "DF008", "DF016", "DF014"} <= r


def test_stage_reference_not_treated_as_image():
    text = "FROM golang:1.25 AS build\nRUN go build -o /out/app .\nFROM build AS test\nRUN go test ./...\nFROM gcr.io/distroless/static-debian12:nonroot\nCOPY --from=build /out/app /app\nUSER nonroot\nENTRYPOINT [\"/app\"]\n"
    r = m.lint(text)
    assert not any(f.rule == "DF001" and "build" == f.message.split("'")[1] for f in r)
    assert not any(f.rule == "DF014" for f in r)


def test_heredoc_body_is_skipped():
    text = "FROM alpine:3.20\nRUN <<EOF\nFROM fake\nUSER root\nEOF\nUSER 1000\n"
    assert "DF003" not in rules(text)


def test_cli(tmp_path, capsys):
    p = tmp_path / "Dockerfile"
    p.write_text("FROM ubuntu\n")
    assert m.main([str(p)]) == 1
    p.write_text(GOOD)
    assert m.main([str(p), "--json"]) == 0
