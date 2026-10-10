"""Inspect Lottie JSON and dotLottie (.lottie) files before using them in a video or a Godot/web scene.

Reports what decides whether an animation is usable as an overlay in a
1080x1920 short: frame rate, length in seconds, canvas size and aspect,
layer counts by type (including inside precompositions), image assets
(embedded data URIs versus external files that must travel with the JSON),
fonts and text, expressions, 3D layers and markers.

Layer types named by the lottie-spec schema: 0 precomposition, 1 solid,
2 image, 3 null, 4 shape. Other ``ty`` values (text, audio, camera ... from
After Effects/Bodymovin exports) are counted as ``ty-N`` and flagged, because
players outside the spec's core set may not render them.

Usage::

    python lottie_json_inspector.py anim.json [more.lottie ...] [--json] [--target 1080x1920] [--min-seconds 1]
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

SPEC_LAYER_TYPES = {0: "precomposition", 1: "solid", 2: "image", 3: "null", 4: "shape"}


class LottieError(ValueError):
    """Not a usable Lottie document."""


def load_documents(path_or_bytes: str | Path | bytes) -> list[tuple[str, dict]]:
    """One (name, document) per animation; .lottie archives may hold several."""
    if isinstance(path_or_bytes, (bytes, bytearray)):
        data, name = bytes(path_or_bytes), "<bytes>"
    else:
        data, name = Path(path_or_bytes).read_bytes(), str(path_or_bytes)
    if data[:2] == b"PK":
        docs = []
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for info in z.infolist():
                n = info.filename
                if n.endswith(".json") and (n.startswith("animations/") or n.startswith("a/")):
                    if info.file_size > 64 * 1024 * 1024:
                        raise LottieError(f"{n} is larger than 64 MB")
                    docs.append((f"{name}:{n}", json.loads(z.read(n).decode("utf-8"))))
        if not docs:
            raise LottieError("dotLottie archive without animations/*.json")
        return docs
    try:
        return [(name, json.loads(data.decode("utf-8")))]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LottieError(f"not JSON: {exc}") from exc


def _walk_layers(layers: list, assets_by_id: dict, depth: int = 0, seen: set | None = None):
    seen = seen or set()
    for layer in layers or []:
        yield layer, depth
        ref = layer.get("refId")
        if layer.get("ty") == 0 and ref in assets_by_id and ref not in seen and depth < 32:
            yield from _walk_layers(assets_by_id[ref].get("layers", []), assets_by_id, depth + 1, seen | {ref})


def _count_expressions(node) -> int:
    n = 0
    stack = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            if isinstance(cur.get("x"), str) and ("k" in cur or "a" in cur):
                n += 1
            stack.extend(cur.values())
        elif isinstance(cur, list):
            stack.extend(cur)
    return n


def inspect_document(doc: dict, name: str = "", target: tuple[int, int] | None = (1080, 1920),
                     min_seconds: float = 0.0) -> dict:
    for key in ("fr", "ip", "op", "w", "h", "layers"):
        if key not in doc:
            raise LottieError(f"missing top-level '{key}'")
    fr, ip, op = float(doc["fr"]), float(doc["ip"]), float(doc["op"])
    if fr <= 0 or op <= ip:
        raise LottieError("frame rate must be > 0 and op > ip")
    w, h = int(doc["w"]), int(doc["h"])
    assets = doc.get("assets", [])
    by_id = {a.get("id"): a for a in assets if "layers" in a}
    images = []
    for a in assets:
        if "layers" in a or "p" not in a:
            continue
        embedded = a.get("e") == 1 or str(a.get("p", "")).startswith("data:")
        images.append({"id": a.get("id"), "w": a.get("w"), "h": a.get("h"), "embedded": embedded,
                       **({} if embedded else {"path": f"{a.get('u', '')}{a.get('p', '')}"})})
    counts: dict[str, int] = {}
    three_d = 0
    max_depth = 0
    for layer, depth in _walk_layers(doc["layers"], by_id):
        ty = layer.get("ty")
        label = SPEC_LAYER_TYPES.get(ty, f"ty-{ty}")
        counts[label] = counts.get(label, 0) + 1
        three_d += 1 if layer.get("ddd") == 1 else 0
        max_depth = max(max_depth, depth)
    fonts = [f.get("fFamily") or f.get("fName") for f in doc.get("fonts", {}).get("list", [])]
    report = {
        "name": name or doc.get("nm", ""),
        "version": doc.get("v"),
        "fps": fr,
        "frames": op - ip,
        "duration_s": round((op - ip) / fr, 3),
        "width": w, "height": h,
        "aspect": round(w / h, 4) if h else None,
        "layers": counts,
        "total_layers": sum(counts.values()),
        "precomp_depth": max_depth,
        "precompositions": len(by_id),
        "images": images,
        "fonts": fonts,
        "expressions": _count_expressions(doc),
        "three_d_layers": three_d,
        "markers": [m.get("cm") for m in doc.get("markers", [])],
        "issues": [],
    }
    issues = report["issues"]
    off_spec = sorted(k for k in counts if k.startswith("ty-"))
    if off_spec:
        issues.append(f"layer types outside the lottie-spec core set ({', '.join(off_spec)}): test in your target player")
    ext = [i for i in images if not i["embedded"]]
    if ext:
        issues.append(f"{len(ext)} external image(s): ship them with the JSON or embed them")
    if fonts:
        issues.append(f"uses font(s) {', '.join(str(f) for f in fonts)}: make sure each is installed and licensed")
    if report["expressions"]:
        issues.append(f"{report['expressions']} expression(s): many players (and ThorVG-based ones) ignore or limit expressions")
    if three_d:
        issues.append("3D layers present: support varies by player")
    if target:
        ta = target[0] / target[1]
        if report["aspect"] and abs(report["aspect"] - ta) > 0.02:
            scale = min(target[0] / w, target[1] / h)
            issues.append(f"aspect {w}x{h} differs from target {target[0]}x{target[1]}: letterbox or crop (fit scale {scale:.2f})")
    if min_seconds and report["duration_s"] < min_seconds:
        issues.append(f"only {report['duration_s']} s long: loop it or pick a longer animation")
    return report


def inspect(path_or_bytes, target=(1080, 1920), min_seconds: float = 0.0) -> list[dict]:
    return [inspect_document(doc, name, target, min_seconds) for name, doc in load_documents(path_or_bytes)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--target", default="1080x1920")
    ap.add_argument("--min-seconds", type=float, default=0.0)
    a = ap.parse_args(argv)
    tw, th = (int(v) for v in a.target.lower().split("x"))
    failed, reports = False, []
    for f in a.files:
        try:
            reports += inspect(f, (tw, th), a.min_seconds)
        except (OSError, LottieError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
            failed = True
            reports.append({"name": f, "error": str(exc)})
    if a.json:
        print(json.dumps(reports, indent=2))
    else:
        for r in reports:
            if "error" in r:
                print(f"{r['name']}: ERROR {r['error']}")
                continue
            print(f"{r['name']}: {r['width']}x{r['height']} {r['fps']} fps {r['duration_s']} s, "
                  f"{r['total_layers']} layer(s) {r['layers']}")
            for i in r["issues"]:
                print(f"  ! {i}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
