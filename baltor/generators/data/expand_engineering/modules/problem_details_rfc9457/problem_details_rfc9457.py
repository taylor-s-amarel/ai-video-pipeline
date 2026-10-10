"""Build, validate and serialise RFC 9457 Problem Details (application/problem+json).

RFC 9457 (July 2023, obsoletes RFC 7807) defines the members ``type`` (URI
reference, default ``about:blank``), ``title``, ``status``, ``detail`` and
``instance``, plus extension members. This module keeps one error shape across a
service: a constructor, a validator, a validation-errors helper using the RFC's
``errors``/``pointer`` example pattern, and a framework-neutral response tuple.

    >>> body = problem(404, detail="Order 42 does not exist", instance="/orders/42")
    >>> body["title"]
    'Not Found'
"""

from __future__ import annotations

import json
import re
from http import HTTPStatus
from typing import Any

MEDIA_TYPE = "application/problem+json"
STANDARD_MEMBERS = ("type", "title", "status", "detail", "instance")
EXTENSION_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,}$")  # RFC 9457 3.2: SHOULD, for XML compatibility
URI_REF_RE = re.compile(r"^[^\s<>\"{}|\\^`]*$")


def status_phrase(status: int) -> str:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return "Error"


def problem(status: int, *, type: str = "about:blank", title: str | None = None, detail: str | None = None,
            instance: str | None = None, **extensions: Any) -> dict:
    """Build a problem details object. With type 'about:blank', title defaults to the status phrase."""
    if not 100 <= int(status) <= 599:
        raise ValueError("status must be an HTTP status code (100-599)")
    doc: dict[str, Any] = {"type": type, "title": title or (status_phrase(status) if type == "about:blank" else None),
                           "status": int(status)}
    if doc["title"] is None:
        raise ValueError("give a title for a non-default problem type")
    if detail:
        doc["detail"] = detail
    if instance:
        doc["instance"] = instance
    for k, v in extensions.items():
        if k in STANDARD_MEMBERS:
            raise ValueError(f"{k} is a standard member; pass it as a keyword argument")
        doc[k] = v
    return doc


def validation_problem(errors: list[tuple[str, str]], *, type: str = "about:blank", status: int = 422,
                       title: str | None = None, detail: str | None = None, instance: str | None = None) -> dict:
    """One problem listing several field errors as {detail, pointer} (JSON Pointer per RFC 6901)."""
    items = [{"detail": d, "pointer": p if p.startswith("#") else "#" + p} for p, d in errors]
    return problem(status, type=type, title=title or ("Your request is not valid." if type != "about:blank" else None),
                   detail=detail or f"{len(items)} field(s) failed validation", instance=instance, errors=items)


def validate(doc: Any, http_status: int | None = None) -> list[str]:
    """Return a list of problems with a problem details object (empty when it looks right)."""
    out: list[str] = []
    if not isinstance(doc, dict):
        return ["a problem details document must be a JSON object"]
    t = doc.get("type", "about:blank")
    if not isinstance(t, str) or not URI_REF_RE.match(t):
        out.append("'type' must be a URI reference string")
    if "status" in doc:
        s = doc["status"]
        if not isinstance(s, int) or isinstance(s, bool) or not 100 <= s <= 599:
            out.append("'status' must be an integer HTTP status code")
        elif http_status is not None and s != http_status:
            out.append(f"'status' {s} does not match the HTTP response status {http_status}")
    for k in ("title", "detail"):
        if k in doc and not isinstance(doc[k], str):
            out.append(f"'{k}' must be a string")
    if "instance" in doc and (not isinstance(doc["instance"], str) or not URI_REF_RE.match(doc["instance"])):
        out.append("'instance' must be a URI reference string")
    if t == "about:blank" and isinstance(doc.get("status"), int) and doc.get("title") not in (None, status_phrase(doc["status"])):
        out.append("with type 'about:blank' the title SHOULD be the HTTP status phrase")
    for k in doc:
        if k not in STANDARD_MEMBERS and not EXTENSION_NAME_RE.match(k):
            out.append(f"extension member '{k}' should start with a letter and use 3+ letters, digits or '_'")
    detail = doc.get("detail")
    if isinstance(detail, str) and re.search(r"Traceback \(most recent call last\)|\bat [\w.$]+\(.*:\d+\)", detail):
        out.append("'detail' looks like a stack trace; do not leak internals to clients")
    return out


def to_response(doc: dict, headers: dict | None = None) -> tuple[int, dict, bytes]:
    """(status, headers, body) for any web framework."""
    h = {"Content-Type": MEDIA_TYPE, **(headers or {})}
    return doc.get("status", 500), h, json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def from_exception(exc: BaseException, mapping: dict[type, tuple[int, str]] | None = None,
                   instance: str | None = None) -> dict:
    """Map an exception to a problem without exposing its message unless the mapping says so."""
    for cls, (status, type_uri) in (mapping or {}).items():
        if isinstance(exc, cls):
            return problem(status, type=type_uri, title=cls.__name__ if type_uri != "about:blank" else None,
                           detail=str(exc) or None, instance=instance)
    return problem(500, instance=instance)
