#!/usr/bin/env python3
"""Lint Kubernetes manifests for resources, probes and the Pod Security "restricted" profile.

Usage::

    python k8s_workload_lint.py manifests/*.yaml [--fail-on high] [--json]
    helm template ./chart | python k8s_workload_lint.py -

Reads YAML (multi-document; needs PyYAML, imported lazily) or JSON (standard library). Exit 1 when a
finding reaches ``--fail-on`` (default ``high``). It complements, and does not replace, server-side
Pod Security Admission, kubeconform schema validation and policy engines such as Kyverno or Gatekeeper.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any, Iterable

SEVERITY = {"info": 0, "low": 1, "medium": 2, "high": 3}
WORKLOADS = {"Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "Job", "CronJob", "Pod"}
LONG_RUNNING = {"Deployment", "StatefulSet", "DaemonSet", "ReplicaSet"}
SECRET_ENV = re.compile(r"(PASSWORD|PASSWD|SECRET|TOKEN|API_?KEY|ACCESS_?KEY|PRIVATE_?KEY|CREDENTIAL)", re.I)
ALLOWED_ADD_CAPS = {"NET_BIND_SERVICE"}


@dataclass
class Finding:
    rule: str
    severity: str
    object: str
    message: str


def load_documents(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        return []
    if text.startswith(("{", "[")):
        data = json.loads(text)
        docs = data if isinstance(data, list) else [data]
    else:
        try:
            import yaml  # type: ignore  # lazy: only YAML input needs PyYAML
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("YAML input needs PyYAML (pip install pyyaml); JSON input works without it") from exc
        docs = [d for d in yaml.safe_load_all(text) if d]
    out = []
    for d in docs:
        if isinstance(d, dict) and d.get("kind", "").endswith("List") and isinstance(d.get("items"), list):
            out.extend(i for i in d["items"] if isinstance(i, dict))
        elif isinstance(d, dict):
            out.append(d)
    return out


def pod_spec(obj: dict) -> dict | None:
    kind, spec = obj.get("kind"), obj.get("spec") or {}
    if kind == "Pod":
        return spec
    if kind == "CronJob":
        return (((spec.get("jobTemplate") or {}).get("spec") or {}).get("template") or {}).get("spec")
    if kind in WORKLOADS:
        return (spec.get("template") or {}).get("spec")
    return None


def _name(obj: dict) -> str:
    md = obj.get("metadata") or {}
    ns = md.get("namespace")
    return f"{obj.get('kind')}/{(ns + '/') if ns else ''}{md.get('name', '?')}"


def _containers(spec: dict) -> Iterable[tuple[str, dict]]:
    for key in ("initContainers", "containers"):
        for c in spec.get(key) or []:
            yield key, c


def _labels_match(selector: dict, labels: dict) -> bool:
    ml = (selector or {}).get("matchLabels") or {}
    return bool(ml) and all(labels.get(k) == v for k, v in ml.items())


def lint_documents(docs: list[dict]) -> list[Finding]:
    out: list[Finding] = []
    pdbs = [d for d in docs if d.get("kind") == "PodDisruptionBudget"]
    for obj in docs:
        name, kind = _name(obj), obj.get("kind")
        md = obj.get("metadata") or {}
        if kind == "Namespace":
            labels = md.get("labels") or {}
            if "pod-security.kubernetes.io/enforce" not in labels:
                out.append(Finding("K026", "medium", name, "namespace has no pod-security.kubernetes.io/enforce label (use restricted or baseline)"))
            continue
        if kind == "Service" and (obj.get("spec") or {}).get("type") in {"LoadBalancer", "NodePort"}:
            out.append(Finding("K025", "info", name, f"Service type {(obj.get('spec') or {}).get('type')} exposes the workload outside the cluster; confirm intent"))
        spec = pod_spec(obj)
        if spec is None:
            continue
        if not md.get("namespace"):
            out.append(Finding("K023", "info", name, "no metadata.namespace; it lands in whatever namespace kubectl targets"))
        psc = spec.get("securityContext") or {}
        for flag in ("hostNetwork", "hostPID", "hostIPC"):
            if spec.get(flag):
                out.append(Finding("K015", "high", name, f"{flag}: true breaks isolation from the node"))
        for v in spec.get("volumes") or []:
            if "hostPath" in v:
                out.append(Finding("K015", "high", name, f"hostPath volume '{v.get('name')}' mounts the node filesystem"))
        if spec.get("automountServiceAccountToken") is not False:
            out.append(Finding("K020", "low", name, "service account token is auto-mounted; set automountServiceAccountToken: false unless the app calls the API"))
        pod_seccomp = (psc.get("seccompProfile") or {}).get("type")
        for section, c in _containers(spec):
            cname = f"{name} [{c.get('name', '?')}]"
            image = str(c.get("image", ""))
            last = image.split("@")[0].rsplit("/", 1)[-1]
            if "@sha256:" not in image and (":" not in last or last.endswith(":latest")):
                out.append(Finding("K001", "medium", cname, f"image '{image}' has no tag or uses :latest"))
            elif "@sha256:" not in image:
                out.append(Finding("K002", "info", cname, f"image '{image}' is not pinned by digest"))
            res = c.get("resources") or {}
            req, lim = res.get("requests") or {}, res.get("limits") or {}
            if not req.get("cpu") or not req.get("memory"):
                out.append(Finding("K003", "medium", cname, "missing resources.requests.cpu/memory; the scheduler cannot place it reliably"))
            if not lim.get("memory"):
                out.append(Finding("K004", "medium", cname, "missing resources.limits.memory; one leak can starve the node"))
            if section == "containers" and kind in LONG_RUNNING:
                if not c.get("readinessProbe"):
                    out.append(Finding("K005", "medium", cname, "no readinessProbe; traffic arrives before the app is ready"))
                if not c.get("livenessProbe"):
                    out.append(Finding("K006", "low", cname, "no livenessProbe; a hung process is never restarted"))
            sc = c.get("securityContext") or {}
            if sc.get("privileged"):
                out.append(Finding("K010", "high", cname, "privileged: true"))
            if sc.get("allowPrivilegeEscalation") is not False:
                out.append(Finding("K011", "high", cname, "allowPrivilegeEscalation must be false (restricted profile)"))
            non_root = sc.get("runAsNonRoot", psc.get("runAsNonRoot"))
            run_as = sc.get("runAsUser", psc.get("runAsUser"))
            if run_as == 0:
                out.append(Finding("K012", "high", cname, "runAsUser: 0 runs as root"))
            elif non_root is not True:
                out.append(Finding("K012", "high", cname, "runAsNonRoot is not true (restricted profile)"))
            caps = sc.get("capabilities") or {}
            if "ALL" not in [str(x).upper() for x in caps.get("drop") or []]:
                out.append(Finding("K013", "medium", cname, "capabilities.drop must include ALL (restricted profile)"))
            extra = [x for x in caps.get("add") or [] if str(x).upper() not in ALLOWED_ADD_CAPS]
            if extra:
                out.append(Finding("K013", "high", cname, f"adds capabilities {extra}; restricted allows only NET_BIND_SERVICE"))
            seccomp = (sc.get("seccompProfile") or {}).get("type") or pod_seccomp
            if seccomp not in {"RuntimeDefault", "Localhost"}:
                out.append(Finding("K014", "medium", cname, "seccompProfile.type must be RuntimeDefault or Localhost (restricted profile)"))
            if sc.get("readOnlyRootFilesystem") is not True:
                out.append(Finding("K016", "low", cname, "readOnlyRootFilesystem is not true; mount an emptyDir for scratch space"))
            for p in c.get("ports") or []:
                if p.get("hostPort"):
                    out.append(Finding("K015", "medium", cname, f"hostPort {p.get('hostPort')} ties the pod to node ports"))
            for env in c.get("env") or []:
                if SECRET_ENV.search(str(env.get("name", ""))) and "value" in env and env.get("value"):
                    out.append(Finding("K024", "high", cname, f"env {env.get('name')} has a literal value; use valueFrom.secretKeyRef"))
        if kind == "Deployment":
            replicas = (obj.get("spec") or {}).get("replicas", 1)
            if isinstance(replicas, int) and replicas < 2:
                out.append(Finding("K021", "low", name, f"replicas={replicas}: a node drain or rollout causes downtime"))
            labels = ((obj.get("spec") or {}).get("template") or {}).get("metadata", {}).get("labels") or {}
            if isinstance(replicas, int) and replicas >= 2 and not any(_labels_match((p.get("spec") or {}).get("selector"), labels) for p in pdbs):
                out.append(Finding("K022", "low", name, "no PodDisruptionBudget in these manifests selects this Deployment"))
    return sorted(out, key=lambda f: (-SEVERITY[f.severity], f.object, f.rule))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("files", nargs="+", help="manifest files, or - for stdin")
    ap.add_argument("--fail-on", choices=list(SEVERITY), default="high")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    docs: list[dict] = []
    for path in a.files:
        text = sys.stdin.read() if path == "-" else open(path, encoding="utf-8").read()
        docs += load_documents(text)
    findings = lint_documents(docs)
    if a.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.severity.upper():6} {f.rule} {f.object}: {f.message}")
        print(f"{len(findings)} finding(s) in {len(docs)} object(s)")
    return 1 if any(SEVERITY[f.severity] >= SEVERITY[a.fail_on] for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
