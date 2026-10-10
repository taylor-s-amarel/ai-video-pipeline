import json

import pytest

import problem_details_rfc9457 as pd


def test_default_type_and_title():
    p = pd.problem(404, detail="Order 42 does not exist", instance="/orders/42")
    assert p == {"type": "about:blank", "title": "Not Found", "status": 404,
                 "detail": "Order 42 does not exist", "instance": "/orders/42"}
    assert pd.validate(p, http_status=404) == []


def test_custom_type_requires_title_and_extensions():
    with pytest.raises(ValueError):
        pd.problem(403, type="https://example.com/probs/out-of-credit")
    p = pd.problem(403, type="https://example.com/probs/out-of-credit", title="You do not have enough credit.",
                   detail="Your current balance is 30, but that costs 50.", balance=30, accounts=["/account/12345"])
    assert p["balance"] == 30 and pd.validate(p) == []


def test_standard_member_as_extension_rejected():
    with pytest.raises(ValueError):
        pd.problem(400, **{"status": 400})


def test_validation_problem_pointers():
    p = pd.validation_problem([("/age", "must be a positive integer"), ("#/profile/color", "must be one of red, blue")],
                              type="https://example.net/validation-error")
    assert p["status"] == 422 and p["errors"][0] == {"detail": "must be a positive integer", "pointer": "#/age"}
    assert pd.validate(p) == []


@pytest.mark.parametrize("doc,fragment", [
    ([], "JSON object"),
    ({"type": "not a uri", "status": 400}, "URI reference"),
    ({"status": "400"}, "integer"),
    ({"status": 400, "title": "Bad Request"}, None),
    ({"status": 404, "title": "Missing"}, "status phrase"),
    ({"status": 500, "detail": "Traceback (most recent call last):\n  File x"}, "stack trace"),
    ({"status": 400, "x": 1}, "extension member"),
])
def test_validate_cases(doc, fragment):
    problems = pd.validate(doc)
    if fragment is None:
        assert problems == []
    else:
        assert any(fragment in p for p in problems), problems


def test_status_mismatch():
    assert "does not match" in pd.validate(pd.problem(400), http_status=422)[0]


def test_to_response():
    status, headers, body = pd.to_response(pd.problem(409, detail="already processing"), {"Retry-After": "1"})
    assert status == 409 and headers["Content-Type"] == "application/problem+json"
    assert json.loads(body)["title"] == "Conflict" and headers["Retry-After"] == "1"


def test_from_exception_hides_unmapped_messages():
    class OutOfStock(Exception):
        pass
    mapped = pd.from_exception(OutOfStock("only 2 left"), {OutOfStock: (409, "https://example.com/probs/out-of-stock")})
    assert mapped["status"] == 409 and mapped["detail"] == "only 2 left" and mapped["title"] == "OutOfStock"
    hidden = pd.from_exception(RuntimeError("db password wrong"))
    assert hidden == {"type": "about:blank", "title": "Internal Server Error", "status": 500}
