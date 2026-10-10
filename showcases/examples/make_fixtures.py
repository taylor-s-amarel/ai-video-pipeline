#!/usr/bin/env python3
"""Generate the dry-run example's synthetic inputs, private answers and PRE-MADE workspaces.

Everything here is fabricated, deterministically, to exercise the showcase
pipeline offline. The "agent outputs" under ``fixtures/`` were written by this
script, not by any agent or harness, and the usage numbers in
``.showcase/usage.json`` are invented. They are not results.

Two tasks:

* ``tiny_dedupe``: cluster duplicate contacts (data cleaning). Baseline fixtures
  use simpler matching rules than the Baltor-arm fixtures, so the example has a
  visible difference to analyse. Baseline trial 2 is deliberately contaminated
  (it holds a placed ``.baltor/`` folder) and is replaced by trial 6, baseline
  trial 3 crashed without output, and baseline trial 5 went over the tool-call
  budget.
* ``tiny_order_total``: a negative control (sum a CSV column product) where both
  arms are correct and the Baltor arm only spends more tokens.

Usage: python3 make_fixtures.py [--out DIR]   (default: this directory)
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import random
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED = 7

PEOPLE = [
    ("Ada Moreno", "ada.moreno@gmail.com", "2025550101", "Northwind"),
    ("Ben Okafor", "ben@okafor.example", "2025550102", "Okafor Labs"),
    ("Alex Kim", "alex.kim@contoso.example", "2025550103", "Contoso"),
    ("Alex Kim", "akim@fabrikam.example", "2025550104", "Fabrikam"),
    ("Chloe Martin", "chloe.martin@gmail.com", "2025550105", "Tailspin"),
    ("Dev Patel", "dev.patel@wingtip.example", "2025550106", "Wingtip"),
    ("Eva Lindqvist", "eva@lindqvist.example", "2025550107", "Lindqvist AB"),
    ("Farah Haddad", "farah.haddad@gmail.com", "2025550108", "Litware"),
    ("Gus Ferreira", "gus@ferreira.example", "2025550109", "Adatum"),
    ("Hana Sato", "hana.sato@proseware.example", "2025550110", "Proseware"),
    ("Ivan Petrov", "ivan.petrov@gmail.com", "2025550111", "Fourth Coffee"),
    ("Jo Nkosi", "jo@nkosi.example", "2025550112", "Nkosi Farms"),
    ("Kai Mueller", "kai.mueller@woodgrove.example", "2025550113", "Woodgrove"),
    ("Lena Rossi", "lena.rossi@gmail.com", "2025550114", "Margie's Travel"),
]


def fmt_phone(d: str, style: int) -> str:
    a, b, c = d[:3], d[3:6], d[6:]
    return [f"({a}) {b}-{c}", f"{a}.{b}.{c}", f"+1 {a} {b} {c}", f"1-{a}-{b}-{c}", f"{a}-{b}-{c}"][style]


def gmail_variant(email: str, k: int) -> str:
    local, domain = email.split("@")
    if domain != "gmail.com":
        return email
    plain = local.replace(".", "")
    return [plain, f"{local}+crm", local[:1] + "." + plain[1:]][k % 3] + "@gmail.com"


def contacts() -> tuple[list[dict], dict[str, str]]:
    rng = random.Random(SEED)
    rows, truth = [], {}
    for pi, (name, email, phone, company) in enumerate(PEOPLE, start=1):
        label = f"p{pi:02d}"
        n = [3, 2, 1, 1, 3, 2, 1, 3, 2, 1, 2, 1, 2, 3][pi - 1]
        for k in range(n):
            if k == 0:
                rec = (name, email, fmt_phone(phone, 4), company)
            elif k == 1:
                e = gmail_variant(email, pi) if email.endswith("@gmail.com") else "  " + email.upper() + " "
                rec = (name.upper() if pi % 2 else name, e, fmt_phone(phone, pi % 4), company)
            else:  # changed job: new email, same phone
                rec = (name, name.split()[0].lower() + "@newjob.example", fmt_phone(phone, 2), "New Job Ltd")
            rows.append({"name": rec[0], "email": rec[1], "phone": rec[2], "company": rec[3], "_label": label})
    rng.shuffle(rows)
    out = []
    for i, r in enumerate(rows, start=1):
        rid = f"r{i:03d}"
        truth[rid] = r.pop("_label")
        out.append({"id": rid, **r})
    return out, truth


DEDUPE_TEMPLATE = '''"""Cluster duplicate contacts.

