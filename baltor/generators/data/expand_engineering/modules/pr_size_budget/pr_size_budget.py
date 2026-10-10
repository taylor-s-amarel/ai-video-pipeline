"""Measure a change against a pull-request size budget, ignoring lockfiles and generated files.

Small changes get better reviews. This reads ``git diff --numstat`` (or stdin),
drops files that reviewers do not read line by line (lockfiles, snapshots,
generated and vendored code, minified bundles), and reports reviewable lines,
file count, whether tests changed alongside source, and the top directories so a
large change can be split.

Usage::

    python pr_size_budget.py --base origin/main               # runs git diff --numstat origin/main...HEAD
    git diff --numstat --cached | python pr_size_budget.py -  # staged changes
    python pr_size_budget.py --base main --max-lines 400 --max-files 25 --json

Exit 1 when the reviewable change exceeds the budget.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field

DEFAULT_EXCLUDES = [
    "package-lock.json", "npm-shrinkwrap.json", "yarn.lock", "pnpm-lock.yaml", "bun.lock", "bun.lockb",
    "poetry.lock", "uv.lock", "Pipfile.lock", "pdm.lock", "Cargo.lock", "Gemfile.lock", "composer.lock",
    "go.sum", "*.min.js", "*.min.css", "*.map", "*.snap", "__snapshots__/*", "*_pb2.py", "*_pb2_grpc.py",
    "*.pb.go", "*.generated.*", "vendor/*", "third_party/*", "dist/*", "build/*", "*.svg",
]
TEST_RE = re.compile(r"(^|/)(tests?|__tests__|spec)/|(^|/)test_[^/]+\.py$|_test\.(py|go)$|\.(test|spec)\.[jt]sx?$")


@dataclass
class FileChange:
    path: str
    added: int
    deleted: int
    binary: bool = False
    excluded: bool = False


@dataclass
class Summary:
    reviewable_lines: int
    reviewable_files: int
    excluded_files: list[str]
    binary_files: list[str]
    tests_touched: bool
    source_touched: bool
    top_directories: list[tuple[str, int]]
    over_budget: bool
    messages: list[str] = field(default_factory=list)


def _new_path(path: str) -> str:
    # 'src/{old => new}/x.py' or 'old.py => new.py'
    m = re.match(r"^(.*)\{(.*) => (.*)\}(.*)$", path)
    if m:
        return (m.group(1) + m.group(3) + m.group(4)).replace("//", "/")
    if " => " in path:
        return path.split(" => ", 1)[1]
    return path


def parse_numstat(text: str, excludes: list[str] = DEFAULT_EXCLUDES) -> list[FileChange]:
    out = []
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        a, d, path = parts[0], parts[1], _new_path("\t".join(parts[2:]))
        binary = a == "-" and d == "-"
        fc = FileChange(path, 0 if binary else int(a), 0 if binary else int(d), binary)
        name = path.rsplit("/", 1)[-1]
        fc.excluded = any(fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(path, "*/" + pat)
                          for pat in excludes)
        out.append(fc)
    return out


def summarize(changes: list[FileChange], max_lines: int = 400, max_files: int = 30, warn_lines: int = 200) -> Summary:
    rev = [c for c in changes if not c.excluded and not c.binary]
    lines = sum(c.added + c.deleted for c in rev)
    dirs = Counter()
    for c in rev:
        top = c.path.split("/")[0] if "/" in c.path else "."
        dirs[top] += c.added + c.deleted
    tests = any(TEST_RE.search(c.path) for c in rev)
    source = any(not TEST_RE.search(c.path) and not c.path.endswith((".md", ".rst", ".txt")) for c in rev)
    over = lines > max_lines or len(rev) > max_files
    s = Summary(lines, len(rev), [c.path for c in changes if c.excluded], [c.path for c in changes if c.binary],
                tests, source, dirs.most_common(5), over)
    if over:
        s.messages.append(f"{lines} reviewable lines in {len(rev)} files exceeds the budget "
                          f"({max_lines} lines / {max_files} files). Consider splitting by: "
                          + ", ".join(f"{d} ({n})" for d, n in s.top_directories))
    elif lines > warn_lines:
        s.messages.append(f"{lines} reviewable lines: reviewable, but above the {warn_lines}-line comfort zone")
    if source and not tests:
        s.messages.append("source changed but no test files changed; say how this was tested")
    return s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Pull request size budget")
    ap.add_argument("input", nargs="?", help="'-' to read numstat from stdin")
    ap.add_argument("--base", default="origin/main")
    ap.add_argument("--max-lines", type=int, default=400)
    ap.add_argument("--max-files", type=int, default=30)
    ap.add_argument("--exclude", action="append", default=[], help="extra glob to exclude")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.input == "-":
        text = sys.stdin.read()
    else:
        text = subprocess.run(["git", "diff", "--numstat", "-M", f"{a.base}...HEAD"],
                              capture_output=True, text=True, check=True).stdout
    s = summarize(parse_numstat(text, DEFAULT_EXCLUDES + a.exclude), a.max_lines, a.max_files)
    if a.json:
        print(json.dumps(asdict(s), indent=2))
    else:
        print(f"reviewable: {s.reviewable_lines} lines in {s.reviewable_files} files "
              f"(excluded {len(s.excluded_files)}, binary {len(s.binary_files)})")
        for m in s.messages:
            print(f"- {m}")
    return 1 if s.over_budget else 0


if __name__ == "__main__":
    raise SystemExit(main())
