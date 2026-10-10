#!/usr/bin/env python3
"""Lint a Dockerfile for hardening problems (root user, unpinned bases, curl|sh, secrets in ENV/ARG, ...).

Usage::

    python dockerfile_hardening_lint.py Dockerfile [more Dockerfiles] [--fail-on high] [--json]

Exit 1 when any finding reaches ``--fail-on`` (default ``high``). Standard library only. This is a
focused subset of what hadolint/Trivy config scanning check; run those too when available.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import asdict, dataclass

SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3}
SECRET_NAME = re.compile(r"(PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|CREDENTIAL)", re.I)
PIPE_TO_SHELL = re.compile(r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(ba|z|da)?sh\b")
FULL_SDK_BASE = re.compile(r"^(golang|rust|node|python|openjdk|maven|gradle|eclipse-temurin)(:[^-]*)?$")


@dataclass
class Finding:
    rule: str
    severity: str
    line: int
    message: str
    file: str = ""


@dataclass
class Instruction:
    line: int
    keyword: str
    args: str


def parse(text: str) -> list[Instruction]:
    """Split a Dockerfile into instructions, joining continuations and skipping heredoc bodies."""
    out: list[Instruction] = []
    lines = text.splitlines()
    escape = "\\"
    i = 0
    if lines and re.match(r"#\s*escape\s*=\s*`", lines[0]):
        escape = "`"
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        start = i + 1
        buf = stripped
        while buf.endswith(escape) and i + 1 < len(lines):
            i += 1
            nxt = lines[i].strip()
            if nxt.startswith("#"):
                continue
            buf = buf[:-1].rstrip() + " " + nxt
        m = re.match(r"(\w+)\s*(.*)", buf)
        if m:
            kw, args = m.group(1).upper(), m.group(2)
            heredoc = re.search(r"<<-?\s*['\"]?(\w+)['\"]?", args)
            if heredoc and kw in {"RUN", "COPY"}:
                term = heredoc.group(1)
                body = []
                while i + 1 < len(lines) and lines[i + 1].strip() != term:
                    i += 1
                    body.append(lines[i])
                i += 1
                args = args + "\n" + "\n".join(body)
            out.append(Instruction(start, kw, args))
        i += 1
    return out


def _assignments(args: str) -> list[tuple[str, str]]:
    """Return (name, value) pairs for ENV/ARG in both `K=v K2=v2` and legacy `K value` forms."""
    try:
        tokens = shlex.split(args, posix=True)
    except ValueError:
        tokens = args.split()
    if not tokens:
        return []
    if "=" not in tokens[0]:
        return [(tokens[0], " ".join(tokens[1:]))]
    out = []
    for t in tokens:
        name, _, value = t.partition("=")
        out.append((name, value))
    return out


def lint(text: str, filename: str = "Dockerfile") -> list[Finding]:
    ins = parse(text)
    f: list[Finding] = []
    stages: list[str] = []
    stage_start_idx: list[int] = []
    for idx, x in enumerate(ins):
        if x.keyword == "FROM":
            stage_start_idx.append(idx)
            parts = [p for p in x.args.split() if not p.startswith("--")]
            image = parts[0] if parts else ""
            alias = parts[2].lower() if len(parts) >= 3 and parts[1].lower() == "as" else ""
            ref_stage = image.lower() in stages
            if alias:
                stages.append(alias)
            if image.lower() == "scratch" or ref_stage or image.startswith("$"):
                continue
            name_tag = image.split("@")[0]
            last = name_tag.rsplit("/", 1)[-1]
            if "@sha256:" not in image:
                if ":" not in last or last.endswith(":latest"):
                    f.append(Finding("DF001", "medium", x.line, f"base image '{image}' is unpinned or uses :latest; pin a version tag and digest"))
                else:
                    f.append(Finding("DF002", "low", x.line, f"base image '{image}' is not pinned by digest (@sha256:...); tags can move"))
    final_stage = ins[stage_start_idx[-1]:] if stage_start_idx else ins
    users = [x for x in final_stage if x.keyword == "USER"]
    if not users:
        f.append(Finding("DF003", "high", final_stage[0].line if final_stage else 1,
                         "final stage has no USER instruction; the container runs as root"))
    elif users[-1].args.split(":")[0].strip() in {"root", "0"}:
        f.append(Finding("DF003", "high", users[-1].line, "final stage switches to root"))
    final_from = final_stage[0].args.split()[0] if final_stage and final_stage[0].keyword == "FROM" else ""
    if len(stage_start_idx) == 1 and FULL_SDK_BASE.match(final_from.split("@")[0].rsplit("/", 1)[-1]):
        f.append(Finding("DF014", "low", final_stage[0].line,
                         f"single-stage build on SDK image '{final_from}'; use a multi-stage build with a slim or distroless runtime"))
    seen_copy_all = False
    for x in ins:
        a = x.args
        if x.keyword == "FROM":
            seen_copy_all = False
        if x.keyword == "ADD":
            if re.search(r"\bhttps?://", a):
                f.append(Finding("DF004", "medium", x.line, "ADD from a URL skips checksum verification; download with a pinned checksum instead"))
            elif not re.search(r"\.(tar|tgz|tar\.gz|tar\.bz2|tar\.xz|zip)\b", a) and "--checksum" not in a and "git@" not in a:
                f.append(Finding("DF004", "low", x.line, "use COPY instead of ADD for local files"))
        if x.keyword == "RUN":
            if PIPE_TO_SHELL.search(a):
                f.append(Finding("DF005", "high", x.line, "remote script piped to a shell; download, verify checksum/signature, then run"))
            if re.search(r"\bapt-get\s+(-\S+\s+)*install\b", a):
                if "--no-install-recommends" not in a:
                    f.append(Finding("DF006", "low", x.line, "apt-get install without --no-install-recommends"))
                if "/var/lib/apt/lists" not in a:
                    f.append(Finding("DF006", "low", x.line, "apt lists not removed in the same RUN (rm -rf /var/lib/apt/lists/*)"))
            if re.search(r"\bapt-get\s+update\b", a) and not re.search(r"\bapt-get\s+(-\S+\s+)*install\b", a):
                f.append(Finding("DF006", "medium", x.line, "apt-get update in its own RUN layer goes stale; combine with install"))
            if re.search(r"\bsudo\b", a):
                f.append(Finding("DF010", "medium", x.line, "sudo in a build step; run as root during build and drop privileges with USER"))
            if re.search(r"\bpip3?\s+install\b", a) and "--no-cache-dir" not in a and "--mount=type=cache" not in a:
                f.append(Finding("DF011", "low", x.line, "pip install without --no-cache-dir (or a cache mount) bloats the layer"))
            if re.search(r"\bnpm\s+install\b", a) and not re.search(r"\bnpm\s+install\s+-g\b", a):
                f.append(Finding("DF011", "low", x.line, "use npm ci for reproducible installs from the lockfile"))
            if re.search(r"\bchmod\s+(-R\s+)?0?777\b", a):
                f.append(Finding("DF013", "medium", x.line, "chmod 777 makes files world-writable"))
            if re.search(r"(PASSWORD|SECRET|TOKEN)=\S+", a) and "--mount=type=secret" not in a:
                f.append(Finding("DF007", "high", x.line, "credential-looking assignment in RUN; use RUN --mount=type=secret"))
        if x.keyword in {"ENV", "ARG"}:
            for name, value in _assignments(a):
                if SECRET_NAME.search(name):
                    sev = "high" if value and value.strip("'\"") else "medium"
                    f.append(Finding("DF007", sev, x.line,
                                     f"{x.keyword} {name} looks like a secret; build args and env persist in image history. Use --mount=type=secret"))
        if x.keyword == "EXPOSE" and re.search(r"\b22(/tcp)?\b", a):
            f.append(Finding("DF012", "medium", x.line, "EXPOSE 22: do not run SSH in application containers"))
        if x.keyword == "COPY" and re.match(r"^(--\S+\s+)*\.\s+\.?/?\S*$", a.strip()):
            seen_copy_all = True
        if x.keyword == "RUN" and seen_copy_all and re.search(r"\b(npm ci|npm install|pip3? install|poetry install|uv sync|go mod download|bundle install|cargo fetch)\b", a):
            f.append(Finding("DF008", "low", x.line, "dependency install runs after `COPY . .`; copy lockfiles first so the layer caches"))
            seen_copy_all = False
        if x.keyword == "WORKDIR" and not a.strip().startswith(("/", "$")):
            f.append(Finding("DF015", "low", x.line, "WORKDIR should be an absolute path"))
        if x.keyword in {"CMD", "ENTRYPOINT"} and not a.strip().startswith("["):
            f.append(Finding("DF016", "low", x.line, f"{x.keyword} in shell form: PID 1 is /bin/sh and SIGTERM may not reach the app; use exec (JSON) form"))
    if not any(x.keyword == "HEALTHCHECK" for x in final_stage):
        f.append(Finding("DF009", "info", 1, "no HEALTHCHECK (fine on Kubernetes, which uses probes; useful for plain Docker/Compose)"))
    for item in f:
        item.file = filename
    return sorted(f, key=lambda z: (-SEVERITY[z.severity], z.line))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+")
    ap.add_argument("--fail-on", choices=list(SEVERITY), default="high")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    allf: list[Finding] = []
    for path in a.files:
        with open(path, encoding="utf-8") as fh:
            allf += lint(fh.read(), path)
    if a.json:
        print(json.dumps([asdict(x) for x in allf], indent=2))
    else:
        for x in allf:
            print(f"{x.file}:{x.line}: {x.severity.upper():6} {x.rule} {x.message}")
        print(f"{len(allf)} finding(s)")
    return 1 if any(SEVERITY[x.severity] >= SEVERITY[a.fail_on] for x in allf) else 0


if __name__ == "__main__":
    sys.exit(main())
