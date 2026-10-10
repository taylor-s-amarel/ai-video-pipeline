"""Self-test for this showcase task's evaluator.

Proves that evaluate.py passes a known-good output and fails a known-bad one,
using fixtures made by setup/make_fixtures.py. Run: python3 -m pytest -q <package dir>
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PKG = Path(__file__).resolve().parent
TASK = json.loads((PKG / "task.json").read_text(encoding="utf-8"))
PARAMS = TASK["params"]
sys.path.insert(0, str(PKG))


def run_setup(tmp_path: Path, seed: int = 20261010, extra: list | None = None) -> tuple[Path, Path]:
    ws, hd = tmp_path / "workspace", tmp_path / "hidden"
    proc = subprocess.run([sys.executable, str(PKG / "setup" / "make_fixtures.py"), "--workspace", str(ws),
                           "--hidden", str(hd), "--seed", str(seed)] + (extra or []),
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert (ws / "TASK.md").exists()
    return ws, hd


def evaluate(ws: Path, hd: Path) -> dict:
    proc = subprocess.run([sys.executable, str(PKG / "evaluate.py"), "--workspace", str(ws), "--hidden", str(hd)],
                          capture_output=True, text=True, timeout=TASK["evaluator"]["timeout_s"] + 60)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["task_id"] == TASK["task_id"]
    assert result["valid"], result["integrity_problems"]
    return result


def assert_good(result: dict) -> None:
    assert not result["errors"], result["errors"]
    assert result["passed"], json.dumps({k: result[k] for k in ("gates", "required_checks", "metrics", "checks")}, indent=1)[:4000]


def assert_bad(result: dict, good: dict | None = None) -> None:
    assert not result["passed"]
    if good is not None:
        assert result["score"] < good["score"]


def test_spec_hash_matches():
    import showcase_eval as se
    assert se.compute_spec_hash(TASK) == TASK["spec_hash"]
    assert se.integrity_problems(TASK, PKG) == []


def test_empty_workspace_fails(tmp_path):
    ws, hd = run_setup(tmp_path)
    for d in TASK["deliverables"]:
        p = ws / d["path"]
        if p.is_file():
            p.unlink()
    result = evaluate(ws, hd)
    assert not result["passed"]


import controls_fixtures as cf  # noqa: E402


def write_good(ws: Path, hd: Path) -> None:
    kind = PARAMS["kind"]
    if kind == "fizzbuzz":
        (ws / "output.txt").write_text((hd / "expected.txt").read_text())
    elif kind == "arithmetic":
        (ws / "answers.json").write_text((hd / "expected.json").read_text())
    elif kind == "typo_fix":
        (ws / "README.md").write_text((hd / "expected.md").read_text())
    elif kind == "csv_sort":
        rows = cf.se.read_csv(ws / "people.csv")
        cf.se.write_csv(ws / "sorted.csv", cf.sort_people(rows))
    elif kind == "unit_conversion":
        rows = cf.se.read_csv(ws / "conversions.csv")
        for r in rows:
            r["result"] = f"{cf.CONVERSIONS[(r['from_unit'], r['to_unit'])](float(r['value'])):.2f}"
        cf.se.write_csv(ws / "conversions.csv", rows)
    elif kind == "rename":
        for f in ws.rglob("*.py"):
            f.write_text(f.read_text().replace(PARAMS["old_name"], PARAMS["new_name"]))
    elif kind == "leap_year":
        (ws / "leap.py").write_text("def is_leap_year(y):\n    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)\n")
    elif kind == "yaml_to_json":
        import yaml
        (ws / "config.json").write_text(json.dumps(yaml.safe_load((ws / "config.yaml").read_text())))
    elif kind == "word_freq":
        stop = (ws / "stopwords.txt").read_text().split()
        (ws / "freq.json").write_text(json.dumps(cf.word_counts((ws / "text.txt").read_text(), stop)))


def write_bad(ws: Path, hd: Path) -> None:
    kind = PARAMS["kind"]
    write_good(ws, hd)
    if kind == "fizzbuzz":
        lines = (ws / "output.txt").read_text().splitlines()
        (ws / "output.txt").write_text("\n".join(str(i + 1) for i in range(len(lines))) + "\n")
    elif kind == "arithmetic":
        ans = json.loads((ws / "answers.json").read_text())
        ans["1"] = ans["1"] + 1
        (ws / "answers.json").write_text(json.dumps(ans))
    elif kind == "typo_fix":
        (ws / "README.md").write_text((ws / "README.md").read_text().replace("Harbour", "Harbor"))
    elif kind == "csv_sort":
        rows = cf.se.read_csv(ws / "sorted.csv")
        cf.se.write_csv(ws / "sorted.csv", sorted(rows, key=lambda r: (r["last_name"], int(r["age"]))))
    elif kind == "unit_conversion":
        rows = cf.se.read_csv(ws / "conversions.csv")
        for r in rows:
            if r["from_unit"] == "F":
                r["result"] = f"{(float(r['value']) - 32) / 1.8 + 1:.2f}"
        cf.se.write_csv(ws / "conversions.csv", rows)
    elif kind == "rename":
        p = ws / "shop" / "cart.py"
        p.write_text(p.read_text().replace(PARAMS["new_name"], PARAMS["old_name"]).replace(
            "from .pricing import " + PARAMS["old_name"], "from .pricing import " + PARAMS["new_name"] + " as " + PARAMS["old_name"]))
    elif kind == "leap_year":
        (ws / "leap.py").write_text("def is_leap_year(y):\n    return y % 4 == 0\n")
    elif kind == "yaml_to_json":
        data = json.loads((ws / "config.json").read_text())
        data["version"] = 7
        (ws / "config.json").write_text(json.dumps(data))
    elif kind == "word_freq":
        data = json.loads((ws / "freq.json").read_text())
        (ws / "freq.json").write_text(json.dumps(sorted(data)))


@pytest.mark.parametrize("seed", [11, 20261010])
def test_known_good_passes_and_known_bad_fails(tmp_path, seed):
    ws, hd = run_setup(tmp_path / "good", seed)
    write_good(ws, hd)
    good = evaluate(ws, hd)
    assert_good(good)
    ws2, hd2 = run_setup(tmp_path / "bad", seed)
    write_bad(ws2, hd2)
    bad = evaluate(ws2, hd2)
    assert_bad(bad, good)


def test_fixtures_are_deterministic(tmp_path):
    a = run_setup(tmp_path / "a", 5)
    b = run_setup(tmp_path / "b", 5)
    for f in sorted(p.relative_to(a[0]) for p in a[0].rglob("*") if p.is_file()):
        assert (a[0] / f).read_bytes() == (b[0] / f).read_bytes(), f
