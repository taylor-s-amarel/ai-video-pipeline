import json
import xml.etree.ElementTree as ET

import pytest

from qa_report_writer import Report


def sample():
    r = Report("demo")
    r.add("duration", True, "64.0 s")
    r.add("motion", False, "window | 12-14 s", evidence="f.png")
    r.add("credit", None, "post text missing")
    return r


def test_totals_and_json():
    r = sample()
    assert r.totals() == {"passed": 1, "failed": 1, "not_checked": 1, "ok": False}
    assert json.loads(r.to_json())["checks"][1]["evidence"] == "f.png"


def test_markdown_escapes_and_status():
    md = sample().markdown()
    assert "**FAIL**" in md and "window \\| 12-14 s" in md and "not checked" in md
    ok = Report("x")
    ok.add("a", True)
    assert "**PASS**" in ok.markdown()
    inc = Report("y")
    inc.add("a", None)
    assert "**INCOMPLETE**" in inc.markdown()


def test_junit():
    root = ET.fromstring(sample().junit())
    assert root.get("failures") == "1" and root.get("skipped") == "1"
    assert root.find("testcase/failure") is not None


def test_validation():
    with pytest.raises(ValueError):
        Report("x").add("a", "yes")
