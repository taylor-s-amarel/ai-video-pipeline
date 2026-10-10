"""One-line JSON logs for Python services: context binding, trace correlation and secret redaction.

    from json_structured_logging import configure_logging, bind_context
    log = configure_logging(service="checkout", level="INFO")
    with bind_context(request_id="r-123", tenant="acme"):
        log.info("order placed", extra={"order_id": 42, "amount_cents": 1999})

Output (one line)::

    {"ts":"2026-10-10T12:00:00.123Z","level":"INFO","logger":"checkout","msg":"order placed",
     "service":"checkout","request_id":"r-123","tenant":"acme","order_id":42,"amount_cents":1999}

When the OpenTelemetry API is installed and a span is active, ``trace_id`` and ``span_id`` are added
(imported lazily; nothing breaks without it). Keys that look like credentials are replaced with
``[REDACTED]`` at any depth. Standard library only.
"""

from __future__ import annotations

import contextlib
import contextvars
import datetime as _dt
import json
import logging
import os
import re
import sys
import traceback
from typing import Any, Iterator

_CONTEXT: contextvars.ContextVar[dict] = contextvars.ContextVar("log_context", default={})
SENSITIVE_KEY = re.compile(r"(pass(word|wd)?|secret|token|authori[sz]ation|api[_-]?key|cookie|session[_-]?id|private[_-]?key|credential)", re.I)
SENSITIVE_VALUE = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}")
REDACTED = "[REDACTED]"
_STD_ATTRS = set(vars(logging.LogRecord("", 0, "", 0, "", (), None))) | {"message", "asctime", "taskName"}


def redact(value: Any, depth: int = 0) -> Any:
    """Return a copy with sensitive keys replaced and bearer/basic credentials masked."""
    if depth > 8:
        return "[TRUNCATED]"
    if isinstance(value, dict):
        return {k: (REDACTED if SENSITIVE_KEY.search(str(k)) else redact(v, depth + 1)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact(v, depth + 1) for v in value]
    if isinstance(value, str):
        return SENSITIVE_VALUE.sub(lambda m: f"{m.group(1)} {REDACTED}", value)
    return value


def _trace_ids() -> dict:
    try:
        from opentelemetry import trace  # type: ignore  # optional, lazy
    except ImportError:
        return {}
    ctx = trace.get_current_span().get_span_context()
    if not getattr(ctx, "is_valid", False):
        return {}
    return {"trace_id": f"{ctx.trace_id:032x}", "span_id": f"{ctx.span_id:016x}"}


class JsonFormatter(logging.Formatter):
    def __init__(self, service: str | None = None, static: dict | None = None):
        super().__init__()
        self.service = service or os.environ.get("OTEL_SERVICE_NAME") or os.environ.get("SERVICE_NAME")
        self.static = dict(static or {})

    def format(self, record: logging.LogRecord) -> str:
        ts = _dt.datetime.fromtimestamp(record.created, tz=_dt.timezone.utc)
        out: dict[str, Any] = {
            "ts": ts.strftime("%Y-%m-%dT%H:%M:%S.") + f"{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if self.service:
            out["service"] = self.service
        out.update(self.static)
        out.update(_CONTEXT.get())
        out.update(_trace_ids())
        for key, val in record.__dict__.items():
            if key not in _STD_ATTRS and not key.startswith("_"):
                out[key] = val
        if record.exc_info and record.exc_info[0] is not None:
            etype, evalue, tb = record.exc_info
            out["error"] = {"type": etype.__name__, "message": str(evalue),
                            "stack": "".join(traceback.format_exception(etype, evalue, tb))[-8000:]}
        out["msg"] = redact(out["msg"])
        return json.dumps(redact(out), default=str, ensure_ascii=False, separators=(",", ":"))


@contextlib.contextmanager
def bind_context(**fields: Any) -> Iterator[None]:
    """Add fields to every log line emitted inside the block (async- and thread-safe via contextvars)."""
    token = _CONTEXT.set({**_CONTEXT.get(), **fields})
    try:
        yield
    finally:
        _CONTEXT.reset(token)


def configure_logging(service: str | None = None, level: str | int = "INFO", stream=None,
                      static: dict | None = None, logger_name: str | None = None) -> logging.Logger:
    """Install a single JSON handler on the root logger (idempotent) and return a named logger."""
    root = logging.getLogger()
    for h in list(root.handlers):
        if getattr(h, "_json_structured", False):
            root.removeHandler(h)
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter(service, static))
    handler._json_structured = True  # type: ignore[attr-defined]
    root.addHandler(handler)
    root.setLevel(level)
    return logging.getLogger(logger_name or service or "app")
