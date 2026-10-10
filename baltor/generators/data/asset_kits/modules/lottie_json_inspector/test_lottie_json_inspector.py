import io
import json
import zipfile

import pytest

import lottie_json_inspector as li


def doc(**kw):
    d = {"v": "5.7.4", "fr": 30, "ip": 0, "op": 90, "w": 1080, "h": 1920, "nm": "pop",
         "assets": [{"id": "comp_0", "layers": [{"ty": 4, "nm": "inner shape"}, {"ty": 1, "nm": "solid"}]},
                    {"id": "img_0", "w": 64, "h": 64, "u": "", "p": "data:image/png;base64,AAAA", "e": 1}],
         "layers": [{"ty": 0, "refId": "comp_0", "nm": "precomp"}, {"ty": 4, "nm": "shape"},
                    {"ty": 2, "refId": "img_0"}, {"ty": 3}],
         "markers": [{"cm": "loop", "tm": 0, "dr": 90}]}
    d.update(kw)
    return d


def test_basic_counts_and_duration():
    r = li.inspect_document(doc())
    assert r["duration_s"] == 3.0 and r["fps"] == 30
    assert r["layers"] == {"precomposition": 1, "shape": 2, "solid": 1, "image": 1, "null": 1}
    assert r["precompositions"] == 1 and r["precomp_depth"] == 1
    assert r["images"][0]["embedded"] is True
    assert r["markers"] == ["loop"]
    assert r["issues"] == []


def test_flags_external_images_fonts_expressions_off_spec_layers_and_aspect():
    d = doc(w=512, h=512)
    d["assets"].append({"id": "img_1", "w": 10, "h": 10, "u": "images/", "p": "img_1.png", "e": 0})
    d["layers"].append({"ty": 5, "nm": "title text"})
    d["fonts"] = {"list": [{"fName": "Inter-Bold", "fFamily": "Inter"}]}
    d["layers"][1]["ks"] = {"o": {"a": 0, "k": 100, "x": "loopOut('cycle')"}}
    r = li.inspect_document(d, min_seconds=5)
    text = " | ".join(r["issues"])
    assert "external image" in text and "images/img_1.png" == r["images"][1]["path"]
    assert "ty-5" in text and "Inter" in text and "expression" in text
    assert "aspect 512x512" in text and "only 3.0 s" in text


def test_invalid_documents():
    with pytest.raises(li.LottieError):
        li.inspect_document({"fr": 30})
    with pytest.raises(li.LottieError):
        li.inspect_document(doc(op=0))
    with pytest.raises(li.LottieError):
        li.load_documents(b"not json")


def test_precomp_cycle_does_not_loop_forever():
    d = doc()
    d["assets"][0]["layers"].append({"ty": 0, "refId": "comp_0"})
    r = li.inspect_document(d)
    assert r["total_layers"] < 50


def test_dotlottie_archive(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("manifest.json", json.dumps({"animations": [{"id": "a"}, {"id": "b"}]}))
        z.writestr("animations/a.json", json.dumps(doc()))
        z.writestr("animations/b.json", json.dumps(doc(op=30)))
    p = tmp_path / "pack.lottie"
    p.write_bytes(buf.getvalue())
    reports = li.inspect(p)
    assert [r["duration_s"] for r in reports] == [3.0, 1.0]


def test_cli(tmp_path, capsys):
    p = tmp_path / "a.json"
    p.write_text(json.dumps(doc()))
    bad = tmp_path / "bad.json"
    bad.write_text("{}")
    assert li.main([str(p)]) == 0
    assert li.main([str(p), str(bad), "--json"]) == 1
