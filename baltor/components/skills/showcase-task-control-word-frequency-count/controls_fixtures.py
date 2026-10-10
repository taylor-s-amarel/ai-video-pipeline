"""Fixture makers and reference answers for the negative-control tasks.

Each maker writes the agent's inputs into the workspace and the expected output
into the hidden directory. Everything is generated from the fixture seed.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import showcase_eval as se


# --------------------------------------------------------------------------- fizzbuzz variant

def fizzbuzz_expected(n: int, rules: list[list]) -> list[str]:
    out = []
    for i in range(1, n + 1):
        word = "".join(w for d, w in rules if i % d == 0)
        out.append(word or str(i))
    return out


def make_fizzbuzz(params: dict, ws: Path, hd: Path, seed: int) -> None:
    rng = random.Random(seed)
    n = rng.randint(params["n_min"], params["n_max"])
    rules = params["rules"]
    se.write_json(ws / "input.json", {"n": n, "rules": rules})
    (hd / "expected.txt").write_text("\n".join(fizzbuzz_expected(n, rules)) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- arithmetic word problems

PROBLEMS = [
    ("A box holds {a} pencils. Maria buys {b} boxes and gives away {c} pencils. How many pencils does she have left?",
     lambda a, b, c: a * b - c),
    ("A train travels {a} km in each of {b} hours, then {c} km more. How many kilometres does it travel in total?",
     lambda a, b, c: a * b + c),
    ("A baker makes {a} loaves a day for {b} days and sells all but {c} of them. How many loaves are sold?",
     lambda a, b, c: a * b - c),
    ("Tom has {a} marbles. He wins {b} more, then splits the total equally among {c} friends and himself; how many does each person get, ignoring any remainder?",
     lambda a, b, c: (a + b) // (c + 1)),
    ("A farm has {a} rows of {b} apple trees. Storms knock down {c} trees. How many trees remain?",
     lambda a, b, c: a * b - c),
    ("A cinema has {a} seats. {b} tickets are sold for the first show and {c} for the second. How many seats were empty across both shows?",
     lambda a, b, c: 2 * a - b - c),
    ("A runner does {a} laps of {b} metres and then a {c} metre cool-down. How many metres did she run?",
     lambda a, b, c: a * b + c),
    ("A shop orders {a} crates with {b} bottles each; {c} bottles arrive broken. How many good bottles arrive?",
     lambda a, b, c: a * b - c),
    ("Sam saves {a} dollars a week for {b} weeks and spends {c} dollars. How many dollars are left?",
     lambda a, b, c: a * b - c),
    ("A library had {a} books, bought {b} boxes of {c} books each, and gave away 10. How many books does it have now?",
     lambda a, b, c: a + b * c - 10),
]


def make_arithmetic(params: dict, ws: Path, hd: Path, seed: int) -> None:
    rng = random.Random(seed)
    problems, answers = [], {}
    for i, (text, fn) in enumerate(PROBLEMS, start=1):
        if i == 6:  # cinema: both shows sell at most the number of seats
            a = rng.randint(50, 200)
            b, c = rng.randint(1, a), rng.randint(1, a)
        else:
            a, b = rng.randint(12, 90), rng.randint(3, 12)
            c = rng.randint(2, min(a * b - 1, 60))
        problems.append({"id": str(i), "question": text.format(a=a, b=b, c=c)})
        answers[str(i)] = fn(a, b, c)
    se.write_json(ws / "problems.json", problems)
    se.write_json(hd / "expected.json", answers)


# --------------------------------------------------------------------------- README typo fix

README_LINES = [
    "# Harbour Tide Tables",
    "",
    "Harbour Tide Tables prints the next high and low tides for a small harbour.",
    "It reads a local file of predicted water levels and never needs the network.",
    "",
    "## Installation",
    "",
    "Clone the repository and install the package in a virtual environment.",
    "The only requirement is Python 3.10 or newer.",
    "",
    "## Usage",
    "",
    "Run the command with the path to a levels file and the harbour name.",
    "The output lists each tide with its time and height in metres.",
    "Add the summary flag to print one line per day instead of every tide.",
    "",
    "## Configuration",
    "",
    "Settings are read from a configuration file in your home directory.",
    "You can override the time zone and the number of days to show.",
    "",
    "## Contributing",
    "",
    "Please open an issue before sending a large change so we can discuss it.",
    "Every pull request needs a short description and passing tests.",
]

TYPO_CANDIDATES = [  # (line index, correct word, typo)
    (2, "prints", "prnits"), (3, "network", "netwrok"), (7, "repository", "repositroy"),
    (8, "requirement", "requirment"), (12, "command", "comand"), (13, "height", "heigth"),
    (14, "summary", "sumary"), (18, "configuration", "configuraton"), (19, "override", "overide"),
    (23, "discuss", "dicsuss"), (24, "description", "descripton"), (24, "passing", "pasing"),
]


def make_typo_fix(params: dict, ws: Path, hd: Path, seed: int) -> None:
    rng = random.Random(seed)
    chosen = sorted(rng.sample(range(len(TYPO_CANDIDATES)), params["typos"]))
    lines = list(README_LINES)
    planted = []
    for idx in chosen:
        line, good, bad = TYPO_CANDIDATES[idx]
        assert good in lines[line], (line, good)
        lines[line] = lines[line].replace(good, bad, 1)
        planted.append({"line": line + 1, "correct": good, "typo": bad})
    (ws / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (hd / "expected.md").write_text("\n".join(README_LINES) + "\n", encoding="utf-8")
    se.write_json(hd / "typos.json", planted)


# --------------------------------------------------------------------------- CSV two-key sort

FIRST = ["Ana", "Ben", "Chen", "Dara", "Eli", "Fay", "Gus", "Hana", "Ivan", "Jo", "Kai", "Lena", "Mo", "Nia", "Omar", "Pia"]
LAST = ["Abbott", "Baker", "Chowdhury", "diaz", "Evans", "Fischer", "Garcia", "Huang", "Ito", "Jones", "Khan", "Lopez"]
CITIES = ["Altoona", "Bedford", "Erie", "Lancaster", "Scranton", "York"]


def sort_people(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=lambda r: (r["last_name"].lower(), -int(r["age"]), r["first_name"].lower()))


def make_csv_sort(params: dict, ws: Path, hd: Path, seed: int) -> None:
    rng = random.Random(seed)
    rows = [{"first_name": rng.choice(FIRST), "last_name": rng.choice(LAST), "age": str(rng.randint(18, 80)),
             "city": rng.choice(CITIES)} for _ in range(params["rows"])]
    se.write_csv(ws / "people.csv", rows)
    se.write_csv(hd / "expected.csv", sort_people(rows))


# --------------------------------------------------------------------------- unit conversion

CONVERSIONS = {
    ("km", "mi"): lambda v: v / 1.609344, ("mi", "km"): lambda v: v * 1.609344,
    ("kg", "lb"): lambda v: v / 0.45359237, ("lb", "kg"): lambda v: v * 0.45359237,
    ("C", "F"): lambda v: v * 9 / 5 + 32, ("F", "C"): lambda v: (v - 32) * 5 / 9,
    ("L", "gal"): lambda v: v / 3.785411784, ("gal", "L"): lambda v: v * 3.785411784,
    ("m", "ft"): lambda v: v / 0.3048, ("ft", "m"): lambda v: v * 0.3048,
}


def make_unit_conversion(params: dict, ws: Path, hd: Path, seed: int) -> None:
    rng = random.Random(seed)
    pairs = list(CONVERSIONS)
    rows, expected = [], []
    for i in range(params["rows"]):
        frm, to = pairs[i % len(pairs)] if i < len(pairs) else rng.choice(pairs)
        value = round(rng.uniform(-40 if frm in ("C", "F") else 0.5, 250), 1)
        rows.append({"row": str(i + 1), "value": f"{value}", "from_unit": frm, "to_unit": to, "result": ""})
        expected.append(round(CONVERSIONS[(frm, to)](value), 2))
    se.write_csv(ws / "conversions.csv", rows)
    se.write_json(hd / "expected.json", expected)


# --------------------------------------------------------------------------- rename refactor

def shop_files(old: str) -> dict[str, str]:
    return {
        "shop/__init__.py": f'"""A tiny shop package."""\n\nfrom .pricing import {old}\n\n__all__ = ["{old}"]\n',
        "shop/pricing.py": f'''"""Order pricing."""


def {old}(items, tax_rate=0.0):
    """Sum quantity x unit price for each item and add tax, rounded to cents."""
    subtotal = sum(qty * price for qty, price in items)
    return round(subtotal * (1 + tax_rate), 2)
''',
        "shop/cart.py": f'''"""Shopping cart."""

from .pricing import {old}


class Cart:
    def __init__(self):
        self.items = []

    def add(self, qty, price):
        self.items.append((qty, price))

    def total(self, tax_rate=0.0):
        return {old}(self.items, tax_rate)
''',
        "shop/invoice.py": f'''"""Invoice text."""

from . import pricing


def invoice_line(items, tax_rate):
    return f"TOTAL {{pricing.{old}(items, tax_rate):.2f}}"
''',
        "shop/cli.py": f'''"""Command line: python -m shop.cli 2x3.50 1x10"""

import sys

from .pricing import {old}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    items = [(int(q), float(p)) for q, p in (a.split("x") for a in argv)]
    print({old}(items))
    return 0
''',
        "tests/test_shop.py": f'''from shop import {old}
from shop.cart import Cart
from shop.invoice import invoice_line


def test_total():
    assert {old}([(2, 3.5), (1, 10.0)]) == 17.0


def test_cart_tax():
    c = Cart()
    c.add(1, 100.0)
    assert c.total(0.06) == 106.0


def test_invoice():
    assert invoice_line([(1, 5.0)], 0.0) == "TOTAL 5.00"
''',
    }


def make_rename(params: dict, ws: Path, hd: Path, seed: int) -> None:
    for rel, text in shop_files(params["old_name"]).items():
        p = ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    rng = random.Random(seed)
    cases = [[[rng.randint(1, 5), round(rng.uniform(0.5, 50), 2)] for _ in range(rng.randint(1, 4))] for _ in range(6)]
    se.write_json(hd / "expected.json", {"cases": cases, "tax": 0.08})


# --------------------------------------------------------------------------- YAML to JSON

def make_yaml_to_json(params: dict, ws: Path, hd: Path, seed: int) -> None:
    import yaml  # PyYAML is used only by setup and evaluator, never required of the agent
    rng = random.Random(seed)
    services = []
    for i in range(rng.randint(3, 5)):
        services.append({
            "name": f"svc-{chr(97 + i)}",
            "port": rng.randint(3000, 9000),
            "replicas": rng.randint(1, 4),
            "enabled": rng.random() > 0.3,
            "tags": rng.sample(["web", "api", "batch", "edge", "internal"], rng.randint(1, 3)),
            "owner": None if rng.random() < 0.3 else rng.choice(["ops", "data", "web"]),
        })
    data = {
        "version": "007",
        "region": rng.choice(["us-east", "eu-west"]),
        "timeout_seconds": round(rng.uniform(1, 30), 1),
        "description": "Deployment config.\nSecond line keeps its newline.\n",
        "services": services,
        "limits": {"cpu": f"{rng.randint(1, 8)}", "memory_mb": rng.randint(256, 4096)},
    }
    lines = [f'version: "{data["version"]}"', f"region: {data['region']}", f"timeout_seconds: {data['timeout_seconds']}",
             "description: |", "  Deployment config.", "  Second line keeps its newline.", "services:"]
    for s in services:
        lines += [f"  - name: {s['name']}", f"    port: {s['port']}", f"    replicas: {s['replicas']}",
                  f"    enabled: {'true' if s['enabled'] else 'false'}", f"    tags: [{', '.join(s['tags'])}]",
                  f"    owner: {s['owner'] if s['owner'] else 'null'}"]
    lines += ["limits:", f'  cpu: "{data["limits"]["cpu"]}"', f"  memory_mb: {data['limits']['memory_mb']}"]
    text = "\n".join(lines) + "\n"
    assert yaml.safe_load(text) == data, "fixture YAML must round-trip"
    (ws / "config.yaml").write_text(text, encoding="utf-8")
    se.write_json(hd / "expected.json", data)


# --------------------------------------------------------------------------- leap year

def is_leap(y: int) -> bool:
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def make_leap(params: dict, ws: Path, hd: Path, seed: int) -> None:
    rng = random.Random(seed)
    years = sorted(set([1600, 1700, 1900, 2000, 2100, 2400, 1996, 2023, 2024] +
                       [rng.randint(1, 3000) for _ in range(params["random_years"])]))
    (ws / "README.md").write_text("Write leap.py here.\n", encoding="utf-8")
    se.write_json(hd / "expected.json", {str(y): is_leap(y) for y in years})


# --------------------------------------------------------------------------- word frequency

VOCAB = ("river stone harbour lantern meadow orchard copper willow thunder signal ferry garden ladder market "
         "pepper canyon beacon timber quarry violet").split()
STOP = ["the", "a", "and", "of", "to", "in", "is", "it"]


def word_counts(text: str, stop: list[str]) -> list[list]:
    import re
    from collections import Counter
    words = [w for w in re.findall(r"[a-z]+", text.lower()) if w not in set(stop)]
    c = Counter(words)
    return [[w, n] for w, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:10]]


def make_word_freq(params: dict, ws: Path, hd: Path, seed: int) -> None:
    rng = random.Random(seed)
    weights = [rng.randint(1, 30) for _ in VOCAB]
    sentences = []
    for _ in range(params["sentences"]):
        ws_ = rng.choices(VOCAB, weights=weights, k=rng.randint(4, 9))
        filler = rng.sample(STOP, 3)
        words = [filler[0].capitalize()] + ws_[:2] + [filler[1]] + ws_[2:] + [filler[2]]
        sentences.append(" ".join(words) + rng.choice([".", "!", "?", ";", ","]))
    text = " ".join(sentences) + "\n"
    (ws / "text.txt").write_text(text, encoding="utf-8")
    (ws / "stopwords.txt").write_text("\n".join(STOP) + "\n", encoding="utf-8")
    se.write_json(hd / "expected.json", word_counts(text, STOP))


MAKERS = {
    "fizzbuzz": make_fizzbuzz, "arithmetic": make_arithmetic, "typo_fix": make_typo_fix,
    "csv_sort": make_csv_sort, "unit_conversion": make_unit_conversion, "rename": make_rename,
    "yaml_to_json": make_yaml_to_json, "leap_year": make_leap, "word_freq": make_word_freq,
}
