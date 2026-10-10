import pytest

from render_cache_key import Plan, step_key


def test_key_changes_with_inputs_and_params(tmp_path):
    f = tmp_path / "bg.mp4"
    f.write_bytes(b"one")
    k1 = step_key("bg", {"seconds": 64}, inputs=[str(f)])
    assert k1 == step_key("bg", {"seconds": 64}, inputs=[str(f)])
    assert k1 != step_key("bg", {"seconds": 65}, inputs=[str(f)])
    f.write_bytes(b"two")
    assert k1 != step_key("bg", {"seconds": 64}, inputs=[str(f)])
    assert step_key("c", deps=["b", "a"]) == step_key("c", deps=["a", "b"])
    with pytest.raises(ValueError):
        step_key("x", {"bad": float("nan")})


def test_plan_freshness(tmp_path):
    out = tmp_path / "final.mp4"
    plan = Plan(str(tmp_path / "cache"))
    assert not plan.is_fresh("k", str(out))
    out.write_bytes(b"video")
    plan.record("k", str(out))
    assert plan.is_fresh("k", str(out)) and not plan.is_fresh("other", str(out))
    out.write_bytes(b"edited by hand")
    assert not plan.is_fresh("k", str(out))
