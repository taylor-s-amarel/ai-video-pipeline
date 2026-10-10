import json
from pathlib import Path

import pytest

import terraform_plan_risk_report as m

HERE = Path(__file__).parent


def rc(address, rtype, actions, after=None, before=None, **extra):
    return {"address": address, "mode": "managed", "type": rtype, "name": address.split(".")[-1],
            "change": {"actions": actions, "before": before, "after": after, **extra}}


def plan(*changes, drift=(), outputs=None):
    return {"format_version": "1.2", "terraform_version": "1.13.1", "resource_changes": list(changes),
            "resource_drift": list(drift), "output_changes": outputs or {}}


def test_classify_actions():
    assert m.classify(["no-op"]) == "no-op"
    assert m.classify(["delete", "create"]) == "replace"
    assert m.classify(["create", "delete"]) == "replace"
    assert m.classify(["forget"]) == "forget"


def test_stateful_delete_is_high_and_fails():
    rep = m.analyse(plan(rc("aws_db_instance.main", "aws_db_instance", ["delete"], before={"id": "x"})))
    assert rep.max_severity == "high"
    assert rep.findings[0].rule == "delete"


def test_stateless_delete_is_medium():
    rep = m.analyse(plan(rc("aws_instance.web", "aws_instance", ["delete"])))
    assert rep.max_severity == "medium"


def test_replace_reports_order_and_forcing_path():
    rep = m.analyse(plan(rc("aws_s3_bucket.logs", "aws_s3_bucket", ["create", "delete"], after={"bucket": "b"},
                            replace_paths=[["bucket"]])))
    f = rep.findings[0]
    assert f.rule == "replace" and f.severity == "high"
    assert "create-before-destroy" in f.message and "bucket" in f.message


def test_iam_wildcard_policy_detected():
    doc = json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "*", "Resource": "*"}]})
    rep = m.analyse(plan(rc("aws_iam_policy.admin", "aws_iam_policy", ["create"], after={"policy": doc})))
    assert any(f.rule == "iam-wildcard" for f in rep.findings)


def test_scoped_iam_policy_not_flagged():
    doc = json.dumps({"Statement": [{"Effect": "Allow", "Action": ["s3:GetObject"], "Resource": "arn:aws:s3:::b/*"}]})
    rep = m.analyse(plan(rc("aws_iam_policy.read", "aws_iam_policy", ["create"], after={"policy": doc})))
    assert not any(f.rule == "iam-wildcard" for f in rep.findings)


def test_open_ingress_variants():
    sg = rc("aws_security_group.web", "aws_security_group", ["update"],
            after={"ingress": [{"from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]}, before={})
    rule = rc("aws_vpc_security_group_ingress_rule.ssh", "aws_vpc_security_group_ingress_rule", ["create"],
              after={"cidr_ipv4": "0.0.0.0/0", "from_port": 22})
    fw = rc("google_compute_firewall.all", "google_compute_firewall", ["create"], after={"source_ranges": ["0.0.0.0/0"]})
    rep = m.analyse(plan(sg, rule, fw))
    assert sum(f.rule == "open-ingress" for f in rep.findings) == 3


def test_public_access_block_disabled():
    rep = m.analyse(plan(rc("aws_s3_bucket_public_access_block.b", "aws_s3_bucket_public_access_block", ["update"],
                            after={"block_public_acls": False, "block_public_policy": True}, before={})))
    assert any(f.rule == "s3-public-access" and "block_public_acls" in f.message for f in rep.findings)


def test_deletion_protection_turned_off():
    rep = m.analyse(plan(rc("aws_db_instance.db", "aws_db_instance", ["update"],
                            before={"deletion_protection": True}, after={"deletion_protection": False})))
    assert any(f.rule == "deletion-protection-off" for f in rep.findings)


def test_required_tags_respect_tags_all_and_unknown():
    tagged = rc("aws_instance.a", "aws_instance", ["create"], after={"tags": {"owner": "x"}, "tags_all": {"owner": "x", "environment": "prod"}})
    missing = rc("aws_instance.b", "aws_instance", ["create"], after={"tags": {"owner": "x"}, "tags_all": {"owner": "x"}})
    unknown = rc("aws_instance.c", "aws_instance", ["create"], after={"tags": {}}, after_unknown={"tags_all": True})
    rep = m.analyse(plan(tagged, missing, unknown), require_tags=["owner", "environment"])
    flagged = [f.address for f in rep.findings if f.rule == "missing-tags"]
    assert flagged == ["aws_instance.b"]


def test_drift_and_outputs_reported():
    d = rc("aws_instance.a", "aws_instance", ["update"])
    rep = m.analyse(plan(drift=[d], outputs={"url": {"actions": ["update"]}, "same": {"actions": ["no-op"]}}))
    assert rep.drift and rep.output_changes == ["url: update"]
    assert rep.max_severity == "info"


def test_data_sources_ignored_and_counts():
    data = {"address": "data.aws_ami.x", "mode": "data", "type": "aws_ami", "change": {"actions": ["read"]}}
    rep = m.analyse(plan(data, rc("aws_instance.a", "aws_instance", ["create"], after={})))
    assert rep.counts == {"create": 1}


def test_rejects_non_plan_document():
    with pytest.raises(ValueError):
        m.analyse({"values": {}})


def test_real_tofu_plan_fixture_parses():
    data = json.loads((HERE / "fixtures" / "tofu_plan_terraform_data.json").read_text())
    rep = m.analyse(data)
    assert rep.counts.get("create", 0) + rep.counts.get("replace", 0) >= 1
    md = m.to_markdown(rep)
    assert "Plan risk report" in md


def test_cli_exit_codes(tmp_path, capsys):
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan(rc("aws_db_instance.main", "aws_db_instance", ["delete"]))))
    assert m.main([str(p), "--format", "json"]) == 1
    assert m.main([str(p), "--fail-on", "never"]) == 0
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    assert m.main([str(bad)]) == 2
