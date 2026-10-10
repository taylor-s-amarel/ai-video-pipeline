"""Write QA results as Markdown, JSON and JUnit XML.

A check is ``{"name", "passed", "detail", "evidence"?}``; ``passed`` may be
``None`` for "not checked", which is reported honestly instead of being
counted as a pass. One report feeds three readers: a person (Markdown
table), a pipeline (JSON with totals) and CI (JUnit XML, where not-checked
items are marked skipped).

Usage::

    from qa_report_writer import Report
    r = Report("sylvia-earle-v3")
    r.add("duration", True, "64.0 s (min 60)")
    r.add("background motion", False, "window 12-14 s mean diff 0.21", evidence="frames/12s.png")
    r.add("music credit in post", None, "post text not provided")
    open("qa.md", "w").write(r.markdown())
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET


class Report:
    def __init__(self, subject: str):
        self.subject = subject
        self.checks: list[dict] = []

    def add(self, name: str, passed: bool | None, detail: str = "", evidence: str | None = None) -> None:
        if passed not in (True, False, None):
            raise ValueError("passed must be True, False or None")
        c = {"name": name, "passed": passed, "detail": detail}
        if evidence:
            c["evidence"] = evidence
        self.checks.append(c)

    def totals(self) -> dict:
        p = sum(1 for c in self.checks if c["passed"] is True)
        f = sum(1 for c in self.checks if c["passed"] is False)
        n = sum(1 for c in self.checks if c["passed"] is None)
        return {"passed": p, "failed": f, "not_checked": n, "ok": f == 0 and n == 0}

    def to_json(self) -> str:
        return json.dumps({"subject": self.subject, "totals": self.totals(), "checks": self.checks}, indent=2,
                          ensure_ascii=False)

    def markdown(self) -> str:
        t = self.totals()
        status = "PASS" if t["ok"] else ("FAIL" if t["failed"] else "INCOMPLETE")
        lines = [f"# QA: {self.subject}", "",
                 f"**{status}**: {t['passed']} passed, {t['failed']} failed, {t['not_checked']} not checked", "",
                 "| Check | Result | Detail | Evidence |", "|---|---|---|---|"]
        for c in self.checks:
            res = {True: "pass", False: "FAIL", None: "not checked"}[c["passed"]]
            cells = [c["name"], res, c["detail"], c.get("evidence", "")]
            lines.append("| " + " | ".join(str(x).replace("|", "\\|").replace("\n", " ") for x in cells) + " |")
        return "\n".join(lines) + "\n"

    def junit(self) -> str:
        t = self.totals()
        suite = ET.Element("testsuite", name=self.subject, tests=str(len(self.checks)), failures=str(t["failed"]),
                           skipped=str(t["not_checked"]))
        for c in self.checks:
            case = ET.SubElement(suite, "testcase", classname=self.subject, name=c["name"])
            if c["passed"] is False:
                ET.SubElement(case, "failure", message=c["detail"][:500])
            elif c["passed"] is None:
                ET.SubElement(case, "skipped", message=c["detail"][:500] or "not checked")
        return ET.tostring(suite, encoding="unicode")
