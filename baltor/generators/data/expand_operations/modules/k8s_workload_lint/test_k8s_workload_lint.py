import json
from pathlib import Path

import k8s_workload_lint as m

HERE = Path(__file__).parent


def rules(docs):
    return {(f.rule, f.severity) for f in m.lint_documents(docs)}


def test_hardened_example_has_only_info_findings():
    docs = m.load_documents((HERE / "examples" / "hardened-deployment.yaml").read_text())
    findings = m.lint_documents(docs)
    assert [f for f in findings if f.severity != "info"] == []


def test_bare_deployment_trips_restricted_rules():
    dep = {"apiVersion": "apps/v1", "kind": "Deployment", "metadata": {"name": "web"},
           "spec": {"replicas": 1, "template": {"metadata": {"labels": {"app": "web"}},
                                                "spec": {"containers": [{"name": "app", "image": "nginx"}]}}}}
    r = {x[0] for x in rules([dep])}
    assert {"K001", "K003", "K004", "K005", "K006", "K011", "K012", "K013", "K014", "K021", "K020", "K023"} <= r


def test_pod_level_security_context_is_inherited():
    pod = {"kind": "Pod", "metadata": {"name": "p", "namespace": "x"},
           "spec": {"automountServiceAccountToken": False,
                    "securityContext": {"runAsNonRoot": True, "seccompProfile": {"type": "RuntimeDefault"}},
                    "containers": [{"name": "c", "image": "r/i:1.0", "resources": {"requests": {"cpu": "10m", "memory": "16Mi"}, "limits": {"memory": "32Mi"}},
                                    "securityContext": {"allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True,
                                                        "capabilities": {"drop": ["ALL"]}}}]}}
    assert {f.rule for f in m.lint_documents([pod])} == {"K002"}


def test_host_access_and_caps_are_high():
    pod = {"kind": "Pod", "metadata": {"name": "p"},
           "spec": {"hostNetwork": True, "volumes": [{"name": "root", "hostPath": {"path": "/"}}],
                    "containers": [{"name": "c", "image": "i:1", "securityContext": {"privileged": True, "capabilities": {"add": ["SYS_ADMIN", "NET_BIND_SERVICE"]}}}]}}
    r = rules([pod])
    assert ("K015", "high") in r and ("K010", "high") in r and ("K013", "high") in r


def test_cronjob_pod_spec_path_and_no_probe_requirement():
    cj = {"kind": "CronJob", "metadata": {"name": "nightly", "namespace": "ops"},
          "spec": {"jobTemplate": {"spec": {"template": {"spec": {"containers": [{"name": "job", "image": "i:1"}]}}}}}}
    r = {x[0] for x in rules([cj])}
    assert "K003" in r and "K005" not in r


def test_secret_literal_env():
    pod = {"kind": "Pod", "metadata": {"name": "p"}, "spec": {"containers": [{"name": "c", "image": "i:1",
           "env": [{"name": "DB_PASSWORD", "value": "x"}, {"name": "API_TOKEN", "valueFrom": {"secretKeyRef": {"name": "s", "key": "k"}}}]}]}}
    hits = [f for f in m.lint_documents([pod]) if f.rule == "K024"]
    assert len(hits) == 1 and "DB_PASSWORD" in hits[0].message


def test_pdb_matching_and_namespace_label():
    dep = {"kind": "Deployment", "metadata": {"name": "web", "namespace": "a"},
           "spec": {"replicas": 3, "template": {"metadata": {"labels": {"app": "web"}}, "spec": {"containers": []}}}}
    pdb = {"kind": "PodDisruptionBudget", "metadata": {"name": "web"}, "spec": {"selector": {"matchLabels": {"app": "web"}}}}
    ns = {"kind": "Namespace", "metadata": {"name": "a"}}
    assert "K022" in {f.rule for f in m.lint_documents([dep])}
    r = {f.rule for f in m.lint_documents([dep, pdb, ns])}
    assert "K022" not in r and "K026" in r


def test_json_list_input_and_cli(tmp_path, capsys):
    lst = {"kind": "List", "items": [{"kind": "Pod", "metadata": {"name": "p"}, "spec": {"containers": [{"name": "c", "image": "i"}]}}]}
    p = tmp_path / "m.json"
    p.write_text(json.dumps(lst))
    assert len(m.load_documents(p.read_text())) == 1
    assert m.main([str(p)]) == 1
    assert m.main([str(HERE / "examples" / "hardened-deployment.yaml"), "--json"]) == 0
