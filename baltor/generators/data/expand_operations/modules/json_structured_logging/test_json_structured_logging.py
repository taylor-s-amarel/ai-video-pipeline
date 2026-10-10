import io
import json
import logging

import json_structured_logging as m


def setup():
    buf = io.StringIO()
    log = m.configure_logging(service="svc", level="DEBUG", stream=buf, static={"env": "test"})
    return log, buf


def lines(buf):
    return [json.loads(x) for x in buf.getvalue().splitlines() if x.strip()]


def test_basic_fields_and_extra():
    log, buf = setup()
    log.info("hello %s", "world", extra={"order_id": 7})
    rec = lines(buf)[-1]
    assert rec["msg"] == "hello world" and rec["level"] == "INFO" and rec["service"] == "svc"
    assert rec["order_id"] == 7 and rec["env"] == "test" and rec["ts"].endswith("Z")


def test_context_binding_nests_and_resets():
    log, buf = setup()
    with m.bind_context(request_id="r1"):
        with m.bind_context(user="u1"):
            log.info("inner")
        log.info("outer")
    log.info("after")
    a, b, c = lines(buf)[-3:]
    assert a["request_id"] == "r1" and a["user"] == "u1"
    assert b["request_id"] == "r1" and "user" not in b
    assert "request_id" not in c


def test_redaction_of_keys_and_bearer_values():
    log, buf = setup()
    log.warning("calling api with Bearer abcdefghijklmnop", extra={"headers": {"Authorization": "x", "Accept": "json"},
                                                                     "db_password": "p", "items": [{"api_key": "k"}]})
    rec = lines(buf)[-1]
    assert rec["headers"]["Authorization"] == "[REDACTED]" and rec["headers"]["Accept"] == "json"
    assert rec["db_password"] == "[REDACTED]" and rec["items"][0]["api_key"] == "[REDACTED]"
    assert "abcdefghijklmnop" not in rec["msg"]


def test_exception_and_unserialisable():
    log, buf = setup()
    try:
        raise ValueError("boom")
    except ValueError:
        log.exception("failed", extra={"obj": object()})
    rec = lines(buf)[-1]
    assert rec["error"]["type"] == "ValueError" and "boom" in rec["error"]["stack"]
    assert isinstance(rec["obj"], str)


def test_configure_is_idempotent():
    setup()
    setup()
    assert sum(getattr(h, "_json_structured", False) for h in logging.getLogger().handlers) == 1


def test_redact_helper_depth_limit():
    deep = {}
    cur = deep
    for _ in range(20):
        cur["x"] = {}
        cur = cur["x"]
    assert "[TRUNCATED]" in json.dumps(m.redact(deep))
