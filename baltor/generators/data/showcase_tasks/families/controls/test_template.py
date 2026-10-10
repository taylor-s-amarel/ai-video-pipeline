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