Usage: python3 dedupe.py contacts.csv clusters.csv
"""

import csv
import re
import sys

KEYS = {keys!r}


def normalize_email(s):
    s = s.strip().lower(){gmail}
    return s


def normalize_phone(s):
    d = re.sub(r"\\D", "", s){strip1}
    return d


def keys_for(row):
    out = []
    if "email" in KEYS:
        out.append("e:" + normalize_email(row["email"]))
    if "phone" in KEYS:
        out.append("p:" + normalize_phone(row["phone"]))
    if "name" in KEYS:
        out.append("n:" + " ".join(row["name"].lower().split()))
    if "name_company" in KEYS:
        out.append("nc:" + " ".join(row["name"].lower().split()) + "|" + row["company"].strip().lower())
    return out


def cluster(rows):
    parent = {{r["id"]: r["id"] for r in rows}}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    first = {{}}
    for r in rows:
        for k in keys_for(r):
            if k in first:
                parent[find(r["id"])] = find(first[k])
            else:
                first[k] = r["id"]
    roots = {{}}
    return {{r["id"]: "c%03d" % roots.setdefault(find(r["id"]), len(roots) + 1) for r in rows}}


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, newline="") as fh:
        rows = list(csv.DictReader(fh))
    labels = cluster(rows)
    with open(dst, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id", "cluster"])
        for r in rows:
            w.writerow([r["id"], labels[r["id"]]])
'''
GMAIL = '''
    local, _, domain = s.partition("@")
    if domain in ("gmail.com", "googlemail.com"):
        s = local.split("+")[0].replace(".", "") + "@gmail.com"'''
STRIP1 = '''
    if len(d) == 11 and d.startswith("1"):
        d = d[1:]'''

NOTES_BASE = [
    "I grouped rows with the same email address, ignoring upper and lower case.",
    "Rows match when the email is the same after lower-casing, or when the names are the same.",
    "",
    "Matched on lower-cased email and on the phone digits. Rows sharing either one are merged.",
    "Same email (case-insensitive) means same person.",
    "Rows are merged when they share a lower-cased email or the same phone digits; I used union-find so chains "
    "of matches end up in one cluster.",
]
NOTES_TREAT = [
    "Two rows are the same person when their normalised phone numbers (digits only, leading US country code 1 "
    "removed) or normalised emails (trimmed, lower-cased, Gmail dots and +tags removed) match. Matches are merged "
    "with union-find, so chains end up together. Name alone is never enough: two different people are called "
    "Alex Kim.",
    "Blocking keys: phone digits without the +1 country code, and email lower-cased with Gmail dots and +tags "
    "removed. Any shared key links two rows; union-find merges the links. I did not match on names because the "
    "file has two different Alex Kims.",
    "Phone (digits, country code stripped), email (lower-case, Gmail dots and +suffix removed) and name plus "
    "company are blocking keys; rows sharing a key are linked and merged with union-find.",
    "I matched rows on lower-cased emails and on phone digits with the leading 1 removed, then merged linked "
    "rows. Gmail addresses written with and without dots were not unified.",
    "Same person = same normalised phone (digits only, no leading 1) or same normalised email (lower-case, Gmail "
    "dots and +tags dropped). Union-find merges chains. Names are ignored because two people share one name.",
]

# (keys, gmail, strip1, notes index, summary ok, tool_calls, crashed)
BASELINE = {
    1: (["email"], False, False, 0, True, 24, False),
    2: (["email", "phone"], True, True, 5, True, 22, False),  # contaminated: used the catalogue
    3: (["email"], False, False, 2, False, 31, True),  # crashed before writing outputs
    4: (["email", "phone"], False, False, 3, True, 27, False),
    5: (["email"], False, False, 4, True, 75, False),  # over the 60 tool-call budget
    6: (["email", "phone"], False, True, 5, True, 29, False),  # replacement for trial 2
}
TREATMENT = {
    1: (["email", "phone"], True, True, 0, True, 21, False),
    2: (["email", "phone"], True, True, 1, True, 19, False),
    3: (["email", "phone", "name_company"], True, True, 2, True, 26, False),
    4: (["email", "phone"], False, True, 3, True, 23, False),
    5: (["email", "phone"], True, True, 4, True, 20, False),
}


def run_dedupe(source: str, rows: list[dict]) -> dict[str, str]:
    ns: dict = {"__name__": "fixture_dedupe"}
    exec(compile(source, "dedupe.py", "exec"), ns)  # noqa: S102 - our own template
    return ns["cluster"](rows)


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    path.write_text(buf.getvalue(), encoding="utf-8")


def dedupe_task(out: Path) -> None:
    task = out / "tiny_dedupe"
    rows, truth = contacts()
    (task / "workspace").mkdir(parents=True, exist_ok=True)
    (task / "private" / "tests").mkdir(parents=True, exist_ok=True)
    write_csv(task / "workspace" / "contacts.csv", ["id", "name", "email", "phone", "company"],
              [[r["id"], r["name"], r["email"], r["phone"], r["company"]] for r in rows])
    write_csv(task / "private" / "clusters_truth.csv", ["id", "cluster"], [[k, v] for k, v in truth.items()])
    rng = random.Random(SEED + 1)
    for arm, table in (("baseline", BASELINE), ("baltor", TREATMENT)):
        notes = NOTES_BASE if arm == "baseline" else NOTES_TREAT
        for trial, (keys, gmail, strip1, ni, summary_ok, tool_calls, crashed) in table.items():
            ws = task / "fixtures" / arm / str(trial)
            if ws.exists():
                shutil.rmtree(ws)
            (ws / ".showcase").mkdir(parents=True)
            shutil.copy2(task / "workspace" / "contacts.csv", ws / "contacts.csv")
            src = DEDUPE_TEMPLATE.format(keys=keys, gmail=GMAIL if gmail else "", strip1=STRIP1 if strip1 else "")
            if crashed:
                (ws / "dedupe.py").write_text(src.split("def cluster")[0], encoding="utf-8")
            else:
                (ws / "dedupe.py").write_text(src, encoding="utf-8")
                labels = run_dedupe(src, rows)
                write_csv(ws / "clusters.csv", ["id", "cluster"], [[r["id"], labels[r["id"]]] for r in rows])
                summary = {"rows": len(rows), "clusters": len(set(labels.values())),
                           "method": "union-find over blocking keys: " + ", ".join(keys)}
                if not summary_ok:
                    summary.pop("method")
                (ws / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
                if notes[ni]:
                    (ws / "NOTES.md").write_text(notes[ni] + "\n", encoding="utf-8")
            wall = rng.randint(260, 520)
            t0 = dt.datetime(2026, 10, 10, 10 + trial, 5 if arm == "baseline" else 35, tzinfo=dt.timezone.utc)
            started, ended = (t.strftime("%Y-%m-%dT%H:%M:%SZ") for t in (t0, t0 + dt.timedelta(seconds=wall)))
            tin = rng.randint(80_000, 120_000) + (25_000 if arm == "baltor" else 0)
            meta = {"arm": arm, "trial": trial, "harness": "manual", "harness_version": "external (fixture)",
                    "model_reported": "example-model", "started_at": started,
                    "ended_at": ended,
                    "message": "FIXTURE written by make_fixtures.py" + ("; agent crashed" if crashed else "")}
            if crashed:
                meta["exit_status"] = "crashed"
            (ws / ".showcase" / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
            usage = {"wall_s": wall, "tool_calls": tool_calls, "tokens_in": tin, "tokens_out": rng.randint(5_000, 9_000)}
            (ws / ".showcase" / "usage.json").write_text(json.dumps(usage, indent=2) + "\n", encoding="utf-8")
            calls = []
            if arm == "baltor" or trial == 2:
                calls = [{"op": "search", "query": "deduplicate contacts by phone and email", "ok": True,
                          "results": ["example_fixture_dedupe_skill@1.0.0"]},
                         {"op": "read", "identity": "example_fixture_dedupe_skill", "version": "1.0.0",
                          "digest": "f1" * 32, "ok": True}]
                (ws / ".showcase" / "catalogue_calls.jsonl").write_text(
                    "".join(json.dumps(c) + "\n" for c in calls), encoding="utf-8")
            if arm == "baseline" and trial == 2:
                (ws / ".baltor").mkdir()
                (ws / ".baltor" / "step.lock.json").write_text(json.dumps(
                    {"spec": "baltor.step-lock/v1", "items": [{"identity": "example_fixture_dedupe_skill"}]}) + "\n",
                    encoding="utf-8")
    (task / "private" / "tests" / "test_dedupe_hidden.py").write_text('''from dedupe import normalize_email, normalize_phone


def test_phone_formats():
    assert normalize_phone("(202) 555-0101") == normalize_phone("202.555.0101") == "2025550101"


def test_phone_country_code():
    assert normalize_phone("+1 202 555 0101") == "2025550101"


def test_email_case_and_space():
    assert normalize_email("  Ada.Moreno@Example.COM ") == "ada.moreno@example.com"


def test_gmail_dots_and_tags():
    assert normalize_email("a.da.moreno@gmail.com") == normalize_email("adamoreno+crm@gmail.com")
''', encoding="utf-8")
    (task / "private" / "summary.schema.json").write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
        "required": ["rows", "clusters", "method"],
        "properties": {"rows": {"type": "integer", "minimum": 1}, "clusters": {"type": "integer", "minimum": 1},
                       "method": {"type": "string", "minLength": 10}}}, indent=2) + "\n", encoding="utf-8")


def order_task(out: Path) -> None:
    task = out / "tiny_order_total"
    rng = random.Random(SEED + 2)
    lines = [[f"o{i:03d}", rng.randint(1, 9), f"{rng.randint(50, 9999) / 100:.2f}"] for i in range(1, 31)]
    total = round(sum(q * float(p) for _, q, p in lines), 2)
    (task / "workspace").mkdir(parents=True, exist_ok=True)
    (task / "private").mkdir(parents=True, exist_ok=True)
    write_csv(task / "workspace" / "orders.csv", ["order_line", "quantity", "unit_price"], lines)
    (task / "private" / "expected_total.json").write_text(json.dumps({"total": total}) + "\n", encoding="utf-8")
    (task / "private" / "check_total.py").write_text('''"""Score total.json against the expected total. Prints one JSON line."""
import json
import sys
from pathlib import Path

ws, expected = Path(sys.argv[1]), json.loads(Path(sys.argv[2]).read_text())["total"]
try:
    got = float(json.loads((ws / "total.json").read_text())["total"])
except Exception as exc:  # noqa: BLE001
    print(json.dumps({"value": 0.0, "passed": False, "details": {"error": str(exc)}}))
    sys.exit(0)
ok = abs(got - expected) <= 0.005
print(json.dumps({"value": 1.0 if ok else 0.0, "passed": ok, "details": {"reported": got, "expected": expected}}))
''', encoding="utf-8")
    (task / "private" / "total.schema.json").write_text(json.dumps({
        "type": "object", "required": ["total"], "additionalProperties": False,
        "properties": {"total": {"type": "number"}}}) + "\n", encoding="utf-8")
    rng2 = random.Random(SEED + 3)
    for arm in ("baseline", "baltor"):
        for trial in (1, 2, 3):
            ws = task / "fixtures" / arm / str(trial)
            if ws.exists():
                shutil.rmtree(ws)
            (ws / ".showcase").mkdir(parents=True)
            shutil.copy2(task / "workspace" / "orders.csv", ws / "orders.csv")
            (ws / "total.json").write_text(json.dumps({"total": total}) + "\n", encoding="utf-8")
            started = f"2026-10-10T{15 + trial:02d}:{'10' if arm == 'baseline' else '40'}:00Z"
            ended = started.replace(":00Z", ":59Z")
            meta = {"arm": arm, "trial": trial, "harness": "manual", "harness_version": "external (fixture)",
                    "model_reported": "example-model", "started_at": started, "ended_at": ended,
                    "message": "FIXTURE written by make_fixtures.py"}
            (ws / ".showcase" / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
            extra = 9_000 if arm == "baltor" else 0
            usage = {"wall_s": rng2.randint(40, 70) + (15 if arm == "baltor" else 0),
                     "tool_calls": rng2.randint(4, 7) + (2 if arm == "baltor" else 0),
                     "tokens_in": rng2.randint(9_000, 12_000) + extra, "tokens_out": rng2.randint(600, 900)}
            (ws / ".showcase" / "usage.json").write_text(json.dumps(usage, indent=2) + "\n", encoding="utf-8")
            if arm == "baltor":
                (ws / ".showcase" / "catalogue_calls.jsonl").write_text(json.dumps(
                    {"op": "search", "query": "sum csv column product", "ok": True, "results": []}) + "\n",
                    encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=HERE)
    a = ap.parse_args(argv)
    dedupe_task(a.out)
    order_task(a.out)
    print(f"fixtures written under {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
