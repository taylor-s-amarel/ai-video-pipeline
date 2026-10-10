"""SemVer 2.0.0 parsing, precedence, bumping and npm-style range matching (standard library only).

Precedence follows https://semver.org/ section 11: numeric core, then pre-release
identifiers (numeric < alphanumeric, shorter set lower when equal so far); build
metadata is ignored. Range syntax follows the npm/node-semver grammar for the common
cases: comparators (<, <=, >, >=, =), caret (^), tilde (~), x-ranges (1.x, 1.2.*, *),
hyphen ranges (1.2.3 - 2.0.0), space-separated AND and ``||`` OR. As in node-semver,
a pre-release version only satisfies a range when some comparator in the matching
set names a pre-release with the same major.minor.patch.

CLI::

    python semver_tools.py compare 1.0.0-rc.1 1.0.0        # prints -1
    python semver_tools.py bump 1.4.2 minor                 # prints 1.5.0
    python semver_tools.py satisfies 1.4.2 "^1.2 || >=3"    # exit 0 if it does
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from functools import total_ordering

# Official regular expression from semver.org (named-group variant).
SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<build>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


@total_ordering
@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    pre: tuple = ()
    build: tuple = ()

    @classmethod
    def parse(cls, text: str) -> "Version":
        m = SEMVER_RE.match(text.strip().lstrip("v=").strip())
        if not m:
            raise ValueError(f"not a SemVer 2.0.0 version: {text!r}")
        pre = tuple(int(p) if p.isdigit() else p for p in m.group("pre").split(".")) if m.group("pre") else ()
        build = tuple(m.group("build").split(".")) if m.group("build") else ()
        return cls(int(m.group("major")), int(m.group("minor")), int(m.group("patch")), pre, build)

    def __str__(self) -> str:
        s = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre:
            s += "-" + ".".join(str(p) for p in self.pre)
        if self.build:
            s += "+" + ".".join(self.build)
        return s

    def _key(self):
        # A version without pre-release ranks above any pre-release of the same core.
        pre_key = (1,) if not self.pre else (0,) + tuple((0, p, "") if isinstance(p, int) else (1, 0, p) for p in self.pre)
        return (self.major, self.minor, self.patch, pre_key)

    def __eq__(self, other) -> bool:  # build metadata is ignored for precedence
        return isinstance(other, Version) and self._key() == other._key()

    def __hash__(self) -> int:
        return hash(self._key())

    def __lt__(self, other: "Version") -> bool:
        return self._key() < other._key()

    @property
    def core(self) -> tuple[int, int, int]:
        return (self.major, self.minor, self.patch)

    def bump(self, part: str, pre_id: str = "rc") -> "Version":
        """Bump 'major', 'minor', 'patch' or 'prerelease' (rc.0 -> rc.1, or 1.2.3 -> 1.2.4-rc.0)."""
        if part == "major":
            return Version(self.major + 1, 0, 0) if not (self.pre and self.minor == 0 and self.patch == 0) else Version(self.major, 0, 0)
        if part == "minor":
            return Version(self.major, self.minor + 1, 0) if not (self.pre and self.patch == 0) else Version(self.major, self.minor, 0)
        if part == "patch":
            return Version(self.major, self.minor, self.patch + 1) if not self.pre else Version(self.major, self.minor, self.patch)
        if part == "prerelease":
            if self.pre and isinstance(self.pre[-1], int):
                return Version(self.major, self.minor, self.patch, self.pre[:-1] + (self.pre[-1] + 1,))
            if self.pre:
                return Version(self.major, self.minor, self.patch, self.pre + (0,))
            return Version(self.major, self.minor, self.patch + 1, (pre_id, 0))
        raise ValueError(f"unknown part {part!r}")


def compare(a: str, b: str) -> int:
    va, vb = Version.parse(a), Version.parse(b)
    return (va > vb) - (va < vb)


def next_version(current: str, bump: str, pre_major_minor: bool = True) -> str:
    """Apply a bump name ('major'|'minor'|'patch'|'none'). With pre_major_minor, a breaking change on 0.x bumps minor."""
    v = Version.parse(current)
    if bump == "none":
        return str(v)
    if bump == "major" and v.major == 0 and pre_major_minor:
        bump = "minor"
    return str(v.bump(bump))


# ----------------------------------------------------------------------------- ranges

_PARTIAL = re.compile(r"^v?(?P<maj>\d+|[xX*])(?:\.(?P<min>\d+|[xX*]))?(?:\.(?P<pat>\d+|[xX*]))?(?:-(?P<pre>[0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")


def _is_x(p):
    return p is None or p in {"x", "X", "*"}


def _partial(text: str):
    m = _PARTIAL.match(text.strip())
    if not m:
        raise ValueError(f"bad version in range: {text!r}")
    return m.group("maj"), m.group("min"), m.group("pat"), m.group("pre")


def _v(maj, mi, pa, pre=None) -> Version:
    return Version.parse(f"{maj}.{mi}.{pa}" + (f"-{pre}" if pre else ""))


def _expand(token: str) -> list[tuple[str, Version]]:
    """Expand one range token into comparator pairs."""
    m = re.match(r"^(\^|~>?|>=|<=|>|<|=)?\s*(.*)$", token)
    op, ver = m.group(1) or "", m.group(2)
    if ver in {"", "*", "x", "X"}:
        return [(">=", _v(0, 0, 0))] if op in {"", "=", ">=", "^", "~"} else ([("<", _v(0, 0, 0, "0"))] if op in {"<", ">"} else [(">=", _v(0, 0, 0))])
    maj, mi, pa, pre = _partial(ver)
    if op == "^":
        M = int(maj) if not _is_x(maj) else 0
        if _is_x(maj):
            return [(">=", _v(0, 0, 0))]
        if _is_x(mi):
            return [(">=", _v(M, 0, 0)), ("<", _v(M + 1, 0, 0, "0"))]
        m_ = int(mi)
        if _is_x(pa):
            lo = _v(M, m_, 0)
            hi = _v(M + 1, 0, 0, "0") if M > 0 else _v(0, m_ + 1, 0, "0")
            return [(">=", lo), ("<", hi)]
        p_ = int(pa)
        lo = _v(M, m_, p_, pre)
        if M > 0:
            hi = _v(M + 1, 0, 0, "0")
        elif m_ > 0:
            hi = _v(0, m_ + 1, 0, "0")
        else:
            hi = _v(0, 0, p_ + 1, "0")
        return [(">=", lo), ("<", hi)]
    if op in {"~", "~>"}:
        if _is_x(maj):
            return [(">=", _v(0, 0, 0))]
        M = int(maj)
        if _is_x(mi):
            return [(">=", _v(M, 0, 0)), ("<", _v(M + 1, 0, 0, "0"))]
        m_ = int(mi)
        p_ = 0 if _is_x(pa) else int(pa)
        return [(">=", _v(M, m_, p_, None if _is_x(pa) else pre)), ("<", _v(M, m_ + 1, 0, "0"))]
    # plain comparator or bare (possibly partial) version
    if _is_x(maj):
        return [(">=", _v(0, 0, 0))]
    M = int(maj)
    if _is_x(mi) or _is_x(pa):
        lo = _v(M, 0 if _is_x(mi) else int(mi), 0)
        hi = _v(M + 1, 0, 0, "0") if _is_x(mi) else _v(M, int(mi) + 1, 0, "0")
        if op in {"", "="}:
            return [(">=", lo), ("<", hi)]
        if op == ">":
            return [(">=", hi)]
        if op == ">=":
            return [(">=", lo)]
        if op == "<":
            return [("<", _v(lo.major, lo.minor, 0, "0"))]
        if op == "<=":
            return [("<", hi)]
    return [(op or "=", _v(M, int(mi), int(pa), pre))]


def _split_set(text: str) -> list[str]:
    text = re.sub(r"\s+-\s+", " - ", text.strip())
    tokens = re.sub(r"(\^|~>?|>=|<=|>|<|=)\s+", r"\1", text).split()
    out, i = [], 0
    while i < len(tokens):
        if i + 2 < len(tokens) and tokens[i + 1] == "-":  # hyphen range
            out.append(("HYPHEN", tokens[i], tokens[i + 2]))
            i += 3
        else:
            out.append(tokens[i])
            i += 1
    return out


def _comparators(set_text: str) -> list[tuple[str, Version]]:
    comps: list[tuple[str, Version]] = []
    for tok in _split_set(set_text):
        if isinstance(tok, tuple):
            _, lo, hi = tok
            lmaj, lmi, lpa, lpre = _partial(lo)
            comps.append((">=", _v(0 if _is_x(lmaj) else lmaj, 0 if _is_x(lmi) else lmi, 0 if _is_x(lpa) else lpa, lpre)))
            hmaj, hmi, hpa, hpre = _partial(hi)
            if _is_x(hmaj):
                continue
            if _is_x(hmi):
                comps.append(("<", _v(int(hmaj) + 1, 0, 0, "0")))
            elif _is_x(hpa):
                comps.append(("<", _v(hmaj, int(hmi) + 1, 0, "0")))
            else:
                comps.append(("<=", _v(hmaj, hmi, hpa, hpre)))
        else:
            comps.extend(_expand(tok))
    return comps


def _test(op: str, v: Version, c: Version) -> bool:
    return {"=": v == c, ">": v > c, ">=": v >= c, "<": v < c, "<=": v <= c}[op]


def satisfies(version: str, range_text: str, include_prerelease: bool = False) -> bool:
    v = Version.parse(version)
    for set_text in range_text.split("||"):
        comps = _comparators(set_text or "*")
        if not all(_test(op, v, c) for op, c in comps):
            continue
        if v.pre and not include_prerelease:
            # node-semver rule: a pre-release only matches if a comparator in this set has a
            # pre-release on the same [major, minor, patch] tuple (ignoring our internal "-0" bounds).
            if not any(c.pre and c.pre != (0,) and c.core == v.core for _, c in comps):
                continue
        return True
    return False


def max_satisfying(versions: list[str], range_text: str) -> str | None:
    ok = [Version.parse(v) for v in versions if satisfies(v, range_text)]
    return str(max(ok)) if ok else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SemVer 2.0.0 helpers")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("compare"); c.add_argument("a"); c.add_argument("b")
    b = sub.add_parser("bump"); b.add_argument("version"); b.add_argument("part", choices=["major", "minor", "patch", "prerelease"])
    s = sub.add_parser("satisfies"); s.add_argument("version"); s.add_argument("range")
    v = sub.add_parser("valid"); v.add_argument("version")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "compare":
            print(compare(a.a, a.b))
        elif a.cmd == "bump":
            print(Version.parse(a.version).bump(a.part))
        elif a.cmd == "satisfies":
            return 0 if satisfies(a.version, a.range) else 1
        elif a.cmd == "valid":
            Version.parse(a.version)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
