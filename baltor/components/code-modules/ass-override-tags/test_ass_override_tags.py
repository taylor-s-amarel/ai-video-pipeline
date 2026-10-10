import pytest

import ass_override_tags as t


def test_block_example():
    assert t.block(t.pos(540, 1500), t.fad(80, 120), t.color("#FFD21F"), t.blur(1.5)) == \
        "{\\pos(540,1500)\\fad(80,120)\\1c&H1FD2FF&\\blur1.5}"


def test_alpha_inverted():
    assert t.alpha(1.0) == "\\alpha&H00&"
    assert t.alpha(0.0, 3) == "\\3a&HFF&"
    assert t.alpha(0.98) == "\\alpha&H05&"


def test_transform_and_move():
    assert t.transform(t.scale(112), t1=0, t2=72, accel=0.5) == "\\t(0,72,0.5,\\fscx112\\fscy112)"
    assert t.transform(t.blur(0)) == "\\t(\\blur0)"
    assert t.move(0, 0, 10, 20, 0, 500) == "\\move(0,0,10,20,0,500)"


@pytest.mark.parametrize("call", [
    lambda: t.an(0), lambda: t.alpha(1.5), lambda: t.color("#12345"), lambda: t.fs(0),
    lambda: t.move(0, 0, 1, 1, t1=5), lambda: t.block("pos(1,1)"), lambda: t.rotate(5, "w"),
    lambda: t.transform(), lambda: t.fad(-1, 0),
])
def test_validation(call):
    with pytest.raises(ValueError):
        call()
