#!/usr/bin/env python3
"""Visual style presets for vertical shorts.

Produces, for the video domain:

* 14 contract schemas (caption, title, background layer, layer stack, 2x2 grid, transition, camera
  move, text animation, palette, typography pairing, animation style, aspect format, thumbnail style
  and whole-look style preset), each with valid and invalid examples;
* one code module (``short_style_preset_kit``) with the maths and ffmpeg/Pillow builders;
* base presets as skills (each ships preset.json, schema.json and scripts/check_preset.py);
* parameterised variants (palette, aspect format, platform, theme, tempo, topic) that point at
  their base with ``variant_of``.

Data tables live in data/video_styles/. Procedural background recipes are below as code because
they are ffmpeg filter graphs built from expression helpers. Contrast numbers are computed here
with the kit's WCAG functions; palette pairs that fail are never emitted.
"""

from __future__ import annotations

import copy
import json
import math
import re
import sys
from pathlib import Path

import yaml

from _lib import GeneratorRun, dumps, effects, skill_md

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "video_styles"
sys.path.insert(0, str(DATA / "code"))
import style_kit as kit  # noqa: E402

try:
    import jsonschema  # type: ignore
except ImportError:  # pragma: no cover
    jsonschema = None

TODAY = "2026-10-10"
DATA_REL = "generators/data/video_styles"
SCHEMA_URL = "https://github.com/taylor-s-amarel/ai-video-pipeline/baltor/contract-schemas/"
KIT = "short_style_preset_kit"
FFMPEG_DOCS = "https://ffmpeg.org/ffmpeg-filters.html"
WCAG_URL = "https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum"
LUM_URL = "https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html"
FPS = 30
LOOP_S = 8


def load_yaml(name: str):
    return yaml.safe_load((DATA / name).read_text(encoding="utf-8"))


PALETTES = load_yaml("palettes.yaml")
FORMATS = load_yaml("formats.yaml")
CAPTIONS = load_yaml("captions.yaml")
TITLES = load_yaml("titles.yaml")
BACKGROUNDS = load_yaml("backgrounds.yaml")
MOTION = load_yaml("motion.yaml")
TYPOGRAPHY = load_yaml("typography.yaml")
ANIM = load_yaml("animation_styles.yaml")
TOPICS = ANIM.pop("topics")
THUMBS = load_yaml("thumbnails.yaml")
STACKS = load_yaml("stacks.yaml")
LOOKS = load_yaml("looks.yaml")
FONTS = json.loads((DATA / "fonts.json").read_text())["fonts"]
_MEASURED_PATH = DATA / "measured.json"
MEASURED = json.loads(_MEASURED_PATH.read_text()) if _MEASURED_PATH.exists() else {}
CODE = {name: (DATA / "code" / name).read_text(encoding="utf-8")
        for name in ("style_kit.py", "style_kit_checks.py", "check_preset.py")}

ASPECTS = FORMATS["aspects"]
TARGETS = FORMATS["targets"]

# --------------------------------------------------------------------------- small helpers


def kebab(identity: str) -> str:
    return identity.replace("_", "-")


def check_skill_identity(identity: str) -> None:
    if len(kebab(identity)) > 64:
        raise ValueError(f"skill identity too long for SKILL.md name: {identity} ({len(identity)})")


def md_table(rows: list[tuple], header: tuple) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in r) + " |")
    return "\n".join(out)


def bullets(items) -> str:
    return "\n".join(f"- {i}" for i in items)


def floor2(x: float) -> float:
    return math.floor(x * 100 + 1e-9) / 100


def worst_panel(fg: str, tint: str, opacity: float) -> float:
    """Unrounded worst-case contrast of fg over a tint panel at opacity over unknown video."""
    dark = kit.composite(tint, (0, 0, 0), opacity)
    light = kit.composite(tint, (255, 255, 255), opacity)
    lf, ld, ll = kit.relative_luminance(fg), kit.relative_luminance(dark), kit.relative_luminance(light)
    if ld <= lf <= ll:
        return 1.0
    return min(kit._ratio_from_luminance(lf, ld), kit._ratio_from_luminance(lf, ll))


def contrast_entry(fg: str, bg: str, size_px: float, weight: int, basis: str, opacity: float | None = None,
                   **extra) -> tuple[dict, bool]:
    if basis == "panel-worst-case":
        r = worst_panel(fg, bg, float(opacity))
    else:
        r = kit.contrast_ratio(fg, bg)
    need = kit.required_ratio(size_px, weight)
    entry = {"basis": basis, "fg": fg, "bg": bg}
    if basis == "panel-worst-case":
        entry["opacity"] = round(float(opacity), 3)
    entry.update({"ratio": floor2(r), "required": need, "size_px": size_px, "weight": weight,
                  "level": kit.wcag_level(r, size_px, weight)})
    entry.update(extra)
    return entry, r >= need


def font_info(family: str, weight: int) -> dict:
    f = FONTS[family]
    return {"family": family, "weight": weight, "licence": f["licence"], "file_url": f["file_url"],
            "licence_url": f["licence_url"], "specimen_url": f["specimen_url"]}


def avg_em(family: str, case: str) -> float:
    m = FONTS[family]["metrics"]
    return m["avg_char_em_caps"] if case == "upper" else m["avg_char_em_mixed"]


def target_info(target_id: str) -> dict:
    t = TARGETS[target_id]
    a = ASPECTS[t["aspect"]]
    w, h = a["size"]
    return {"id": target_id, "label": t["label"], "platform": t["platform"], "aspect": a["ratio"],
            "width": w, "height": h, "safe_margins": dict(t["margins"]), "margins_basis": FORMATS["margin_basis"].strip()}


def aspect_target(aspect_id: str) -> str:
    return {"9x16": "generic_9x16", "4x5": "feed_4x5", "1x1": "square_1x1", "16x9": "landscape_16x9"}[aspect_id]


def palette_colors(pid: str) -> dict:
    return PALETTES[pid]["colors"]


def compatible(mode_needed: str | None, pid: str) -> bool:
    return mode_needed is None or PALETTES[pid]["mode"] == mode_needed


EFFECTS_RENDER = effects(filesystem="write", executes="python",
                         side_effects=["runs ffmpeg/ffprobe commands from SKILL.md that write render files into the working directory",
                                       "scripts/check_preset.py reads preset.json and schema.json"])
EFFECTS_CHECK = effects(filesystem="read", executes="python",
                        side_effects=["scripts/check_preset.py reads preset.json and schema.json"])
FONT_HOSTS = ["raw.githubusercontent.com"]
EFFECTS_FONTS = effects(filesystem="write", executes="python", hosts=FONT_HOSTS,
                        side_effects=["downloads font files from the google/fonts repository on GitHub",
                                      "runs ffmpeg and scripts/check_preset.py"])
FOOTAGE_HOSTS = ["commons.wikimedia.org", "upload.wikimedia.org", "images.nasa.gov", "www.nasa.gov", "www.pexels.com",
                 "pixabay.com"]

# --------------------------------------------------------------------------- procedural background recipes
# Expression helpers. Every recipe returns an ffmpeg filter graph that ends in [out] (W x H, yuv420p)
# and loops seamlessly every P seconds: time terms are periodic in P and scrolled textures move a
# whole number of tile widths per loop.


def _hsh(i: str, j: str) -> str:
    s = f"sin(({i})*127.1+({j})*311.7)*43758.5453"
    return f"(({s})-floor({s}))"


def _vnoise(x: str, y: str, px: int, py: int, salt: int = 0, s: int = 0) -> str:
    a, b, fx, fy = s, s + 1, s + 2, s + 3
    i0, i1 = f"mod(ld({a}),{px})+{salt}", f"mod(ld({a})+1,{px})+{salt}"
    j0, j1 = f"mod(ld({b}),{py})", f"mod(ld({b})+1,{py})"
    return (f"(st({a},floor({x}));st({b},floor({y}));"
            f"st({fx},({x})-ld({a}));st({fy},({y})-ld({b}));"
            f"st({fx},ld({fx})*ld({fx})*(3-2*ld({fx})));st({fy},ld({fy})*ld({fy})*(3-2*ld({fy})));"
            f"lerp(lerp({_hsh(i0, j0)},{_hsh(i1, j0)},ld({fx})),lerp({_hsh(i0, j1)},{_hsh(i1, j1)},ld({fx})),ld({fy})))")


def tfbm(nx: int, ny: int, octaves: int = 3, seed: int = 0) -> str:
    """Tileable value-noise fbm in [0, 1] over the texture (lattice wraps at nx, ny)."""
    parts, amp, total = [], 1.0, 0.0
    for o in range(octaves):
        f = 2 ** o
        parts.append(f"{amp:g}*{_vnoise(f'X/W*{nx * f}', f'Y/H*{ny * f}', nx * f, ny * f, salt=(o + 1) * 1013 + seed * 7919)}")
        total += amp
        amp *= 0.5
    return f"(({'+'.join(parts)})/{total:g})"


def particles(cell: int, rmin: float, rmax: float, density: float, seed: int = 0, soft: float = 1.0) -> str:
    """Tileable soft discs: at most one per cell, kept inside the cell so the texture wraps cleanly."""
    i, j = f"floor(X/{cell})", f"floor(Y/{cell})"
    pres = f"lt({_hsh(f'{i}+{seed}', f'{j}+{seed * 3 + 1}')},{density})"
    px = f"(({i})+0.3+0.4*{_hsh(f'{i}+{seed + 11}', j)})*{cell}"
    py = f"(({j})+0.3+0.4*{_hsh(i, f'{j}+{seed + 23}')})*{cell}"
    r = f"({rmin}+({rmax}-{rmin})*{_hsh(f'{i}+{seed + 5}', f'{j}+{seed + 7}')})"
    bri = f"(0.35+0.65*{_hsh(f'{i}+{seed + 13}', f'{j}+{seed + 17}')})"
    d = f"hypot(X-{px},Y-{py})"
    return f"(255*{pres}*{bri}*pow(clip(1-{d}/{r},0,1),{soft}))"


def streaks(cell: int, seed: int, width: float = 1.6, head: float = 2.4, density: float = 0.6) -> str:
    i = f"floor(X/{cell})"
    dx = f"(X-(({i})+0.5)*{cell})"
    yh = f"({_hsh(f'{i}+{seed}', 3)}*H)"
    ln = f"(H*(0.05+0.12*{_hsh(f'{i}+{seed + 1}', 5)}))"
    pres = f"lt({_hsh(f'{i}+{seed + 2}', 9)},{density})"
    return (f"(st(5,mod({yh}-Y,H));st(6,{ln});255*{pres}*min(1,if(lt(ld(5),ld(6)),(1-ld(5)/ld(6))*0.55,0)"
            f"*exp(-{dx}*{dx}/(2*{width}*{width}))+exp(-({dx}*{dx}+ld(5)*ld(5))/(2*{head}*{head}))))")


def gradmap(stops) -> str:
    """lutrgb mapping a gray value through colour stops [(pos, '#RRGGBB'), ...]."""
    stops = sorted((int(p), c) for p, c in stops)
    out = []
    for ch in range(3):
        vals = [(p, int(c[1 + 2 * ch:3 + 2 * ch], 16)) for p, c in stops]
        expr = str(vals[-1][1])
        for k in range(len(vals) - 2, -1, -1):
            (p0, c0), (p1, c1) = vals[k], vals[k + 1]
            expr = f"if(lt(val,{p1}),lerp({c0},{c1},(val-{p0})/{max(p1 - p0, 1)}),{expr})"
        if vals[0][0] > 0:
            expr = f"if(lt(val,{vals[0][0]}),{vals[0][1]},{expr})"
        out.append(expr)
    return "lutrgb=r='{}':g='{}':b='{}'".format(*out)


def snap(n: float, cell: int) -> int:
    return max(cell, int(round(n / cell)) * cell)


def finish(stops, W: int, H: int, flags: str = "bicubic", blur: float = 0.0) -> str:
    b = f"gblur=sigma={blur}," if blur else ""
    return f"{b}format=gbrp,{gradmap(stops)},scale={W}:{H}:flags={flags},setsar=1,format=yuv420p[out]"


def per_frame(expr: str, w: int, h: int, fps: int, P: int) -> str:
    return f"color=c=black:s={w}x{h}:r={fps}:d={P},format=gray,geq=lum='{expr}'"


def texture(expr: str, w: int, h: int, fps: int, P: int, W: int, H: int, blur: float = 0.0) -> str:
    """One tileable frame at work size, blurred and upscaled once, repeated for P seconds."""
    n = int(round(P * fps))
    b = f",gblur=sigma={blur}" if blur else ""
    return (f"color=c=black:s={w}x{h}:r={fps}:d=1,trim=end_frame=1,format=gray,geq=lum='{expr}'{b},"
            f"scale={W}:{H}:flags=bicubic,loop=loop={n - 1}:size=1:start=0,setpts=N/({fps}*TB)")


def scroll(kx: int, ky: int, fps: int, P: int) -> str:
    n = P * fps
    return f"scroll=horizontal={kx / n:.10f}:vertical={ky / n:.10f}"


def U() -> str:
    return "st(0,X/W);st(1,Y/H);"


def ph(P: int) -> str:
    return f"(2*PI*T/{P})"


def gauss2(cx: str, cy: str, s: float) -> str:
    return f"exp(-(pow(ld(0)-({cx}),2)+pow((ld(1)-({cy}))*H/W,2))/(2*{s}*{s}))"


def warp_graph(src_expr: str, w: int, h: int, fps: int, P: int, W: int, H: int, amount: float = 0.18,
               k_src=(0, -1)) -> str:
    src = texture(src_expr, w, h, fps, P, W, H)
    m1 = texture("255*" + tfbm(3, 5, 2, seed=21), w, h, fps, P, W, H)
    m2 = texture("255*" + tfbm(3, 5, 2, seed=33), w, h, fps, P, W, H)
    lut = f"lut=y='128+(val-128)*{min(2.1, round(amount * W / 100, 2))}'"
    return (f"{src},{scroll(k_src[0], k_src[1], fps, P)}[s];{m1},{scroll(1, 0, fps, P)},{lut}[mx];"
            f"{m2},{scroll(0, 1, fps, P)},{lut}[my];[s][mx][my]displace=edge=wrap")


def g_ocean_waves(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    w1 = f"sin(2*PI*ld(1)*6-{p}+1.4*sin(2*PI*ld(0)*1.2+{p}))"
    e = (U() + f"st(2,{w1});st(3,sin(2*PI*(ld(1)*13+ld(0)*1.7)-2*{p}));"
         f"clip(60+70*ld(1)+35*ld(2)+15*ld(3)+80*pow(max(0,ld(2)),14),0,255)")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=1.2)


def g_meadow_wind(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    e = (U() + f"st(2,0.38+0.012*sin(2*PI*ld(0)*2+{p}));"
         f"st(3,clip((ld(1)-ld(2))/(1-ld(2)),0,1));"
         f"st(4,0.5+0.5*sin(2*PI*(ld(0)*55+1.3*ld(3)*sin(2*{p}+ld(0)*6))));"
         f"if(lt(ld(1),ld(2)),205+45*ld(1)/ld(2)+6*sin(2*PI*ld(0)*3-{p}),"
         f"clip(35+95*ld(4)*(0.35+0.65*(1-ld(3)))+30*sin(2*PI*(ld(0)*2+ld(1))-2*{p}),0,190))")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=0.6)


def g_sunlit_water(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    c = (f"sin(2*PI*ld(0)*2.2+1.5*sin(2*PI*ld(1)*1.4+{p}))+sin(2*PI*ld(1)*2.6+1.2*sin(2*PI*ld(0)*1.3-{p}))"
         f"+sin(2*PI*(ld(0)+ld(1))*1.6+{p})")
    e = U() + f"st(2,{c});clip(45+210*pow(1-abs(ld(2))/3,7),0,255)"
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=0.8)


def g_coastal_aerial(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    e = (U() + f"st(2,ld(0)*0.55+ld(1)-0.78+0.035*sin(2*PI*ld(0)*5+2*{p})+0.012*sin(2*PI*ld(0)*13-3*{p}));"
         f"st(3,exp(-ld(2)*ld(2)/(2*0.012*0.012)));"
         f"max(if(lt(ld(2),0),clip(20+100*(1+ld(2)/0.5)+22*sin(2*PI*ld(2)*20+2*{p}),0,125),"
         f"170+20*sin(2*PI*ld(0)*9)*sin(2*PI*ld(1)*7)),255*ld(3))")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=0.8)


def g_cloud_timelapse(W, H, fps, P, stops):
    w, h = W // 4, H // 4
    t = texture("255*" + tfbm(4, 6, 4, seed=3), w, h, fps, P, W, H)
    t2 = texture("255*" + tfbm(3, 5, 3, seed=29), w, h, fps, P, W, H)
    return (f"{t},{scroll(1, 0, fps, P)}[a1];{t2},{scroll(2, 0, fps, P)}[b1];"
            f"[a1][b1]blend=all_mode=average," + finish(stops, W, H, blur=1.5))


def g_rain_on_glass(W, H, fps, P, stops):
    w, h = snap(W // 4, 30), snap(H // 4, 30)
    lights = texture(particles(30, 6, 12, 0.5, seed=12, soft=0.4), w, h, fps, P, W, H, blur=5)
    s1 = texture(streaks(10, 1), w, h, fps, P, W, H)
    s2 = texture(streaks(15, 40, 2.0, 3.2, 0.5), w, h, fps, P, W, H)
    return (f"{lights},lut=y='val*0.55+18',{scroll(1, 0, fps, P)}[bg];"
            f"{s1},{scroll(0, 1, fps, P)}[s1];{s2},{scroll(0, 2, fps, P)}[s2];"
            f"[s1][s2]blend=all_mode=lighten[s];[bg][s]blend=all_mode=screen," + finish(stops, W, H))


def g_city_night_bokeh(W, H, fps, P, stops):
    c = 30
    w, h = snap(W // 4, c), snap(H // 4, c)
    a = texture(particles(c, 5, 12, 0.55, seed=2, soft=0.35), w, h, fps, P, W, H, blur=1.2)
    b = texture(particles(c, 3, 8, 0.5, seed=19, soft=0.35), w, h, fps, P, W, H, blur=2.5)
    return (f"{a},{scroll(1, 0, fps, P)}[a];{b},{scroll(-1, 0, fps, P)}[b];"
            f"[a][b]blend=all_mode=screen," + finish(stops, W, H))


def g_forest_sunbeams(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    e = (U() + "st(2,atan2(Y+0.15*H,X+0.1*W));"
         f"st(3,pow(0.5+0.5*sin(ld(2)*17+0.9*sin(2*{p}+ld(2)*3)),3));"
         f"clip(28+30*(1-ld(1))+16*sin(2*PI*ld(0)*7+1)*sin(2*PI*ld(1)*5)"
         f"+190*ld(3)*exp(-1.1*hypot(ld(0),ld(1)))*(0.7+0.3*sin(2*{p})),0,255)")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=1.0)


def g_ink_in_water(W, H, fps, P, stops):
    w, h = W // 4, H // 4
    g = warp_graph("clip(255*(" + tfbm(3, 4, 4, seed=5) + "-0.38)*2.6,0,255)", w, h, fps, P, W, H, 0.2)
    return g + "," + finish(stops, W, H, blur=1.0)


def g_campfire_embers(W, H, fps, P, stops):
    w, h, p = snap(W // 4, 30), snap(H // 4, 30), ph(P)
    glow = per_frame(U() + f"clip(110*exp(-(1-ld(1))*3.2)*(0.82+0.18*sin(3*{p}+ld(0)*7)),0,255)", w, h, fps, P)
    a = texture(particles(15, 1.2, 2.6, 0.35, seed=4, soft=0.8), w, h, fps, P, W, H)
    b = texture(particles(30, 2, 4, 0.3, seed=9, soft=0.6), w, h, fps, P, W, H)
    return (f"{glow},scale={W}:{H}[g];{a},{scroll(0, -1, fps, P)}[a];{b},{scroll(0, -2, fps, P)}[b];"
            f"[a][b]blend=all_mode=lighten[p];[g][p]blend=all_mode=lighten," + finish(stops, W, H))


def g_neon_grid(W, H, fps, P, stops):
    w, h = W // 2, H // 2
    e = (U() + "st(2,0.56);st(3,ld(1)-ld(2));"
         "if(gt(ld(3),0),"
         f"st(4,0.25/ld(3));st(5,pow(abs(cos(PI*(ld(4)-2*T/{P}))),40));"
         "st(6,pow(abs(cos(PI*(ld(0)-0.5)/ld(3)*1.6)),40));"
         "clip(25+230*max(ld(5),ld(6))*clip(ld(3)*8,0,1),0,255),"
         "st(7,hypot(ld(0)-0.5,(ld(1)-ld(2)+0.11)*H/W));"
         "if(lt(ld(7),0.17)*(lt(ld(1),ld(2)-0.11)+gt(sin(ld(1)*260),-0.2)),215,20+110*pow(ld(1)/ld(2),2)))")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=0.5)


def g_warm_paper(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    tex = texture("255*" + tfbm(24, 40, 3, seed=12), w, h, fps, P, W, H)
    light = per_frame(U() + f"clip(128+80*sin(2*PI*ld(0)+2*{p})*cos(2*PI*ld(1)*0.8-2*{p})"
                            f"-40*hypot(ld(0)-0.5,ld(1)-0.5),0,255)", w, h, fps, P)
    return (f"{tex}[t];{light},scale={W}:{H}[l];[t][l]blend=all_expr='A*0.45+B*0.55',"
            + finish(stops, W, H, blur=0.4))


def g_light_leaks(W, H, fps, P, stops):
    w, h, p = W // 8, H // 8, ph(P)
    e = U() + "clip(255*(0.95*{}+0.8*{}+0.6*{}),0,255)".format(
        gauss2(f"0.2+0.25*sin({p})", f"0.25+0.2*cos({p})", 0.28),
        gauss2(f"0.8+0.2*cos({p}+1)", f"0.7+0.25*sin(2*{p})", 0.32),
        gauss2(f"0.5+0.4*sin({p}+2)", f"0.5+0.4*sin({p})", 0.2))
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H)


def g_dust_particles(W, H, fps, P, stops):
    w, h = snap(W // 4, 30), snap(H // 4, 30)
    a = texture(particles(15, 0.8, 1.8, 0.3, seed=6, soft=1.2), w, h, fps, P, W, H)
    b = texture(particles(30, 1.5, 3.2, 0.3, seed=27, soft=1.0), w, h, fps, P, W, H, blur=1.2)
    return (f"{a},{scroll(0, -1, fps, P)}[a];{b},{scroll(1, -1, fps, P)}[b];"
            f"[a][b]blend=all_mode=lighten," + finish(stops, W, H))


def g_atmospheric_haze(W, H, fps, P, stops):
    w, h = W // 4, H // 4
    t = texture("255*" + tfbm(3, 5, 3, seed=14), w, h, fps, P, W, H)
    t2 = texture("255*" + tfbm(2, 4, 3, seed=47), w, h, fps, P, W, H)
    return (f"{t},{scroll(1, 0, fps, P)}[a1];{t2},{scroll(-1, 0, fps, P)}[b1];"
            f"[a1][b1]blend=all_mode=average,eq=contrast=1.6," + finish(stops, W, H, blur=2))


def g_bokeh_drift(W, H, fps, P, stops):
    w, h = snap(W // 4, 30), snap(H // 4, 30)
    a = texture(particles(30, 7, 13, 0.4, seed=31, soft=0.3), w, h, fps, P, W, H, blur=1.5)
    b = texture(particles(15, 3, 6, 0.3, seed=44, soft=0.3), w, h, fps, P, W, H, blur=1)
    return (f"{a},{scroll(1, -1, fps, P)}[a];{b},{scroll(-1, -2, fps, P)}[b];"
            f"[a][b]blend=all_mode=screen," + finish(stops, W, H))


def g_film_grain(W, H, fps, P, stops):
    w, h = W // 2, H // 2
    return (f"color=c=0x808080:s={w}x{h}:r={fps}:d={P},noise=alls=36:allf=t+u:all_seed=1234,format=gray,"
            + finish(stops, W, H))


def g_starfield_drift(W, H, fps, P, stops):
    w, h = snap(W // 4, 30), snap(H // 4, 30)
    a = texture(particles(15, 0.6, 1.5, 0.45, seed=51, soft=1.5), w, h, fps, P, W, H)
    b = texture(particles(30, 1.2, 2.4, 0.35, seed=57, soft=1.2), w, h, fps, P, W, H)
    neb = texture("clip(255*(" + tfbm(2, 4, 3, seed=61) + "-0.45)*1.4,0,110)", w, h, fps, P, W, H, blur=3)
    return (f"{a},{scroll(2, 0, fps, P)}[a];{b},{scroll(4, 0, fps, P)}[b];{neb},{scroll(1, 0, fps, P)}[n];"
            f"[a][b]blend=all_mode=lighten[s];[n][s]blend=all_mode=screen," + finish(stops, W, H))


def g_aurora_ribbons(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    r1 = f"exp(-pow(ld(1)-(0.32+0.07*sin(2*PI*ld(0)*1.5+2*{p})+0.03*sin(2*PI*ld(0)*4-3*{p})),2)/(2*0.04*0.04))"
    r2 = f"exp(-pow(ld(1)-(0.46+0.05*sin(2*PI*ld(0)*1.1-2*{p}+1)),2)/(2*0.03*0.03))"
    cur = f"(0.55+0.45*sin(2*PI*ld(0)*18-2*{p}+2*sin(2*{p}+2*PI*ld(0)*2)))"
    e = U() + f"st(2,{cur});clip(255*(0.9*{r1}*ld(2)+0.55*{r2}*ld(2))+25*(1-ld(1)),0,255)"
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=1.0)


def g_gradient_drift(W, H, fps, P, stops):
    w, h, p = W // 8, H // 8, ph(P)
    e = U() + f"clip(127.5+100*sin(PI*(0.6*ld(0)+0.9*ld(1))-{p})+27*sin(2*PI*ld(0)*1.3+{p}),0,255)"
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H)


def g_underwater_rays(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    e = (U() + f"st(2,atan2(Y+0.25*H,X-0.5*W));st(3,pow(0.5+0.5*sin(ld(2)*26+1.4*sin(2*{p}+ld(2)*4)),6));"
         f"clip(40+60*(1-ld(1))+170*ld(3)*exp(-1.8*ld(1))*(0.75+0.25*sin(2*{p}+ld(0)*3)),0,255)")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=1.0)


def g_snowfall(W, H, fps, P, stops):
    w, h = snap(W // 4, 30), snap(H // 4, 30)
    base = per_frame(U() + "clip(30+60*ld(1),0,255)", w, h, fps, P)
    a = texture(particles(15, 0.8, 1.4, 0.35, seed=71, soft=1.0), w, h, fps, P, W, H)
    b = texture(particles(15, 1.4, 2.2, 0.3, seed=73, soft=0.9), w, h, fps, P, W, H)
    c = texture(particles(30, 2.4, 3.6, 0.3, seed=79, soft=0.8), w, h, fps, P, W, H, blur=0.8)
    return (f"{base},scale={W}:{H}[g];{a},{scroll(0, 1, fps, P)}[a];{b},{scroll(0, 2, fps, P)}[b];"
            f"{c},{scroll(0, 3, fps, P)}[c];[a][b]blend=all_mode=lighten[ab];[ab][c]blend=all_mode=lighten[s];"
            f"[g][s]blend=all_mode=lighten," + finish(stops, W, H))


def g_fireflies(W, H, fps, P, stops):
    w, h = snap(W // 4, 30), snap(H // 4, 30)
    a = texture(particles(30, 2.5, 4.5, 0.3, seed=83, soft=0.9), w, h, fps, P, W, H, blur=1.5)
    b = texture(particles(30, 2, 3.5, 0.3, seed=89, soft=0.9), w, h, fps, P, W, H, blur=1.5)
    blink = texture("255*" + tfbm(2, 3, 2, seed=97), w, h, fps, P, W, H)
    return (f"{a},{scroll(1, 1, fps, P)}[a];{b},{scroll(-1, 1, fps, P)}[b];"
            f"[a][b]blend=all_mode=lighten[f];{blink},{scroll(0, -2, fps, P)},eq=contrast=2.2[k];"
            f"[f][k]blend=all_expr='min(255,A*(0.25+B/160))'," + finish(stops, W, H))


def g_blueprint_grid(W, H, fps, P, stops):
    w, h = W // 2, H // 2
    m, M = 12, 60
    e = (f"st(0,X+T/{P}*{M});st(1,Y+T/{P}*{M});"
         f"st(2,min(mod(ld(0),{m}),{m}-mod(ld(0),{m})));st(3,min(mod(ld(1),{m}),{m}-mod(ld(1),{m})));"
         f"st(4,min(mod(ld(0),{M}),{M}-mod(ld(0),{M})));st(5,min(mod(ld(1),{M}),{M}-mod(ld(1),{M})));"
         f"clip(45+60*max(clip(1-ld(2),0,1),clip(1-ld(3),0,1))+150*max(clip(1.6-ld(4),0,1),clip(1.6-ld(5),0,1))"
         f"+20*(1-Y/H),0,255)")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H)


def g_chalkboard_dust(W, H, fps, P, stops):
    w, h = snap(W // 4, 30), snap(H // 4, 30)
    smudge = texture("clip(30+90*" + tfbm(4, 7, 3, seed=101) + ",0,255)", w, h, fps, P, W, H)
    dust = texture(particles(15, 0.6, 1.4, 0.25, seed=103, soft=1.0), w, h, fps, P, W, H)
    return (f"{smudge},{scroll(2, 0, fps, P)}[s];{dust},{scroll(1, -2, fps, P)}[d];[s][d]blend=all_mode=lighten,"
            + finish(stops, W, H, blur=0.5))


def g_halftone_drift(W, H, fps, P, stops):
    c = 12
    w, h, p = snap(W // 2, c), snap(H // 2, c), ph(P)
    e = (f"st(0,X/W);st(1,Y/H);st(2,(floor(X/{c})+0.5)*{c});st(3,(floor(Y/{c})+0.5)*{c});"
         f"st(4,0.5+0.5*sin(2*PI*(ld(0)*1.5+ld(1)*1.0)-{p}));"
         f"255*clip({c}*0.5*(0.12+0.88*ld(4))-hypot(X-ld(2),Y-ld(3))+0.5,0,1)")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H)


def g_topographic_lines(W, H, fps, P, stops):
    w, h, p = W // 2, H // 2, ph(P)
    f = f"sin(2*PI*ld(0)*1.3+1.5*sin(2*PI*ld(1)*1.1+{p}))+cos(2*PI*ld(1)*1.7-{p}+1.2*sin(2*PI*ld(0)*0.9))"
    e = U() + f"st(2,{f});st(3,ld(2)*3-floor(ld(2)*3));st(4,min(ld(3),1-ld(3)));255*exp(-ld(4)*ld(4)/(2*0.03*0.03))"
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=0.4)


def g_smoke_wisps(W, H, fps, P, stops):
    w, h = W // 4, H // 4
    g = warp_graph("clip(255*(" + tfbm(3, 4, 4, seed=111) + "-0.5)*3.2,0,255)", w, h, fps, P, W, H, 0.25, (0, -1))
    return g + "," + finish(stops, W, H, blur=1.5)


def g_silk_waves(W, H, fps, P, stops):
    w, h, p = W // 4, H // 4, ph(P)
    e = (U() + f"st(2,sin(2*PI*(ld(1)*2.2+0.25*sin(2*PI*ld(0)*1.1+{p})+0.12*sin(2*PI*ld(0)*2.7-2*{p}))));"
         f"clip(60+195*pow(0.5+0.5*ld(2),3),0,255)")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=0.6)


def g_crt_scanlines(W, H, fps, P, stops):
    w, h = W // 2, H // 2
    e = (f"st(1,Y/H);st(2,ld(1)-T/{P}-floor(ld(1)-T/{P}));"
         f"clip(30+45*lt(mod(Y,3),1.5)+120*exp(-pow(ld(2)-0.5,2)/(2*0.03*0.03)),0,255)")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, flags="neighbor")


def g_comic_sunburst(W, H, fps, P, stops):
    w, h, p = W // 2, H // 2, ph(P)
    e = f"st(2,atan2(Y-0.42*H,X-0.5*W));255*clip(0.5+4*sin(ld(2)*14+2*{p}),0,1)"
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H)


def g_pixel_sky_parallax(W, H, fps, P, stops):
    w, h = W // 12, H // 12
    e = (U() + f"st(2,0.6+0.05*sin(2*PI*(ld(0)*2+2*T/{P}))+0.02*sin(2*PI*(ld(0)*5+2*T/{P})));"
         f"st(3,0.74+0.05*sin(2*PI*(ld(0)*1.5+4*T/{P}))+0.015*sin(2*PI*(ld(0)*4+4*T/{P})));"
         f"st(4,gt(sin(2*PI*(ld(0)*3+T/{P}))*sin(2*PI*ld(1)*9),0.55)*lt(ld(1),0.42));"
         "if(gt(ld(1),0.92),0,if(gt(ld(1),ld(3)),70,if(gt(ld(1),ld(2)),120,if(ld(4),255,if(lt(ld(1),0.25),200,230)))))")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, flags="neighbor")


def g_lava_blobs(W, H, fps, P, stops):
    w, h, p = W // 8, H // 8, ph(P)
    blobs = [(0.35, 1, 1, 0.0, 0.5, 0.11), (0.4, 2, 1, 1.0, 2.0, 0.09), (0.3, 1, 2, 2.0, 1.0, 0.1),
             (0.38, 3, 1, 3.0, 0.3, 0.08), (0.42, 1, 3, 4.0, 2.5, 0.07)]
    terms = [f"{r * r}/(pow(ld(0)-(0.5+0.35*sin({kx}*{p}+{fx})),2)+pow((ld(1)-(0.5+{ay}*cos({ky}*{p}+{fy})))*H/W,2)+0.0001)"
             for ay, kx, ky, fx, fy, r in blobs]
    e = U() + f"st(2,{'+'.join(terms)});clip(255*(ld(2)-0.8)*1.4,0,200)+55*ld(1)*lt(ld(2),0.8)"
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H, blur=0.6)


def g_vignette_breathe(W, H, fps, P, stops):
    w, h, p = W // 8, H // 8, ph(P)
    e = U() + f"255*pow(clip((hypot(ld(0)-0.5,(ld(1)-0.5)*H/W)/0.75-(0.3+0.06*sin({p})))/0.7,0,1),1.5)"
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H)


def g_lowpoly_facets(W, H, fps, P, stops):
    c = 60
    w, h, p = snap(W // 2, c), snap(H // 2, c), ph(P)
    e = (f"st(0,floor(X/{c}));st(1,floor(Y/{c}));st(2,X/{c}-ld(0));st(3,Y/{c}-ld(1));st(4,gt(ld(2),ld(3)));"
         f"st(5,{_hsh('ld(0)*2+ld(4)', 'ld(1)')});"
         f"clip(50+130*(0.55*ld(5)+0.45*(1-Y/H))+45*sin(2*{p}+ld(5)*6.283),0,255)")
    return per_frame(e, w, h, fps, P) + "," + finish(stops, W, H)


RECIPES = {name[2:]: fn for name, fn in list(globals().items()) if name.startswith("g_")}


def prefix_labels(graph: str, prefix: str) -> str:
    """Rename every [label] in a recipe so several recipes can share one filter graph."""
    return re.sub(r"\[([A-Za-z0-9_]+)\]", lambda m: f"[{prefix}{m.group(1)}]", graph)


def even(n: float) -> int:
    return max(2, int(n) // 2 * 2)


def ramp_stops(bid: str, pid: str | None) -> list:
    """Colour stops for a background, recoloured with a palette when the background allows it."""
    bg = BACKGROUNDS[bid]
    if pid is None or bg["recolor"] == "none":
        return [list(s) for s in bg["stops"]]
    pal = PALETTES[pid]
    if bg["recolor"] == "ramp":
        ramp = pal["ramp"]
        return [[0, ramp[0]], [64, ramp[1]], [128, ramp[2]], [200, ramp[3]], [255, ramp[4]]]
    if bg["recolor"] == "overlay":
        light = pal["colors"]["light"]
        mid = kit.rgb_to_hex(kit.composite(light, (0, 0, 0), 0.5))
        return [[0, "#000000"], [140, mid], [255, light]]
    if bg["recolor"] == "two_tone":
        a, b = pal["gradient"] if bid == "gradient_drift" else (pal["colors"]["background"], pal["colors"]["accent"])
        if bid == "comic_sunburst":
            a, b = pal["colors"]["accent"], pal["colors"]["accent_2"]
        return [[0, a], [255, b]]
    raise ValueError(bg["recolor"])


def background_graph(bid: str, W: int, H: int, pid: str | None = None, fps: int = FPS, P: int = LOOP_S) -> str:
    if bid == "motion_grid_2x2":
        return grid_graph(MOTION["grids"]["even_feathered"], BACKGROUNDS[bid]["cells"], W, H, pid, fps, P)
    return RECIPES[bid](W, H, fps, P, ramp_stops(bid, pid))


def grid_cells_spec(gspec: dict, cells: list[str]) -> list[dict]:
    out = []
    for i in range(4):
        c = {"source": f"bg_layer_{cells[0] if gspec.get('same_source') else cells[i]}", "opacity": gspec["opacity"][i]}
        if gspec.get("mirror"):
            c["mirror"] = gspec["mirror"][i]
        if gspec.get("start_offset_s"):
            c["start_offset_s"] = gspec["start_offset_s"][i]
        if gspec.get("reveal_delay_s"):
            c["reveal_delay_s"] = gspec["reveal_delay_s"][i]
        out.append(c)
    return out


def grid_graph(gspec: dict, cells: list[str], W: int, H: int, pid: str | None = None, fps: int = FPS,
               P: int = LOOP_S) -> str:
    """Self-contained graph: base gradient + four procedural loops in a feathered 2x2 grid -> [out]."""
    rects = kit.grid_2x2_rects(W, H, gspec["gutter_px"], gspec["margin_px"])
    base = prefix_labels(RECIPES["gradient_drift"](W, H, fps, P, ramp_stops("gradient_drift", pid or "house_yellow_night")), "base_")
    parts = [base.replace("[base_out]", "[base_o]")]
    names = [cells[0]] * 4 if gspec.get("same_source") else cells
    for i, (rect, name) in enumerate(zip(rects, names)):
        _, _, cw, ch = rect
        sub = prefix_labels(RECIPES[name](even(cw), even(ch), fps, P, ramp_stops(name, None)), f"c{i}_")
        parts.append(sub)
        if gspec.get("same_source"):
            break
    if gspec.get("same_source"):
        parts.append("[c0_out]split=4[c0s][c1s][c2s][c3s]")
        inputs = ("c0s", "c1s", "c2s", "c3s")
    else:
        inputs = ("c0_out", "c1_out", "c2_out", "c3_out")
    grid = {"gutter_px": gspec["gutter_px"], "margin_px": gspec["margin_px"], "feather_px": gspec["feather_px"],
            "corner_radius_px": gspec["corner_radius_px"], "cells": grid_cells_spec(gspec, cells)}
    parts.append(kit.grid_2x2_filter(grid, W, H, fps, base_label="base_o", inputs=inputs, out_label="gridv"))
    parts.append("[gridv]format=yuv420p[out]")
    return ";".join(parts)


def render_cmd(out_name: str, seconds: int = LOOP_S, graph_file: str = "filtergraph.txt") -> str:
    return (f'ffmpeg -y -filter_complex "$(cat {graph_file})" -map "[out]" -t {seconds} -r {FPS} \\\n'
            f"  -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -movflags +faststart {out_name}")


# --------------------------------------------------------------------------- schemas

HEX = {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"}
OPACITY = {"type": "number", "minimum": 0, "maximum": 0.98}
FRACTION = {"type": "number", "minimum": 0, "maximum": 1}
IDENT = {"type": "string", "pattern": "^[a-z][a-z0-9]*(_[a-z0-9]+)*$"}
EASINGS = ["linear", "ease-in", "ease-out", "ease-in-out", "sine-in-out", "ease-out-back", "ease-out-elastic", "step"]
BLENDS = sorted(kit.BLEND_MODES)


def defs() -> dict:
    return {
        "hex": HEX,
        "opacity": dict(OPACITY, description="Layer or panel opacity. House rule: nothing above 0.98."),
        "fraction": FRACTION,
        "identity": IDENT,
        "easing": {"oneOf": [{"enum": EASINGS},
                             {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4,
                              "description": "cubic-bezier(x1, y1, x2, y2)"}]},
        "blend": {"enum": BLENDS},
        "font": {
            "type": "object", "additionalProperties": False,
            "required": ["family", "weight", "licence", "file_url"],
            "properties": {
                "family": {"type": "string", "minLength": 2},
                "weight": {"type": "integer", "minimum": 100, "maximum": 1000},
                "size_px": {"type": "number", "minimum": 8, "maximum": 400},
                "min_size_px": {"type": "number", "minimum": 8, "maximum": 400},
                "case": {"enum": ["as-written", "upper", "lower", "title"]},
                "letter_spacing_em": {"type": "number", "minimum": -0.1, "maximum": 0.5},
                "licence": {"enum": ["OFL-1.1", "Apache-2.0"]},
                "file_url": {"type": "string", "pattern": "^https://raw\\.githubusercontent\\.com/google/fonts/main/"},
                "licence_url": {"type": "string", "pattern": "^https://raw\\.githubusercontent\\.com/google/fonts/main/"},
                "specimen_url": {"type": "string", "pattern": "^https://fonts\\.google\\.com/specimen/"},
                "avg_char_em": {"type": "number", "minimum": 0.2, "maximum": 1.2},
                "variable_axes": {"type": "object"},
            },
        },
        "contrast": {
            "type": "object", "additionalProperties": False,
            "required": ["basis", "fg", "bg", "ratio", "required"],
            "properties": {
                "basis": {"enum": ["panel-worst-case", "stroke", "solid"],
                          "description": "panel-worst-case: fg over a bg-tinted panel at `opacity` over any video (worst of black/white beneath)."},
                "fg": HEX, "bg": HEX, "opacity": OPACITY,
                "ratio": {"type": "number", "minimum": 3.0, "maximum": 21.0},
                "required": {"enum": [3.0, 4.5]},
                "size_px": {"type": "number"}, "weight": {"type": "integer"},
                "level": {"enum": ["AA", "AAA"]},
                "stroke_px": {"type": "number"},
            },
            "allOf": [
                {"if": {"properties": {"required": {"const": 4.5}}}, "then": {"properties": {"ratio": {"minimum": 4.5}}}},
                {"if": {"properties": {"basis": {"const": "panel-worst-case"}}}, "then": {"required": ["opacity"]}},
            ],
        },
        "margins": {
            "type": "object", "additionalProperties": False, "required": ["top", "bottom", "left", "right"],
            "properties": {k: {"type": "number", "minimum": 0, "maximum": 0.5} for k in ("top", "bottom", "left", "right")},
        },
        "target": {
            "type": "object", "additionalProperties": False,
            "required": ["id", "platform", "aspect", "width", "height", "safe_margins"],
            "properties": {
                "id": {"type": "string"}, "label": {"type": "string"},
                "platform": {"enum": ["generic", "youtube-shorts", "instagram-reels", "tiktok", "instagram-feed", "youtube"]},
                "aspect": {"enum": ["9:16", "4:5", "1:1", "16:9"]},
                "width": {"type": "integer", "minimum": 256, "maximum": 4096},
                "height": {"type": "integer", "minimum": 256, "maximum": 4096},
                "safe_margins": {"$ref": "#/$defs/margins"},
                "margins_basis": {"type": "string"},
            },
        },
        "motion": {
            "type": "object", "additionalProperties": True, "required": ["type"],
            "properties": {"type": {"enum": ["static", "loop", "drift", "scroll", "pan", "zoom", "rotate", "parallax",
                                             "rise", "fall", "sway", "pulse", "follow", "keyframed", "ken-burns",
                                             "punch-in"]},
                           "period_s": {"type": "number", "exclusiveMinimum": 0}},
        },
    }


def schema(name: str, title: str, description: str, required: list, properties: dict, all_of=None, extra=None) -> dict:
    s = {"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": SCHEMA_URL + name, "title": title,
         "description": description, "type": "object", "additionalProperties": False,
         "required": ["type", "id", "name", "version"] + required,
         "properties": {"id": {"$ref": "#/$defs/identity"}, "name": {"type": "string", "minLength": 3},
                        "version": {"type": "integer", "minimum": 1}, "notes": {"type": "string"},
                        "variant": {"type": "object", "description": "Present on variants: base identity and what changed."},
                        **properties},
         "$defs": defs()}
    if all_of:
        s["allOf"] = all_of
    if extra:
        s.update(extra)
    return s


BACKING_TYPES = ["frosted-glass", "solid", "pill", "scrim", "sticker", "none"]
BACKING = {
    "type": "object", "additionalProperties": False, "required": ["type"],
    "properties": {"type": {"enum": BACKING_TYPES}, "tint": {"$ref": "#/$defs/hex"}, "opacity": {"$ref": "#/$defs/opacity"},
                   "blur_px": {"type": "number", "minimum": 0, "maximum": 120}, "radius_px": {"type": "number", "minimum": 0, "maximum": 999},
                   "padding_px": {"type": "array", "items": {"type": "number", "minimum": 0}, "minItems": 2, "maxItems": 2},
                   "feather_px": {"type": "number", "minimum": 0, "maximum": 200},
                   "rotation_deg": {"type": "number", "minimum": -15, "maximum": 15},
                   "full_width": {"type": "boolean"}, "shape": {"enum": ["rounded-rect", "starburst"]}},
    "allOf": [{"if": {"properties": {"type": {"const": "frosted-glass"}}},
               "then": {"required": ["tint", "opacity", "blur_px"], "properties": {"blur_px": {"minimum": 8}}}},
              {"if": {"properties": {"type": {"enum": ["solid", "pill", "scrim", "sticker"]}}},
               "then": {"required": ["tint", "opacity"]}}],
}
STROKE = {"type": "object", "additionalProperties": False, "required": ["color", "width_px"],
          "properties": {"color": {"$ref": "#/$defs/hex"}, "width_px": {"type": "number", "minimum": 0, "maximum": 40}}}
SHADOW = {"type": "object", "additionalProperties": False,
          "properties": {"color": {"$ref": "#/$defs/hex"}, "opacity": {"$ref": "#/$defs/opacity"},
                         "blur_px": {"type": "number", "minimum": 0, "maximum": 80},
                         "offset_px": {"type": "array", "items": {"type": "number"}, "minItems": 2, "maxItems": 2}}}
TARGET_REF = {"$ref": "#/$defs/target"}
REF_SIZE = {"type": "array", "items": {"type": "integer", "minimum": 256}, "minItems": 2, "maxItems": 2}
STR_LIST = {"type": "array", "items": {"type": "string"}}

SCHEMAS: dict[str, dict] = {}

SCHEMAS["caption-style"] = schema(
    "caption-style-preset-schema", "Caption style preset",
    "One synced caption line style for vertical video: font, fill, outline, backing panel, layout inside a platform safe area, keyword emphasis, timing and measured WCAG contrast.",
    ["font", "fill", "backing", "layout", "emphasis", "timing", "contrast", "target"],
    {"type": {"const": "caption-style"}, "house": {"type": "boolean"},
     "font": {"$ref": "#/$defs/font"}, "fill": {"$ref": "#/$defs/hex"}, "stroke": STROKE, "shadow": SHADOW,
     "backing": BACKING,
     "layout": {"type": "object", "additionalProperties": False,
                "required": ["center_y_fraction", "max_width_fraction", "max_lines", "max_words", "max_chars", "align"],
                "properties": {"center_y_fraction": FRACTION, "max_width_fraction": {"type": "number", "minimum": 0.3, "maximum": 1},
                               "max_lines": {"type": "integer", "minimum": 1, "maximum": 3},
                               "max_words": {"type": "integer", "minimum": 1, "maximum": 16},
                               "max_chars": {"type": "integer", "minimum": 4, "maximum": 80},
                               "align": {"enum": ["center", "left", "right"]}}},
     "emphasis": {"type": "object", "additionalProperties": False, "required": ["mode"],
                  "properties": {"mode": {"enum": ["keyword-pop", "color", "box-current-word", "box-keyword", "underline", "glow", "none"]},
                                 "color": {"$ref": "#/$defs/hex"}, "text_color": {"$ref": "#/$defs/hex"},
                                 "box_opacity": {"$ref": "#/$defs/opacity"},
                                 "scale_peak": {"type": "number", "minimum": 1, "maximum": 1.5},
                                 "duration_ms": {"type": "number", "minimum": 0, "maximum": 2000}, "easing": {"$ref": "#/$defs/easing"}}},
     "timing": {"type": "object", "additionalProperties": False, "required": ["sync_tolerance_ms"],
                "properties": {"sync_tolerance_ms": {"type": "number", "minimum": 0, "maximum": 300},
                               "min_on_screen_ms": {"type": "number", "minimum": 0}, "max_on_screen_ms": {"type": "number", "minimum": 0}}},
     "animation_in": {"$ref": "#/$defs/identity"}, "keyword_animation": {"$ref": "#/$defs/identity"},
     "palette": {"$ref": "#/$defs/identity"},
     "contrast": {"type": "object", "required": ["text"], "additionalProperties": {"$ref": "#/$defs/contrast"}},
     "target": TARGET_REF, "reference_size": REF_SIZE,
     "use_when": STR_LIST, "avoid_when": STR_LIST, "forbid": STR_LIST},
    all_of=[{"if": {"properties": {"house": {"const": True}}, "required": ["house"]},
             "then": {"properties": {"backing": {"properties": {"type": {"const": "frosted-glass"},
                                                                 "opacity": {"minimum": 0.55, "maximum": 0.75}}},
                                     "layout": {"properties": {"max_lines": {"const": 1}, "max_words": {"maximum": 7}}},
                                     "timing": {"properties": {"sync_tolerance_ms": {"maximum": 150}}}}}},
            {"if": {"properties": {"backing": {"properties": {"type": {"const": "none"}}}}},
             "then": {"required": ["stroke"], "properties": {"stroke": {"properties": {"width_px": {"minimum": 4}}}}}}])

SCHEMAS["title-style"] = schema(
    "title-style-preset-schema", "Title and label style preset",
    "Hook title or item label for vertical video: font, colours, backing, position over the photo, first-frame timing and measured contrast. House titles are #FFD21F, centred no lower than 40% of the height, visible on frame 0, with a 55-75% frosted backing.",
    ["font", "fill", "backing", "position", "text", "timing", "contrast", "target"],
    {"type": {"const": "title-style"}, "house": {"type": "boolean"}, "label_house": {"type": "boolean"},
     "font": {"$ref": "#/$defs/font"}, "fill": {"$ref": "#/$defs/hex"}, "stroke": STROKE, "shadow": SHADOW, "backing": BACKING,
     "position": {"type": "object", "additionalProperties": False, "required": ["region", "center_y_fraction", "over", "max_width_fraction"],
                  "properties": {"region": {"enum": ["upper-third", "center", "lower-third-bar", "top-left"]},
                                 "center_y_fraction": FRACTION, "over": {"enum": ["photo", "background", "panel"]},
                                 "max_width_fraction": {"type": "number", "minimum": 0.2, "maximum": 1},
                                 "never_move_photo": {"type": "boolean"}}},
     "text": {"type": "object", "additionalProperties": False, "required": ["min_words", "max_words", "max_lines"],
              "properties": {"template": {"type": "string"}, "min_words": {"type": "integer", "minimum": 1},
                             "max_words": {"type": "integer", "minimum": 1, "maximum": 30},
                             "max_lines": {"type": "integer", "minimum": 1, "maximum": 4},
                             "max_chars_per_line": {"type": "integer", "minimum": 2, "maximum": 80},
                             "ends_with": {"type": "string"}}},
     "secondary": {"type": "object"},
     "timing": {"type": "object", "additionalProperties": False, "required": ["first_frame", "hold_s"],
                "properties": {"first_frame": {"type": "boolean"}, "hold_s": {"type": "number", "minimum": 0.5, "maximum": 10}}},
     "animation_in": {"$ref": "#/$defs/identity"}, "palette": {"$ref": "#/$defs/identity"},
     "contrast": {"type": "object", "required": ["title"], "additionalProperties": {"$ref": "#/$defs/contrast"}},
     "target": TARGET_REF, "reference_size": REF_SIZE, "use_when": STR_LIST, "avoid_when": STR_LIST},
    all_of=[{"if": {"properties": {"house": {"const": True}}, "required": ["house"]},
             "then": {"properties": {"fill": {"const": "#FFD21F"},
                                     "font": {"properties": {"weight": {"minimum": 700}}},
                                     "position": {"properties": {"center_y_fraction": {"maximum": 0.40}, "over": {"const": "photo"}}},
                                     "timing": {"properties": {"first_frame": {"const": True}}},
                                     "backing": {"properties": {"type": {"const": "frosted-glass"},
                                                                "opacity": {"minimum": 0.55, "maximum": 0.75}}}}}}])

SCHEMAS["background-layer"] = schema(
    "background-layer-preset-schema", "Background layer preset",
    "A moving background or overlay layer that renders procedurally with ffmpeg (seamless loop) and, for footage-first layers, says how to find licensed footage.",
    ["category", "role", "render", "default_opacity", "default_blend", "motion"],
    {"type": {"const": "background-layer"}, "category": {"enum": ["footage", "procedural-light", "procedural-texture", "procedural-particles",
                                                                   "procedural-scene", "overlay", "composite"]},
     "role": {"enum": ["base", "background-video", "texture", "light", "particles", "haze", "grain", "vignette", "overlay", "grid-2x2"]},
     "look": {"type": "string"},
     "render": {"type": "object", "additionalProperties": False,
                "required": ["method", "width", "height", "fps", "loop_period_s", "filtergraph_file"],
                "properties": {"method": {"enum": ["ffmpeg-lavfi", "ffmpeg-composite"]}, "width": {"type": "integer"}, "height": {"type": "integer"},
                               "fps": {"type": "integer", "minimum": 1, "maximum": 120}, "loop_period_s": {"type": "number", "minimum": 1},
                               "filtergraph_file": {"type": "string"}, "filtergraph_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                               "colour_stops": {"type": "array", "items": {"type": "array", "prefixItems": [{"type": "integer", "minimum": 0, "maximum": 255}, {"$ref": "#/$defs/hex"}], "minItems": 2, "maxItems": 2}},
                               "tested_with": {"type": "string"}}},
     "footage": {"type": "object", "additionalProperties": False, "required": ["search_terms", "sources", "accepted_licences"],
                 "properties": {"search_terms": STR_LIST, "prefer": {"type": "string"},
                                "sources": {"type": "array", "items": {"type": "object", "required": ["name", "url"],
                                                                         "properties": {"name": {"type": "string"}, "url": {"type": "string", "format": "uri"},
                                                                                        "terms_url": {"type": "string", "format": "uri"}, "note": {"type": "string"}}}},
                                "accepted_licences": STR_LIST, "rejected_licences": STR_LIST, "record": STR_LIST}},
     "default_opacity": {"$ref": "#/$defs/opacity"}, "default_blend": {"$ref": "#/$defs/blend"},
     "motion": {"$ref": "#/$defs/motion"}, "recolor": {"enum": ["ramp", "overlay", "two_tone", "none"]},
     "palette": {"$ref": "#/$defs/identity"}, "grid": {"type": "object"}, "use_when": STR_LIST, "target": TARGET_REF},
    all_of=[{"if": {"properties": {"category": {"const": "footage"}}}, "then": {"required": ["footage"]}}])

LAYER_ROLES = ["base", "background-video", "background-image", "grid-2x2", "texture", "light", "particles", "haze", "grain",
               "vignette", "overlay", "shadow", "photo", "panel", "title", "caption", "label", "number", "transition", "grade"]
BG_ROLES = ["base", "background-video", "background-image", "grid-2x2", "texture", "light", "particles", "haze", "grain", "vignette", "overlay"]
SCHEMAS["layer-stack"] = schema(
    "layer-stack-preset-schema", "Layer stack preset",
    "An ordered stack of 5-64 layers (bottom to top) with role, source, opacity (<= 0.98), blend mode and motion. At least one background layer must move; a photo layer keeps at least 80% of the frame width.",
    ["canvas", "layers", "rules"],
    {"type": {"const": "layer-stack"}, "house": {"type": "boolean"}, "summary": {"type": "string"},
     "canvas": {"type": "object", "additionalProperties": False, "required": ["width", "height", "fps"],
                "properties": {"width": {"type": "integer"}, "height": {"type": "integer"}, "fps": {"type": "integer"}}},
     "theme": {"type": "string"}, "palette": {"$ref": "#/$defs/identity"}, "target": TARGET_REF,
     "layers": {"type": "array", "minItems": 5, "maxItems": 64,
                "items": {"type": "object", "additionalProperties": False, "required": ["z", "id", "role", "source", "opacity", "blend", "motion"],
                          "properties": {"z": {"type": "integer", "minimum": 1}, "id": {"type": "string", "pattern": "^[a-z][a-z0-9_]*$"},
                                         "role": {"enum": LAYER_ROLES},
                                         "source": {"type": "object", "required": ["kind", "ref"],
                                                    "properties": {"kind": {"enum": ["component", "asset", "palette-colour", "effect", "grade"]},
                                                                   "ref": {"type": "string"}, "cells": {"type": "array"}}},
                                         "opacity": {"$ref": "#/$defs/opacity"}, "blend": {"$ref": "#/$defs/blend"},
                                         "motion": {"$ref": "#/$defs/motion"},
                                         "rect": {"type": "object", "additionalProperties": False, "required": ["x", "y", "w", "h"],
                                                  "properties": {k: FRACTION for k in ("x", "y", "w", "h")}},
                                         "feather_px": {"type": "number", "minimum": 0, "maximum": 200},
                                         "corner_radius_px": {"type": "number", "minimum": 0},
                                         "opacity_keyframes": {"type": "array", "items": {"type": "array", "prefixItems": [{"type": "number", "minimum": 0}, {"$ref": "#/$defs/opacity"}], "minItems": 2, "maxItems": 2}},
                                         "details": {"type": "object"}},
                          "allOf": [{"if": {"properties": {"role": {"const": "photo"}}, "required": ["rect"]},
                                     "then": {"properties": {"rect": {"properties": {"w": {"minimum": 0.8}}}}}}]},
                "contains": {"type": "object", "required": ["role", "motion"],
                             "properties": {"role": {"enum": BG_ROLES}, "motion": {"properties": {"type": {"not": {"const": "static"}}}}}}},
     "rules": {"type": "object", "required": ["max_layer_opacity", "min_layers"],
               "properties": {"max_layer_opacity": {"const": 0.98}, "min_layers": {"type": "integer", "minimum": 5}}},
     "effects": {"type": "object", "additionalProperties": {"type": "string"}},
     "background_render": {"type": "object"}})

SCHEMAS["grid-system"] = schema(
    "grid-2x2-preset-schema", "2x2 motion grid preset",
    "Four moving sources in a 2x2 grid with gutter, margin, feathered rounded cells, per-cell opacity (<= 0.98), mirroring, start offsets and reveal delays.",
    ["rows", "cols", "gutter_px", "margin_px", "feather_px", "corner_radius_px", "cells", "placement", "canvas"],
    {"type": {"const": "grid-system"}, "rows": {"const": 2}, "cols": {"const": 2},
     "gutter_px": {"type": "number", "minimum": 0, "maximum": 200}, "margin_px": {"type": "number", "minimum": 0, "maximum": 400},
     "feather_px": {"type": "number", "minimum": 0, "maximum": 200}, "corner_radius_px": {"type": "number", "minimum": 0, "maximum": 400},
     "cells": {"type": "array", "minItems": 4, "maxItems": 4,
               "items": {"type": "object", "additionalProperties": False, "required": ["source", "opacity"],
                         "properties": {"source": {"type": "string"}, "opacity": {"$ref": "#/$defs/opacity"},
                                        "mirror": {"enum": ["", "h", "v", "hv"]}, "start_offset_s": {"type": "number", "minimum": 0},
                                        "reveal_delay_s": {"type": "number", "minimum": 0}, "view": {"type": "string"}}}},
     "placement": {"type": "object", "additionalProperties": False, "required": ["as", "blend"],
                   "properties": {"as": {"enum": ["background-layer", "main-content"]}, "blend": {"$ref": "#/$defs/blend"},
                                  "layer_opacity": {"$ref": "#/$defs/opacity"}}},
     "canvas": {"type": "object", "required": ["width", "height", "fps"]},
     "rects": {"type": "array", "items": {"type": "array", "items": {"type": "integer"}, "minItems": 4, "maxItems": 4}, "minItems": 4, "maxItems": 4},
     "render": {"type": "object"}, "cell_set": {"type": "string"}, "target": TARGET_REF, "use_when": STR_LIST})

SCHEMAS["transition"] = schema(
    "transition-preset-schema", "Transition preset",
    "A cut or ffmpeg xfade transition with duration and tempo, optionally combined with an overlay pulse (e.g. light leak) whose peak opacity stays <= 0.98.",
    ["method", "duration_ms", "tempo"],
    {"type": {"const": "transition"}, "method": {"enum": ["cut", "xfade", "xfade+overlay"]},
     "xfade": {"enum": sorted(kit.XFADE_TRANSITIONS)}, "duration_ms": {"type": "number", "minimum": 0, "maximum": 3000},
     "tempo": {"enum": ["snappy", "standard", "slow"]},
     "overlay": {"type": "object", "additionalProperties": False, "required": ["source", "peak_opacity", "blend"],
                 "properties": {"source": {"$ref": "#/$defs/identity"}, "peak_opacity": {"$ref": "#/$defs/opacity"},
                                "blend": {"$ref": "#/$defs/blend"}, "ramp_ms": {"type": "number"}}},
     "ffmpeg": {"type": "object"}, "min_ffmpeg": {"type": "string"}, "use_when": STR_LIST, "avoid_when": STR_LIST},
    all_of=[{"if": {"properties": {"method": {"const": "cut"}}}, "then": {"properties": {"duration_ms": {"const": 0}}}},
            {"if": {"properties": {"method": {"enum": ["xfade", "xfade+overlay"]}}},
             "then": {"required": ["xfade"], "properties": {"duration_ms": {"minimum": 40}}}}])

SCHEMAS["camera-move"] = schema(
    "camera-move-preset-schema", "Camera move preset",
    "A virtual camera move over a still or layered image: zoom and centre paths (fractions of the source), optional rotation, punch-in keyframes, shake or parallax layers, with the renderer that supports it.",
    ["kind", "duration_s", "zoom", "center", "easing", "renderer", "output"],
    {"type": {"const": "camera-move"},
     "kind": {"enum": ["ken-burns", "push-in", "pull-back", "pan", "tilt", "drift", "whip", "punch-in", "rotate", "shake",
                       "parallax-dolly", "alternating"]},
     "duration_s": {"type": "number", "minimum": 0.1, "maximum": 60},
     "zoom": {"type": "object", "required": ["from", "to"], "properties": {"from": {"type": "number", "minimum": 1, "maximum": 4}, "to": {"type": "number", "minimum": 1, "maximum": 4}}},
     "center": {"type": "object", "required": ["from", "to"],
                "properties": {"from": {"type": "array", "items": FRACTION, "minItems": 2, "maxItems": 2},
                               "to": {"type": "array", "items": FRACTION, "minItems": 2, "maxItems": 2}}},
     "rotation_deg": {"type": "object", "properties": {"from": {"type": "number", "minimum": -15, "maximum": 15}, "to": {"type": "number", "minimum": -15, "maximum": 15}}},
     "easing": {"$ref": "#/$defs/easing"},
     "zoom_keyframes": {"type": "array", "items": {"type": "object", "required": ["t", "zoom"]}},
     "shake": {"type": "object", "properties": {"amplitude": {"type": "number", "minimum": 0, "maximum": 0.05}, "frequency_hz": {"type": "number", "minimum": 0.05, "maximum": 15}}},
     "layers": {"type": "array", "items": {"type": "object", "required": ["name", "speed"]}},
     "pair": {"type": "object"}, "motion_blur": {"type": "string"},
     "renderer": {"enum": ["zoompan", "pillow", "overlay-expr"]}, "prescale": {"type": "integer", "minimum": 1, "maximum": 8},
     "output": {"type": "object", "required": ["width", "height", "fps"]}, "ffmpeg": {"type": "object"},
     "intensity": {"enum": ["subtle", "standard", "strong"]}, "target": TARGET_REF, "use_when": STR_LIST},
    all_of=[{"if": {"properties": {"renderer": {"const": "zoompan"}}},
             "then": {"not": {"anyOf": [{"required": ["rotation_deg"]}, {"required": ["shake"]}]}}}])

TEXT_PROPS = {"t": FRACTION, "scale": {"type": "number", "minimum": 0, "maximum": 4},
              "opacity": {"type": "number", "minimum": 0, "maximum": 1, "description": "Multiplier of the text layer's own opacity (itself <= 0.98)."},
              "dx_px": {"type": "number"}, "dy_px": {"type": "number"}, "rotation_deg": {"type": "number", "minimum": -45, "maximum": 45},
              "blur_px": {"type": "number", "minimum": 0, "maximum": 40}, "reveal": FRACTION, "ease": {"enum": EASINGS}}
SCHEMAS["text-animation"] = schema(
    "text-animation-preset-schema", "Text animation preset",
    "How text enters or emphasises: per text, line, word or character, with keyframes or a damped spring (stiffness, damping, mass) and the spring's computed overshoot and settle time.",
    ["unit", "duration_ms", "stagger_ms", "tempo"],
    {"type": {"const": "text-animation"}, "unit": {"enum": ["text", "line", "word", "character"]},
     "duration_ms": {"type": "number", "minimum": 1, "maximum": 5000}, "stagger_ms": {"type": "number", "minimum": 0, "maximum": 2000},
     "tempo": {"enum": ["snappy", "standard", "gentle"]},
     "keyframes": {"type": "array", "minItems": 2, "items": {"type": "object", "additionalProperties": False, "required": ["t"], "properties": TEXT_PROPS}},
     "spring": {"type": "object", "additionalProperties": False, "required": ["stiffness", "damping"],
                "properties": {"stiffness": {"type": "number", "exclusiveMinimum": 0}, "damping": {"type": "number", "exclusiveMinimum": 0},
                               "mass": {"type": "number", "exclusiveMinimum": 0}}},
     "spring_metrics": {"type": "object"}, "from": {"type": "object"}, "to": {"type": "object"},
     "count": {"type": "object", "required": ["from", "easing"]}, "shake": {"type": "object"},
     "samples": {"type": "array"}, "ffmpeg": {"type": "object"}, "timing_source": {"type": "string"},
     "applies_to": {"type": "string"}, "use_when": STR_LIST},
    extra={"oneOf": [{"required": ["keyframes"]}, {"required": ["spring", "from", "to"]}]})

PAIR = {"type": "object", "additionalProperties": False,
        "required": ["fg_role", "bg_role", "fg", "bg", "basis", "ratio", "required", "use"],
        "properties": {"fg_role": {"type": "string"}, "bg_role": {"type": "string"}, "fg": {"$ref": "#/$defs/hex"}, "bg": {"$ref": "#/$defs/hex"},
                       "basis": {"enum": ["panel-worst-case", "solid"]}, "opacity": {"$ref": "#/$defs/opacity"},
                       "ratio": {"type": "number", "minimum": 3.0}, "required": {"enum": [3.0, 4.5]},
                       "use": {"enum": ["any-size", "large-bold-only"]}, "min_size_px": {"type": "number"}, "min_weight": {"type": "integer"},
                       "level": {"type": "string"}},
        "allOf": [{"if": {"properties": {"use": {"const": "any-size"}}}, "then": {"properties": {"ratio": {"minimum": 4.5}, "required": {"const": 4.5}}}},
                  {"if": {"properties": {"use": {"const": "large-bold-only"}}},
                   "then": {"required": ["min_size_px", "min_weight"], "properties": {"min_size_px": {"minimum": 24}, "min_weight": {"minimum": 700}}}}]}
SCHEMAS["palette"] = schema(
    "palette-preset-schema", "Palette preset",
    "Named colour roles for a look plus every text/background pair that passes WCAG contrast (4.5:1, or 3:1 restricted to >= 24 px bold text), measured worst-case over unknown video for semi-transparent panels.",
    ["mode", "colors", "panel_opacity", "ramp", "pairs"],
    {"type": {"const": "palette"}, "mode": {"enum": ["dark", "light"]},
     "colors": {"type": "object", "additionalProperties": False,
                "required": ["background", "surface", "panel_tint", "text", "title", "keyword", "accent", "accent_2", "stroke", "light", "particle"],
                "properties": {k: {"$ref": "#/$defs/hex"} for k in ("background", "surface", "panel_tint", "text", "title", "keyword", "accent",
                                                                      "accent_2", "stroke", "light", "particle")}},
     "panel_opacity": {"$ref": "#/$defs/opacity"}, "gradient": {"type": "array", "items": {"$ref": "#/$defs/hex"}, "minItems": 2, "maxItems": 2},
     "ramp": {"type": "array", "items": {"$ref": "#/$defs/hex"}, "minItems": 5, "maxItems": 5},
     "pairs": {"type": "array", "minItems": 3, "items": PAIR}, "failed_pair_count": {"type": "integer", "minimum": 0},
     "mood": STR_LIST, "source": {"type": "object", "required": ["name", "url"]}})

FONT_SLOT = {"type": "object", "additionalProperties": False, "required": ["family", "weight", "licence", "file_url", "licence_url", "specimen_url"],
             "properties": {"family": {"type": "string"}, "weight": {"type": "integer", "minimum": 100, "maximum": 1000},
                            "licence": {"enum": ["OFL-1.1", "Apache-2.0"]}, "file": {"type": "string"},
                            "file_url": {"type": "string", "pattern": "^https://raw\\.githubusercontent\\.com/google/fonts/main/"},
                            "licence_url": {"type": "string", "pattern": "^https://raw\\.githubusercontent\\.com/google/fonts/main/"},
                            "specimen_url": {"type": "string", "pattern": "^https://fonts\\.google\\.com/specimen/"},
                            "case": {"enum": ["as-written", "upper", "lower", "title"]}, "variable_axes": {"type": "object"},
                            "avg_char_em": {"type": "number"}, "category": {"type": "string"}}}
SCHEMAS["typography"] = schema(
    "typography-pairing-schema", "Typography pairing preset",
    "Display, caption and number fonts (OFL-1.1 or Apache-2.0 only, from Google Fonts) with sizes, measured average glyph widths and characters per line for a target frame.",
    ["display", "text", "sizes", "chars_per_line", "target"],
    {"type": {"const": "typography"}, "display": FONT_SLOT, "text": FONT_SLOT, "numbers": FONT_SLOT,
     "sizes": {"type": "object", "required": ["title_px", "caption_px", "min_caption_px", "label_px", "number_px"]},
     "chars_per_line": {"type": "object", "required": ["title", "caption"]}, "target": TARGET_REF, "mood": STR_LIST, "why": {"type": "string"}})

SCHEMAS["animation-style"] = schema(
    "animation-style-preset-schema", "Animation style preset",
    "A production look (projection, camera angles, shading, outlines, frame timing, palette limits) with recipes for open-source tools and the topics it suits.",
    ["projection", "camera", "shading", "timing", "recipe", "best_for", "render"],
    {"type": {"const": "animation-style"},
     "projection": {"enum": ["orthographic-top", "orthographic-side", "isometric", "dimetric-2to1", "perspective", "layered-2.5d", "multi-view"]},
     "camera": {"type": "object", "required": ["elevation_deg", "azimuth_deg", "orthographic"]},
     "shading": {"enum": ["flat", "cel-2-tone", "cel-3-tone", "soft-clay", "textured-paper", "line-only", "voxel-flat", "pbr-soft"]},
     "outline": {"type": "object"}, "timing": {"type": "object", "required": ["render_fps", "animate_on"],
                                                 "properties": {"render_fps": {"type": "integer"}, "animate_on": {"enum": ["ones", "twos", "threes"]}}},
     "palette": {"type": "object"}, "layers": {"type": "array"}, "views": STR_LIST, "best_for": STR_LIST, "avoid": STR_LIST,
     "look": {"type": "string"}, "recipe": STR_LIST, "pitfalls": STR_LIST, "tools": STR_LIST,
     "render": {"type": "object", "required": ["width", "height"]}, "topic": {"type": "object"}, "suggested": {"type": "object"},
     "target": TARGET_REF})

SCHEMAS["aspect-format"] = schema(
    "aspect-format-preset-schema", "Aspect format preset",
    "Frame size, platform, conservative safe margins (with their basis), title/caption zones, photo rectangle and export encoding settings.",
    ["aspect", "width", "height", "platform", "safe_margins", "zones", "encoding"],
    {"type": {"const": "aspect-format"}, "aspect": {"enum": ["9:16", "4:5", "1:1", "16:9"]},
     "width": {"type": "integer"}, "height": {"type": "integer"},
     "platform": {"enum": ["generic", "youtube-shorts", "instagram-reels", "tiktok", "instagram-feed", "youtube"]},
     "safe_margins": {"$ref": "#/$defs/margins"}, "margins_basis": {"type": "string"}, "margins_verified": {"type": "boolean"},
     "safe_rect_px": {"type": "array", "items": {"type": "integer"}, "minItems": 4, "maxItems": 4},
     "zones": {"type": "object", "required": ["title_center_y", "caption_center_y", "photo_rect"]},
     "encoding": {"type": "object", "required": ["video_codec", "pix_fmt", "fps", "audio_codec", "audio_rate_hz", "ffmpeg_args", "source"]},
     "duration": {"type": "object"}, "use": {"type": "string"}})

SCHEMAS["thumbnail-style"] = schema(
    "thumbnail-style-preset-schema", "Thumbnail style preset",
    "Thumbnail or cover layout: size, text limits and font, panel, subject placement, measured contrast and export limits.",
    ["target", "text", "panel", "layout", "contrast", "export"],
    {"type": {"const": "thumbnail-style"},
     "target": {"type": "object", "required": ["id", "width", "height"]},
     "text": {"type": "object", "required": ["max_words", "font", "size_px", "fill"]},
     "panel": {"type": "object", "required": ["type"]}, "layout": {"type": "object"},
     "contrast": {"type": "object", "required": ["text"], "additionalProperties": {"$ref": "#/$defs/contrast"}},
     "export": {"type": "object", "required": ["format", "quality"]}, "palette": {"$ref": "#/$defs/identity"}, "use_when": STR_LIST})

SCHEMAS["style-preset"] = schema(
    "short-style-preset-schema", "Whole-look style preset",
    "A named look that combines caption, title, label, layer stack, palette, typography, text animations, camera moves, transitions and thumbnail presets, with pacing and the standing house rules.",
    ["components", "pacing", "rules", "target", "use_for"],
    {"type": {"const": "style-preset"}, "house": {"type": "boolean"}, "use_for": STR_LIST, "avoid": STR_LIST,
     "components": {"type": "object", "additionalProperties": False,
                    "required": ["palette", "typography", "caption_style", "title_style", "layer_stack", "text_in", "keyword", "camera_moves", "transitions", "thumbnail"],
                    "properties": {"palette": IDENT, "typography": IDENT, "caption_style": IDENT, "title_style": IDENT, "label_style": IDENT,
                                   "layer_stack": IDENT, "text_in": IDENT, "keyword": IDENT,
                                   "camera_moves": {"type": "array", "items": IDENT, "minItems": 1},
                                   "transitions": {"type": "array", "items": IDENT, "minItems": 1}, "thumbnail": IDENT,
                                   "animation_style": IDENT, "aspect_format": IDENT, "stack_theme": {"type": "string"}}},
     "pacing": {"type": "object", "required": ["shot_s", "words_per_minute", "cut_on"]},
     "rules": {"type": "object", "required": ["min_duration_s", "max_layer_opacity", "moving_background"],
               "properties": {"min_duration_s": {"type": "number", "minimum": 60}, "max_layer_opacity": {"const": 0.98},
                              "moving_background": {"const": True}}},
     "target": TARGET_REF})

SCHEMA_IDS = {
    "caption-style": "caption_style_preset_schema", "title-style": "title_style_preset_schema",
    "background-layer": "background_layer_preset_schema", "layer-stack": "layer_stack_preset_schema",
    "grid-system": "grid_2x2_preset_schema", "transition": "transition_preset_schema",
    "camera-move": "camera_move_preset_schema", "text-animation": "text_animation_preset_schema",
    "palette": "palette_preset_schema", "typography": "typography_pairing_schema",
    "animation-style": "animation_style_preset_schema", "aspect-format": "aspect_format_preset_schema",
    "thumbnail-style": "thumbnail_style_preset_schema", "style-preset": "short_style_preset_schema",
}
SUBKIND = {"caption-style": "caption-style", "title-style": "title-style", "background-layer": "background-layer",
           "layer-stack": "layer-stack", "grid-system": "grid-system", "transition": "transition", "camera-move": "camera-move",
           "text-animation": "text-animation", "palette": "palette", "typography": "typography",
           "animation-style": "animation-style", "aspect-format": "aspect-format", "thumbnail-style": "thumbnail-style",
           "style-preset": "style-preset"}

_VALIDATORS: dict[str, object] = {}


def validate_preset(ptype: str, preset: dict) -> None:
    if jsonschema is None:
        return
    if ptype not in _VALIDATORS:
        s = SCHEMAS[ptype]
        jsonschema.Draft202012Validator.check_schema(s)
        _VALIDATORS[ptype] = jsonschema.Draft202012Validator(s)
    errs = list(_VALIDATORS[ptype].iter_errors(preset))
    if errs:
        e = errs[0]
        raise ValueError(f"{preset.get('id')}: {'/'.join(map(str, e.absolute_path))}: {e.message}")


# --------------------------------------------------------------------------- preset builders

def static_font_file(family: str, weight: int) -> str:
    f = FONTS[family]
    if f["variable_axes"]:
        return f"{family.replace(' ', '')}-{weight}.ttf"
    return f["file"]


def font_block(spec_font: dict, extra: dict | None = None) -> dict:
    fam, w = spec_font["family"], spec_font["weight"]
    out = font_info(fam, w)
    for k in ("size_px", "min_size_px", "case", "letter_spacing_em"):
        if k in spec_font:
            out[k] = spec_font[k]
    out["avg_char_em"] = avg_em(fam, spec_font.get("case", "as-written"))
    if FONTS[fam]["variable_axes"]:
        out["variable_axes"] = FONTS[fam]["variable_axes"]
    if extra:
        out.update(extra)
    return out


def resolve_backing(spec_b: dict, c: dict, pal: dict) -> dict:
    b = {"type": spec_b["type"]}
    if spec_b["type"] == "none":
        return b
    b["tint"] = c[spec_b["tint_role"]]
    b["opacity"] = float(spec_b.get("opacity", pal["panel_opacity"]))
    for k in ("blur_px", "radius_px", "padding_px", "feather_px", "rotation_deg", "full_width", "shape"):
        if k in spec_b:
            b[k] = spec_b[k]
    return b


def caption_layout(spec: dict, tgt: dict, size: float, pad: list, stroke_px: float, font_fam: str, case: str) -> dict:
    W, H = tgt["width"], tgt["height"]
    m = tgt["safe_margins"]
    lay = spec["layout"]
    mwf = lay["max_width_fraction"]
    if tgt["aspect"] == "16:9":
        mwf = min(mwf, 0.7)
    mwf = min(mwf, 1 - m["left"] - m["right"]) if not spec.get("backing", {}).get("full_width") else mwf
    box_h = size * 1.25 * lay["max_lines"] + 2 * pad[0]
    bottom = H * (1 - m["bottom"])
    default_c = (bottom - box_h / 2 - 0.01 * H) / H
    c = lay.get("center_y_fraction", default_c)
    c = min(c, default_c)
    c = max(c, (H * m["top"] + box_h / 2) / H)
    usable = mwf * W - 2 * pad[1] - 2 * stroke_px
    chars = int(usable // (avg_em(font_fam, case) * size))
    return {"center_y_fraction": round(c, 3), "max_width_fraction": round(mwf, 3), "max_lines": lay["max_lines"],
            "max_words": lay["max_words"], "max_chars": max(4, min(80, chars)), "align": lay["align"]}


def text_contrast(fill: str, backing: dict, stroke: dict, size: float, weight: int, label: str) -> tuple[dict, bool]:
    if backing["type"] == "none":
        return contrast_entry(fill, stroke["color"], size, weight, "stroke", stroke_px=stroke["width_px"])
    return contrast_entry(fill, backing["tint"], size, weight, "panel-worst-case", backing["opacity"])


def build_caption(cid: str, pid: str | None = None, target: str = "generic_9x16") -> dict | None:
    spec = CAPTIONS[cid]
    pid = pid or spec["default_palette"]
    pal = PALETTES[pid]
    c = pal["colors"]
    tgt = target_info(target)
    f = spec["font"]
    size, weight, case = f["size_px"], f["weight"], f.get("case", "as-written")
    stroke = {"color": c[spec["stroke"]["role"]], "width_px": spec["stroke"]["width_px"]}
    backing = resolve_backing(spec["backing"], c, pal)
    if spec.get("house") and not (0.55 <= backing.get("opacity", 0) <= 0.75):
        return None
    if backing["type"] == "none" and stroke["width_px"] < 0.08 * size:
        raise ValueError(f"{cid}: outline must be at least 8% of the font size")
    pad = backing.get("padding_px", [0, 0])
    fill = c[spec["fill_role"]]
    em = spec["emphasis"]
    emphasis = {"mode": em["mode"], "scale_peak": em["scale_peak"], "duration_ms": em["duration_ms"], "easing": em["easing"]}
    if em["mode"] != "none":
        emphasis["color"] = c[em["color_role"]]
    if em.get("text_role"):
        emphasis["text_color"] = c[em["text_role"]]
        emphasis["box_opacity"] = em["box_opacity"]
    ok_all = True
    contrast = {}
    min_size = f["min_size_px"]
    entry, ok = text_contrast(fill, backing, stroke, min_size, weight, "text")
    contrast["text"], ok_all = entry, ok_all and ok
    if em["mode"] in ("keyword-pop", "color", "glow"):
        entry, ok = text_contrast(emphasis["color"], backing, stroke, min_size, weight, "keyword")
        contrast["keyword"], ok_all = entry, ok_all and ok
    elif em["mode"] in ("box-current-word", "box-keyword"):
        entry, ok = contrast_entry(emphasis["text_color"], emphasis["color"], min_size, weight, "panel-worst-case", em["box_opacity"])
        contrast["keyword_box"], ok_all = entry, ok_all and ok
    elif em["mode"] == "underline" and backing["type"] != "none":
        r = worst_panel(emphasis["color"], backing["tint"], backing["opacity"])
        if r < 3.0:
            ok_all = False
        contrast["underline"] = {"basis": "panel-worst-case", "fg": emphasis["color"], "bg": backing["tint"],
                                 "opacity": backing["opacity"], "ratio": floor2(r), "required": 3.0,
                                 "level": "AA" if r >= 3.0 else "AA"}
    if not ok_all:
        return None
    preset = {
        "type": "caption-style", "id": f"caption_{cid}", "name": spec["name"], "version": 1,
        "house": bool(spec.get("house")),
        "font": font_block(f), "fill": fill, "stroke": stroke,
        "backing": backing,
        "layout": caption_layout(spec, tgt, size, pad, stroke["width_px"], f["family"], case),
        "emphasis": emphasis,
        "timing": dict(spec["timing"]),
        "animation_in": spec["animation_in"],
        "palette": f"palette_{pid}",
        "contrast": contrast,
        "target": tgt, "reference_size": [tgt["width"], tgt["height"]],
        "use_when": spec["use_when"], "avoid_when": spec["avoid_when"],
    }
    if spec.get("keyword_animation"):
        preset["keyword_animation"] = spec["keyword_animation"]
    if spec.get("shadow"):
        sh = spec["shadow"]
        preset["shadow"] = {"color": c[sh.get("role", "stroke")], "opacity": sh["opacity"], "blur_px": sh["blur_px"],
                            "offset_px": sh["offset_px"]}
    if spec.get("house"):
        preset["forbid"] = ["progress bars", "stacked label panels", "repeated section labels"]
    if spec.get("notes"):
        preset["notes"] = " ".join(spec["notes"].split())
    if preset["emphasis"]["mode"] == "none":
        preset["emphasis"] = {"mode": "none"}
    return preset


def build_title(tid: str, pid: str | None = None, target: str = "generic_9x16") -> dict | None:
    spec = TITLES[tid]
    pid = pid or spec["default_palette"]
    pal = PALETTES[pid]
    c = pal["colors"]
    tgt = target_info(target)
    W, H, m = tgt["width"], tgt["height"], tgt["safe_margins"]
    f = spec["font"]
    size, weight, case = f["size_px"], f["weight"], f.get("case", "as-written")
    fill = c[spec["fill_role"]]
    stroke = {"color": c[spec["stroke"]["role"]], "width_px": spec["stroke"]["width_px"]}
    backing = resolve_backing(spec["backing"], c, pal)
    house = bool(spec.get("house"))
    if house and (fill.upper() != "#FFD21F" or not 0.55 <= backing.get("opacity", 0) <= 0.75):
        return None
    if backing["type"] == "none" and stroke["width_px"] < 0.06 * size:
        raise ValueError(f"{tid}: outline must be at least 6% of the font size")
    min_size = f["min_size_px"]
    entry, ok = text_contrast(fill, backing, stroke, min_size, weight, "title")
    if not ok:
        return None
    contrast = {"title": entry}
    pos = dict(spec["position"])
    pad = backing.get("padding_px", [0, 0])
    lines = spec["text"]["max_lines"]
    box_h = size * 1.15 * lines + 2 * pad[0]
    top_c = (H * m["top"] + box_h / 2) / H
    bottom_c = (H * (1 - m["bottom"]) - box_h / 2) / H
    pos["center_y_fraction"] = round(min(max(pos["center_y_fraction"], top_c), bottom_c), 3)
    if house and pos["center_y_fraction"] > 0.40:
        return None
    mwf = min(pos["max_width_fraction"], 1 - m["left"] - m["right"])
    pos["max_width_fraction"] = round(mwf, 3)
    if pos["over"] == "photo":
        pos["never_move_photo"] = True
    text = dict(spec["text"])
    usable = mwf * W - 2 * pad[1] - 2 * stroke["width_px"]
    text["max_chars_per_line"] = max(2, min(80, int(usable // (avg_em(f["family"], case) * size))))
    preset = {
        "type": "title-style", "id": f"title_{tid}", "name": spec["name"], "version": 1, "house": house,
        "font": font_block(f), "fill": fill, "stroke": stroke, "backing": backing, "position": pos, "text": text,
        "timing": dict(spec["timing"]), "animation_in": spec["animation_in"], "palette": f"palette_{pid}",
        "contrast": contrast, "target": tgt, "reference_size": [W, H],
        "use_when": spec["use_when"], "avoid_when": spec["avoid_when"],
    }
    if spec.get("label_house"):
        preset["label_house"] = True
    if spec.get("shadow"):
        sh = spec["shadow"]
        preset["shadow"] = {"color": c[sh.get("role", "stroke")], "opacity": sh["opacity"], "blur_px": sh["blur_px"],
                            "offset_px": sh["offset_px"]}
    if spec.get("secondary"):
        sec = copy.deepcopy(spec["secondary"])
        sf = sec.pop("font")
        sec_fill = c[sec.pop("fill_role")]
        bar_role = sec.pop("bar_role", None)
        sec_font = font_block(sf)
        sec_entry, ok2 = (contrast_entry(sec_fill, c[bar_role], sf["size_px"], sf["weight"], "solid") if bar_role
                          else text_contrast(sec_fill, backing, stroke, sf["size_px"], sf["weight"], "secondary"))
        if not ok2:
            return None
        contrast["secondary"] = sec_entry
        preset["secondary"] = {"font": sec_font, "fill": sec_fill, **sec}
        if bar_role:
            preset["secondary"]["bar_color"] = c[bar_role]
    if spec.get("notes"):
        preset["notes"] = " ".join(spec["notes"].split())
    return preset


PAIR_CANDIDATES = [
    ("text", "panel_tint", "panel"), ("title", "panel_tint", "panel"), ("keyword", "panel_tint", "panel"),
    ("text", "background", "solid"), ("title", "background", "solid"), ("keyword", "background", "solid"),
    ("accent", "background", "solid"), ("text", "surface", "solid"), ("keyword", "surface", "solid"),
    ("text", "stroke", "solid"), ("title", "stroke", "solid"), ("background", "keyword", "card"),
    ("background", "title", "card"), ("background", "accent", "card"),
]


def build_palette(pid: str) -> dict:
    p = PALETTES[pid]
    c, op = p["colors"], p["panel_opacity"]
    pairs, failed = [], 0
    for fg_role, bg_role, basis in PAIR_CANDIDATES:
        fg, bg = c[fg_role], c[bg_role]
        if fg.upper() == bg.upper():
            continue
        if basis == "panel":
            r, b, o = worst_panel(fg, bg, op), "panel-worst-case", op
        elif basis == "card":
            r, b, o = worst_panel(fg, bg, 0.95), "panel-worst-case", 0.95
        else:
            r, b, o = kit.contrast_ratio(fg, bg), "solid", None
        if r < 3.0:
            failed += 1
            continue
        pair = {"fg_role": fg_role, "bg_role": bg_role + ("@panel" if basis == "panel" else "@card95" if basis == "card" else ""),
                "fg": fg, "bg": bg, "basis": b}
        if o is not None:
            pair["opacity"] = o
        if r >= 4.5:
            pair.update({"ratio": floor2(r), "required": 4.5, "use": "any-size", "level": "AAA" if r >= 7 else "AA"})
        else:
            pair.update({"ratio": floor2(r), "required": 3.0, "use": "large-bold-only", "min_size_px": 24, "min_weight": 700,
                         "level": "AA-large"})
        pairs.append(pair)
    roles = {"text": "panel_tint", "title": "panel_tint", "keyword": "panel_tint"}
    for fg_role, bg_role in roles.items():
        if not any(x["fg_role"] == fg_role and x["bg_role"] == bg_role + "@panel" for x in pairs):
            raise ValueError(f"palette {pid}: {fg_role} on the frosted panel fails 3:1; fix the palette")
    preset = {"type": "palette", "id": f"palette_{pid}", "name": p["name"], "version": 1, "mode": p["mode"],
              "colors": dict(c), "panel_opacity": op, "gradient": p["gradient"], "ramp": p["ramp"], "pairs": pairs,
              "failed_pair_count": failed, "mood": p["mood"], "notes": p["notes"]}
    if p.get("source"):
        preset["source"] = p["source"]
    return preset


def font_slot(slot: dict) -> dict:
    fam = slot["family"]
    f = FONTS[fam]
    out = {"family": fam, "weight": slot["weight"], "licence": f["licence"], "file": f["file"], "file_url": f["file_url"],
           "licence_url": f["licence_url"], "specimen_url": f["specimen_url"], "category": f["category"],
           "case": slot.get("case", "as-written"), "avg_char_em": avg_em(fam, slot.get("case", "as-written"))}
    if f["variable_axes"]:
        out["variable_axes"] = f["variable_axes"]
    return out


def build_typography(tp: str, aspect: str = "9x16") -> dict:
    spec = TYPOGRAPHY[tp]
    tgt = target_info(aspect_target(aspect))
    W = tgt["width"]
    sizes = dict(spec["sizes"])
    disp, text = font_slot(spec["display"]), font_slot(spec["text"])
    title_cpl = int((0.88 * W - 80) // (disp["avg_char_em"] * sizes["title_px"]))
    cap_cpl = int((0.88 * W - 72) // (text["avg_char_em"] * sizes["caption_px"]))
    preset = {"type": "typography", "id": f"type_pair_{tp}", "name": spec["name"], "version": 1, "display": disp, "text": text,
              "sizes": sizes, "chars_per_line": {"title": title_cpl, "caption": cap_cpl}, "target": tgt,
              "mood": spec["mood"], "why": spec["why"]}
    if spec.get("numbers"):
        preset["numbers"] = font_slot(spec["numbers"])
    return preset


BG_MOTION = {
    "ocean_waves": "loop", "meadow_wind": "sway", "sunlit_water": "loop", "coastal_aerial": "loop", "cloud_timelapse": "scroll",
    "rain_on_glass": "fall", "city_night_bokeh": "drift", "forest_sunbeams": "sway", "ink_in_water": "drift",
    "campfire_embers": "rise", "neon_grid": "loop", "warm_paper": "drift", "light_leaks": "drift", "dust_particles": "rise",
    "atmospheric_haze": "drift", "bokeh_drift": "rise", "film_grain": "loop", "motion_grid_2x2": "loop",
    "starfield_drift": "scroll", "aurora_ribbons": "sway", "gradient_drift": "drift", "underwater_rays": "sway",
    "snowfall": "fall", "fireflies": "drift", "blueprint_grid": "scroll", "chalkboard_dust": "drift", "halftone_drift": "loop",
    "topographic_lines": "loop", "smoke_wisps": "rise", "silk_waves": "loop", "crt_scanlines": "scroll",
    "comic_sunburst": "rotate", "pixel_sky_parallax": "parallax", "lava_blobs": "drift", "vignette_breathe": "pulse",
    "lowpoly_facets": "pulse",
}

FOOTAGE_SOURCES = [
    {"name": "Wikimedia Commons", "url": "https://commons.wikimedia.org/",
     "note": "Each file page states its author and licence (often CC BY, CC BY-SA or public domain). Use the page's own credit line."},
    {"name": "NASA Image and Video Library", "url": "https://images.nasa.gov/",
     "terms_url": "https://www.nasa.gov/nasa-brand-center/images-and-media/",
     "note": "NASA's guidelines say its media is generally not subject to US copyright; logos and insignia are not public domain, endorsement may not be implied, and some items are third-party and marked."},
    {"name": "Pexels", "url": "https://www.pexels.com/", "terms_url": "https://www.pexels.com/license/",
     "note": "Pexels License: free to use and modify, attribution appreciated but not required; do not sell unaltered copies, imply endorsement or show identifiable people in a bad light."},
    {"name": "Pixabay", "url": "https://pixabay.com/", "terms_url": "https://pixabay.com/en/service/license/",
     "note": "Pixabay Content License: free to use without attribution; no standalone redistribution, and restrictions on trademarks and recognisable people."},
]
ACCEPTED_LICENCES = ["CC0-1.0", "Public domain (check the item page, e.g. US federal government works)",
                     "CC-BY-4.0 (credit the author in the post text)", "Pexels License (see terms_url)",
                     "Pixabay Content License (see terms_url)"]
REJECTED_LICENCES = ["Any NC (non-commercial) licence", "Any ND (no-derivatives) licence", "No stated licence",
                     "CC-BY-SA unless you accept ShareAlike terms for the finished video"]
RIGHTS_RECORD = ["item page URL", "author or agency", "licence name and version", "retrieval date", "credit line, if required"]


def motion_class(diff: float) -> str:
    return "strong" if diff >= 1.0 else "moderate" if diff >= 0.6 else "subtle"


def build_background(bid: str, pid: str | None = None, aspect: str = "9x16") -> tuple[dict, str]:
    spec = BACKGROUNDS[bid]
    tgt = target_info(aspect_target(aspect))
    W, H = tgt["width"], tgt["height"]
    graph = background_graph(bid, W, H, pid)
    stops = ramp_stops(bid, pid) if bid != "motion_grid_2x2" else None
    ident = f"bg_layer_{bid}"
    motion = {"type": BG_MOTION[bid], "period_s": LOOP_S}
    meas = MEASURED.get("backgrounds", {}).get(bid)
    if meas:
        motion["measured_mean_abs_frame_diff"] = meas["mean_abs_frame_diff"]
        motion["class"] = motion_class(meas["mean_abs_frame_diff"])
        motion["measured_on"] = meas["conditions"]
    preset = {"type": "background-layer", "id": ident, "name": spec["name"], "version": 1, "category": spec["category"],
              "role": spec["role"], "look": spec["look"],
              "render": {"method": "ffmpeg-composite" if bid == "motion_grid_2x2" else "ffmpeg-lavfi", "width": W, "height": H,
                         "fps": FPS, "loop_period_s": LOOP_S, "filtergraph_file": "filtergraph.txt",
                         "tested_with": "FFmpeg 6.1.1"},
              "default_opacity": spec["default_opacity"], "default_blend": spec["default_blend"], "motion": motion,
              "recolor": spec["recolor"], "use_when": spec["use_when"], "target": tgt}
    if stops:
        preset["render"]["colour_stops"] = stops
    if pid:
        preset["palette"] = f"palette_{pid}"
    if spec.get("footage"):
        preset["footage"] = {"search_terms": spec["footage"]["search_terms"], "prefer": spec["footage"]["prefer"],
                             "sources": FOOTAGE_SOURCES, "accepted_licences": ACCEPTED_LICENCES,
                             "rejected_licences": REJECTED_LICENCES, "record": RIGHTS_RECORD}
    if bid == "motion_grid_2x2":
        preset["grid"] = {"preset": "grid_2x2_even_feathered", "cells": [f"bg_layer_{c}" for c in spec["cells"]]}
    return preset, graph


def build_grid(gid: str, cell_set: str = "nature", aspect: str = "9x16") -> tuple[dict, str]:
    g = MOTION["grids"][gid]
    tgt = target_info(aspect_target(aspect))
    W, H = tgt["width"], tgt["height"]
    rects = kit.grid_2x2_rects(W, H, g["gutter_px"], g["margin_px"])
    main = g["placement"] == "main-content"
    if main:
        cells = [{"source": f"asset:view_{v}", "opacity": g["opacity"][i], "view": v} for i, v in enumerate(g["views"])]
        grid = {"gutter_px": g["gutter_px"], "margin_px": g["margin_px"], "feather_px": g["feather_px"],
                "corner_radius_px": g["corner_radius_px"], "cells": cells}
        graph = ("[0:v]scale=%d:%d,setsar=1,format=yuv420p[base];" % (W, H)
                 + kit.grid_2x2_filter(grid, W, H, FPS, base_label="base", inputs=("1:v", "2:v", "3:v", "4:v"), out_label="gridv")
                 + ";[gridv]format=yuv420p[out]")
    else:
        names = MOTION["grid_cell_sets"][cell_set]
        cells = grid_cells_spec(g, names)
        graph = grid_graph(g, names, W, H)
    preset = {"type": "grid-system", "id": f"grid_2x2_{gid}", "name": g["name"], "version": 1, "rows": 2, "cols": 2,
              "gutter_px": g["gutter_px"], "margin_px": g["margin_px"], "feather_px": g["feather_px"],
              "corner_radius_px": g["corner_radius_px"], "cells": cells,
              "placement": {"as": g["placement"], "blend": g["blend"],
                            "layer_opacity": 0.96 if main else 0.98},
              "canvas": {"width": W, "height": H, "fps": FPS}, "rects": [list(r) for r in rects],
              "render": {"filtergraph_file": "filtergraph.txt", "standalone": not main,
                         "inputs": "0: base video; 1-4: the four view clips (top, front, side, perspective)" if main
                         else "none (procedural cells and base gradient are generated inside the graph)"},
              "target": tgt, "use_when": g["use_when"]}
    if not main:
        preset["cell_set"] = cell_set
    return preset, graph


TEMPO = {"snappy": 0.6, "standard": 1.0, "slow": 1.6}


def build_transition(tid: str, tempo: str = "standard") -> dict:
    spec = MOTION["transitions"][tid]
    d = 0 if spec["method"] == "cut" else max(40, int(round(spec["duration_ms"] * TEMPO[tempo] / 10.0)) * 10)
    preset = {"type": "transition", "id": f"transition_{tid}", "name": spec["name"], "version": 1, "method": spec["method"],
              "duration_ms": d, "tempo": tempo, "use_when": spec["use_when"], "avoid_when": spec["avoid_when"]}
    if spec.get("xfade"):
        preset["xfade"] = spec["xfade"]
    if spec.get("overlay"):
        o = spec["overlay"]
        preset["overlay"] = {"source": o["source"], "peak_opacity": o["peak_opacity"], "blend": o["blend"], "ramp_ms": d}
    if spec.get("min_ffmpeg"):
        preset["min_ffmpeg"] = spec["min_ffmpeg"]
    sec = d / 1000
    if spec["method"] == "cut":
        preset["ffmpeg"] = {"filter": "[a][b]concat=n=2:v=1:a=0[v]"}
    else:
        f = f"[a][b]xfade=transition={spec['xfade']}:duration={sec:g}:offset=<A_DURATION-{sec:g}>[v]"
        preset["ffmpeg"] = {"filter": f}
        if spec.get("overlay"):
            peak = spec["overlay"]["peak_opacity"]
            half = sec / 2
            preset["ffmpeg"]["overlay_blend"] = (
                f"[v][leak]blend=all_expr='A+(255-A)*B/255*{peak}*max(0,1-abs(T-(<OFFSET>+{half:g}))/{half:g})'[vv]")
    return preset


INTENSITY = {"subtle": 0.5, "standard": 1.0, "strong": 1.6}


def scaled_move(spec: dict, factor: float) -> dict:
    s = copy.deepcopy(spec)
    z0, z1 = s["zoom"]["from"], s["zoom"]["to"]
    base = min(z0, z1)
    if z0 != z1:
        s["zoom"] = {"from": round(1 + (z0 - 1) * factor, 3), "to": round(1 + (z1 - 1) * factor, 3)}
    else:
        s["zoom"] = {"from": round(1 + (z0 - 1) * max(factor, 0.6), 3), "to": round(1 + (z1 - 1) * max(factor, 0.6), 3)}
    del base
    (cx0, cy0), (cx1, cy1) = s["center"]["from"], s["center"]["to"]
    mx, my = (cx0 + cx1) / 2, (cy0 + cy1) / 2
    s["center"] = {"from": [round(mx + (cx0 - mx) * factor, 3), round(my + (cy0 - my) * factor, 3)],
                   "to": [round(mx + (cx1 - mx) * factor, 3), round(my + (cy1 - my) * factor, 3)]}
    # keep the visible window inside the image: half-window (1/(2 zoom)) must fit around the centre
    zmin = min(s["zoom"]["from"], s["zoom"]["to"])
    lim = 1 / (2 * zmin)
    for key in ("from", "to"):
        x, y = s["center"][key]
        s["center"][key] = [round(min(max(x, lim), 1 - lim), 3), round(min(max(y, lim), 1 - lim), 3)]
    return s


def build_camera(mid: str, aspect: str = "9x16", intensity: str = "standard") -> dict:
    spec = MOTION["camera_moves"][mid]
    if intensity != "standard":
        spec = scaled_move(spec, INTENSITY[intensity])
    tgt = target_info(aspect_target(aspect))
    W, H = tgt["width"], tgt["height"]
    move = {k: spec[k] for k in ("duration_s", "zoom", "center", "easing") if k in spec}
    for k in ("rotation_deg", "zoom_keyframes", "shake"):
        if k in spec:
            move[k] = spec[k]
    preset = {"type": "camera-move", "id": f"camera_{mid}", "name": spec["name"], "version": 1, "kind": spec["kind"], **move,
              "renderer": spec["renderer"], "prescale": 4, "output": {"width": W, "height": H, "fps": FPS},
              "intensity": intensity, "target": tgt, "use_when": spec["use_when"]}
    for k in ("layers", "pair", "motion_blur"):
        if k in spec:
            preset[k] = spec[k]
    if spec["renderer"] == "zoompan":
        preset["ffmpeg"] = {"filter": kit.zoompan_filter(move, W, H, FPS, prescale=4)}
        if spec.get("pair"):
            pm = dict(move, zoom=spec["pair"]["zoom"], center=spec["pair"]["center"])
            preset["ffmpeg"]["pair_filter"] = kit.zoompan_filter(pm, W, H, FPS, prescale=4)
        if spec.get("motion_blur"):
            preset["ffmpeg"]["filter"] += "," + spec["motion_blur"]
    return preset


def build_text_anim(aid: str, tempo: str = "standard") -> dict:
    spec = copy.deepcopy(MOTION["text_animations"][aid])
    f = {"snappy": 0.7, "standard": 1.0, "gentle": 1.4}[tempo]
    preset = {"type": "text-animation", "id": f"text_anim_{aid}", "name": spec["name"], "version": 1, "unit": spec["unit"],
              "duration_ms": max(1, int(round(spec["duration_ms"] * f))), "stagger_ms": int(round(spec["stagger_ms"] * f)),
              "tempo": tempo, "use_when": spec["use_when"]}
    if aid == "typewriter":
        preset["duration_ms"] = 1
    if "spring" in spec:
        sp = spec["spring"]
        k2, c2 = sp["stiffness"] / (f * f), sp["damping"] / f
        preset["spring"] = {"stiffness": round(k2, 2), "damping": round(c2, 3), "mass": sp.get("mass", 1)}
        preset["spring_metrics"] = kit.spring_metrics(k2, c2, sp.get("mass", 1))
        preset["from"], preset["to"] = spec["from"], spec["to"]
    else:
        preset["keyframes"] = spec["keyframes"]
    for k in ("count", "shake", "timing_source", "applies_to"):
        if k in spec:
            preset[k] = spec[k]
    probe = dict(preset)
    dur = preset["duration_ms"]
    times = sorted({0, int(dur * 0.25), int(dur * 0.5), int(dur * 0.75), dur})
    if "spring_metrics" in preset:
        times = sorted(set(times) | {int(preset["spring_metrics"]["peak_time_s"] * 1000)})
    samples = []
    for t in times:
        st = kit.text_anim_state(probe, t, 1)[0]
        samples.append([t, {k: round(v, 3) for k, v in st.items() if k != "visible" and isinstance(v, float)
                            and abs(v - kit._TEXT_PROPS.get(k, 0)) > 1e-6 or k in ("scale", "opacity")}])
    preset["samples"] = samples
    expr = drawtext_exprs(preset)
    if expr:
        preset["ffmpeg"] = expr
    return preset


def drawtext_exprs(preset: dict) -> dict | None:
    """drawtext expressions (relative to start time T0) for whole-text animations ffmpeg can express."""
    if preset["unit"] not in ("text", "line") or preset.get("count"):
        return None
    dur = preset["duration_ms"] / 1000
    s = f"clip((t-T0)/{dur:g},0,1)"
    out = {}
    if "keyframes" in preset:
        kf = preset["keyframes"]
        for prop, key in (("scale", "fontsize_factor"), ("opacity", "alpha"), ("dy_px", "y_offset")):
            if any(prop in k for k in kf):
                if any("ease" in k and k["ease"] in ("ease-out-elastic",) for k in kf):
                    return None
                out[key] = kit._piecewise_expr(kf, prop, s)
        if any(k for k in kf if set(k) - {"t", "ease", "scale", "opacity", "dy_px"}):
            return None
    else:
        sp = preset["spring"]
        w0 = math.sqrt(sp["stiffness"] / sp["mass"])
        z = sp["damping"] / (2 * math.sqrt(sp["stiffness"] * sp["mass"]))
        if z >= 1:
            return None
        wd = w0 * math.sqrt(1 - z * z)
        p = f"(1-exp(-{z * w0:.4f}*max(0,t-T0))*(cos({wd:.4f}*max(0,t-T0))+{z * w0 / wd:.4f}*sin({wd:.4f}*max(0,t-T0))))"
        for prop, key in (("scale", "fontsize_factor"), ("opacity", "alpha"), ("dy_px", "y_offset")):
            if prop in preset["from"]:
                a, b = preset["from"][prop], preset["to"][prop]
                e = f"({a:g}+({b - a:g})*{p})"
                out[key] = f"clip({e},0,1)" if prop == "opacity" else e
    return out or None


def build_anim_style(sid: str, aspect: str = "9x16", topic: str | None = None) -> dict:
    spec = copy.deepcopy(ANIM[sid])
    tgt = target_info(aspect_target(aspect))
    W, H = tgt["width"], tgt["height"]
    render = {"width": W, "height": H, "fps": spec["timing"]["render_fps"]}
    if sid == "pixel_art":
        render["base_resolution"] = [W // 4, H // 4]
        render["upscale"] = f"scale=iw*4:ih*4:flags=neighbor  ({W // 4}x{H // 4} -> {W}x{H})"
    if spec["projection"] in ("isometric", "orthographic-top", "orthographic-side"):
        render["blender_output"] = f"Resolution X {W}, Y {H}; Orthographic Scale sets the width of the view in scene units"
    preset = {"type": "animation-style", "id": f"anim_style_{sid}", "name": spec["name"], "version": 1,
              "projection": spec["projection"], "camera": spec["camera"], "shading": spec["shading"], "outline": spec["outline"],
              "timing": spec["timing"], "palette": spec["palette"], "best_for": spec["best_for"], "avoid": spec["avoid"],
              "look": spec["look"], "recipe": spec["recipe"], "pitfalls": spec["pitfalls"], "tools": spec["tools"],
              "render": render, "target": tgt}
    for k in ("layers", "views"):
        if k in spec:
            preset[k] = spec[k]
    if topic:
        t = TOPICS[topic]
        preset["topic"] = {"id": topic, "label": t["label"], "note": t["note"]}
        preset["suggested"] = {"palette": f"palette_{t['palette']}", "background": f"bg_layer_{t['background']}"}
    return preset


ENCODE_ARGS = FORMATS["encoding"]["ffmpeg"].format(gop=FPS // 2)


def build_aspect(aspect: str, target: str | None = None) -> dict:
    a = ASPECTS[aspect]
    tid = target or aspect_target(aspect)
    tgt = target_info(tid)
    W, H = a["size"]
    m = tgt["safe_margins"]
    preset = {"type": "aspect-format", "id": f"aspect_{aspect}" + (f"_{tid}" if target else ""),
              "name": tgt["label"], "version": 1, "aspect": a["ratio"], "width": W, "height": H, "platform": tgt["platform"],
              "safe_margins": m, "margins_basis": FORMATS["margin_basis"].strip(), "margins_verified": False,
              "safe_rect_px": list(kit.safe_rect(W, H, m)),
              "zones": {"title_center_y": max(a["title_center_y"], round(m["top"] + 0.08, 3)),
                        "caption_center_y": min(a["caption_center_y"], round(1 - m["bottom"] - 0.04, 3)),
                        "photo_rect": a["photo_rect"]},
              "encoding": {"video_codec": "h264 (libx264), High profile", "pix_fmt": "yuv420p", "fps": FPS, "gop": FPS // 2,
                           "b_frames": 2, "closed_gop": True, "audio_codec": "aac", "audio_rate_hz": 48000,
                           "container": "mp4 with faststart", "ffmpeg_args": ENCODE_ARGS,
                           "source": FORMATS["encoding"]["source"], "source_summary": " ".join(FORMATS["encoding"]["summary"].split())},
              "duration": {"min_s": 60, "note": "House rule: deliver full videos of at least 60 seconds."},
              "use": a["use"]}
    return preset


def build_thumbnail(thid: str, pid: str | None = None, target: str = "youtube_16x9") -> dict | None:
    spec = THUMBS["styles"][thid]
    tg = THUMBS["targets"][target]
    pid = pid or spec["default_palette"]
    pal = PALETTES[pid]
    c = pal["colors"]
    W, H = tg["size"]
    t = spec["text"]
    size = int(round(t["size_frac"] * min(W, H) * (1080 / min(W, H)) * (W / 1080 if W < 1080 else 1)))
    size = int(round(t["size_frac"] * W))
    stroke_w = int(round(t["stroke_frac"] * W))
    fill = c[t["fill_role"]]
    stroke = {"color": c[t["stroke_role"]], "width_px": stroke_w}
    pspec = spec["panel"]
    panel = {"type": pspec["type"]}
    if pspec["type"] != "none":
        panel["tint"] = c[pspec["tint_role"]]
        panel["opacity"] = float(pspec.get("opacity", pal["panel_opacity"]))
        if "blur_px" in pspec:
            panel["blur_px"] = pspec["blur_px"]
    weight = t["font"]["weight"]
    if panel["type"] == "none":
        if stroke_w < 0.06 * size:
            raise ValueError(f"{thid}: outline too thin")
        entry, ok = contrast_entry(fill, stroke["color"], size, weight, "stroke", stroke_px=stroke_w)
    else:
        entry, ok = contrast_entry(fill, panel["tint"], size, weight, "panel-worst-case", panel["opacity"])
    if not ok:
        return None
    return {"type": "thumbnail-style", "id": f"thumb_{thid}", "name": spec["name"], "version": 1,
            "target": {"id": target, "label": tg["label"], "width": W, "height": H},
            "text": {"max_words": t["max_words"], "font": font_block(dict(t["font"], size_px=size)), "size_px": size,
                     "fill": fill, "stroke": stroke, "case": t["font"].get("case", "as-written")},
            "panel": panel, "layout": spec["layout"], "contrast": {"text": entry},
            "export": {"format": "jpg", "quality": 90, "max_bytes": tg["max_bytes"], "note": tg["note"],
                       **({"source": tg["source"]} if tg.get("source") else {})},
            "palette": f"palette_{pid}", "use_when": spec["use_when"]}


ROLE_MOTION = {"drift": "drift", "loop": "loop", "rise": "rise", "sway": "sway", "pulse": "pulse", "follow": "follow",
               "ken-burns": "ken-burns", "punch-in": "punch-in", "keyframed": "keyframed", "static": "static",
               "rotate": "rotate", "parallax": "parallax", "scroll": "scroll"}


def resolve_source(src: str, theme: dict) -> dict:
    src = src.format(**theme) if "{" in src else src
    kind, ref = src.split(":", 1)
    if kind == "bg":
        return {"kind": "component", "ref": f"bg_layer_{ref}"}
    if kind == "grid":
        return {"kind": "component", "ref": f"grid_2x2_{ref}"}
    if kind == "title":
        return {"kind": "component", "ref": f"title_{ref}"}
    if kind == "caption":
        return {"kind": "component", "ref": f"caption_{ref}"}
    if kind == "anim":
        return {"kind": "component", "ref": f"text_anim_{ref}"}
    if kind == "asset":
        return {"kind": "asset", "ref": ref}
    if kind == "solid":
        return {"kind": "palette-colour", "ref": ref}
    if kind == "grade":
        return {"kind": "grade", "ref": f"palette_{ref}"}
    if kind in ("fx", "panel"):
        return {"kind": "effect", "ref": f"{kind}:{ref}"}
    raise ValueError(src)


def build_stack(sid: str, theme_id: str | None = None, aspect: str | None = None) -> tuple[dict, str, dict]:
    spec = STACKS["stacks"][sid]
    theme_id = theme_id or spec["theme"]
    theme = dict(STACKS["themes"][theme_id])
    aspect = aspect or spec.get("aspect", "9x16")
    pid = spec.get("palette") or theme["palette"]
    theme["palette"] = pid
    tgt = target_info(aspect_target(aspect))
    W, H = tgt["width"], tgt["height"]
    photo_rect = ASPECTS[aspect]["photo_rect"]
    layers, used_fx = [], {}
    for row in spec["layers"]:
        z, lid, role, src, op, blend, motion = row[:7]
        extras = copy.deepcopy(row[7]) if len(row) > 7 else {}
        layer = {"z": z, "id": lid, "role": role, "source": resolve_source(src, theme), "opacity": op, "blend": blend,
                 "motion": {"type": ROLE_MOTION[motion]}}
        if extras.pop("rect", None) == "photo":
            layer["rect"] = dict(photo_rect)
        for k in ("feather_px", "corner_radius_px"):
            if k in extras:
                layer[k] = extras.pop(k)
        if "opacity_keyframes" in extras:
            layer["opacity_keyframes"] = extras.pop("opacity_keyframes")
        if "cells" in extras:
            cells = extras.pop("cells")
            cells = cells.format(**theme) if "{" in cells else cells
            if cells in MOTION["grid_cell_sets"]:
                layer["source"]["cells"] = [f"bg_layer_{c}" for c in MOTION["grid_cell_sets"][cells]]
            else:
                layer["source"]["cells"] = [c.strip() for c in cells.split(",")]
        if extras:
            layer["details"] = extras
        if layer["source"]["kind"] == "effect":
            name = layer["source"]["ref"].split(":", 1)[1]
            if layer["source"]["ref"].startswith("fx:"):
                used_fx[name] = STACKS["effects"][name]
        layers.append(layer)
    graph, render_info = stack_background_graph(layers, W, H, pid)
    preset = {"type": "layer-stack", "id": f"layer_stack_{sid}", "name": spec["name"], "version": 1, "house": bool(spec.get("house")),
              "summary": spec["summary"], "canvas": {"width": W, "height": H, "fps": FPS}, "theme": theme_id,
              "palette": f"palette_{pid}", "target": tgt, "layers": layers,
              "rules": {"max_layer_opacity": 0.98, "min_layers": 5}, "effects": used_fx, "background_render": render_info}
    problems = kit.layer_stack_problems(preset)
    if problems:
        raise ValueError(f"{sid}/{theme_id}/{aspect}: {problems}")
    return preset, graph, theme


def stack_background_graph(layers: list[dict], W: int, H: int, pid: str) -> tuple[str, dict]:
    """Composite every full-frame procedural layer (backgrounds, grids, palette colours, grade) into one loop."""
    pal = PALETTES[pid]
    parts, comp, included, skipped = [], [], [], []
    for layer in layers:
        src = layer["source"]
        if layer.get("rect") or layer.get("opacity_keyframes") or layer["role"] == "transition":
            skipped.append(layer["id"])
            continue
        label = f"z{layer['z']}_"
        if src["kind"] == "component" and src["ref"].startswith("bg_layer_"):
            bid = src["ref"][len("bg_layer_"):]
            use_pid = pid if BACKGROUNDS[bid]["recolor"] in ("two_tone",) or bid == "gradient_drift" else None
            if BACKGROUNDS[bid]["recolor"] == "overlay":
                use_pid = pid
            parts.append(prefix_labels(background_graph(bid, W, H, use_pid), label))
        elif src["kind"] == "component" and src["ref"].startswith("grid_2x2_"):
            gid = src["ref"][len("grid_2x2_"):]
            cells = [c[len("bg_layer_"):] for c in src.get("cells", [])]
            if not cells or any(c not in RECIPES for c in cells):
                skipped.append(layer["id"])
                continue
            parts.append(prefix_labels(grid_graph(MOTION["grids"][gid], cells, W, H, pid), label))
        elif src["kind"] == "palette-colour":
            parts.append(f"color=c=0x{pal['colors'][src['ref']][1:]}:s={W}x{H}:r={FPS}:d={LOOP_S},format=yuv420p[{label}out]")
        elif src["kind"] == "grade":
            parts.append(f"color=c=0x{pal['colors']['light'][1:]}:s={W}x{H}:r={FPS}:d={LOOP_S},format=yuv420p[{label}out]")
        else:
            skipped.append(layer["id"])
            continue
        comp.append({"label": f"{label}out", "opacity": layer["opacity"], "blend": layer["blend"], "id": layer["id"]})
        included.append(layer["id"])
    parts.append(kit.layer_stack_filter(comp, W, H, FPS, out_label="stackv"))
    parts.append("[stackv]format=yuv420p[out]")
    info = {"filtergraph_file": "background_filtergraph.txt", "loop_period_s": LOOP_S, "included_layers": included,
            "rendered_separately": skipped,
            "note": "The background graph renders every full-frame procedural layer. Photo, panels, text, effects and cut-timed layers are composited afterwards in z order."}
    return ";".join(parts), info


def build_look(lid: str, target: str = "generic_9x16", pid: str | None = None) -> tuple[dict, dict | None]:
    spec = LOOKS[lid]
    pid = pid or spec["palette"]
    tgt = target_info(target)
    comps = {"palette": f"palette_{pid}", "typography": spec["typography"], "caption_style": spec["caption"],
             "title_style": spec["title"], "label_style": spec["label"], "layer_stack": spec["stack"],
             "text_in": spec["text_in"], "keyword": spec["keyword"], "camera_moves": spec["camera"],
             "transitions": spec["transitions"], "thumbnail": spec["thumbnail"],
             "aspect_format": {"9:16": "aspect_9x16", "4:5": "aspect_4x5", "1:1": "aspect_1x1", "16:9": "aspect_16x9"}[tgt["aspect"]]}
    if spec.get("animation_style"):
        comps["animation_style"] = spec["animation_style"]
    if spec.get("stack_theme"):
        comps["stack_theme"] = spec["stack_theme"]
    preset = {"type": "style-preset", "id": f"look_{lid}", "name": spec["name"], "version": 1, "house": bool(spec.get("house")),
              "use_for": spec["use_for"], "avoid": spec["avoid"], "components": comps,
              "pacing": {"shot_s": spec["pacing"]["shot_s"], "words_per_minute": spec["pacing"]["words_per_minute"],
                         "cut_on": spec["pacing"]["cut_on"]},
              "rules": {"min_duration_s": 60, "max_layer_opacity": 0.98, "moving_background": True,
                        "sources_required_for_facts": True, "title_on_first_frame": True},
              "target": tgt}
    return preset, look_spec_template(spec, preset, pid, tgt)


SPEC_FORMATS = {"9:16": "1080x1920", "4:5": "1080x1350", "16:9": "1920x1080"}
SPEC_KINDS = {"base": "background-video", "background-video": "background-video", "grid-2x2": "grid-2x2",
              "texture": "texture", "light": "light", "particles": "particles", "haze": "overlay", "grain": "texture",
              "vignette": "overlay", "overlay": "overlay", "photo": "photo"}
SPEC_BLENDS = {"normal": "normal", "screen": "screen", "multiply": "multiply", "overlay": "overlay", "soft-light": "soft-light",
               "add": "add", "lighten": "screen", "darken": "multiply"}


def look_spec_template(spec: dict, preset: dict, pid: str, tgt: dict) -> dict | None:
    fmt = SPEC_FORMATS.get(tgt["aspect"])
    if not fmt:
        return None
    stack_id = spec["stack"][len("layer_stack_"):]
    stack, _, _ = build_stack(stack_id, spec.get("stack_theme"))
    pal = PALETTES[pid]
    label_tpl = {"title_fact_number_label": "FACT", "title_step_card_center": "STEP"}.get(spec["label"])
    scenes = []
    for i in range(4):
        layers = []
        for layer in stack["layers"]:
            kind = SPEC_KINDS.get(layer["role"])
            if not kind or layer["source"]["kind"] not in ("component", "asset"):
                continue
            src = layer["source"]["ref"] if layer["source"]["kind"] == "component" else f"{{{{{layer['source']['ref'].upper()}_{i + 1}}}}}"
            entry = {"kind": kind, "source": src, "opacity": layer["opacity"]}
            if layer["blend"] in SPEC_BLENDS:
                entry["blend"] = SPEC_BLENDS[layer["blend"]]
            if layer.get("feather_px"):
                entry["feather_px"] = layer["feather_px"]
            entry["motion"] = layer["motion"]["type"]
            layers.append(entry)
        scene = {"start_s": i * 16, "end_s": (i + 1) * 16, "layers": layers}
        if label_tpl:
            scene["label"] = f"{label_tpl} {i + 1}"
            scene["key_number"] = "{{KEY_NUMBER_%d}}" % (i + 1)
        scenes.append(scene)
    wpm = sum(spec["pacing"]["words_per_minute"]) // 2
    title_id = spec["title"][len("title_"):]
    title_spec = TITLES[title_id]
    backing = "frosted-glass" if title_spec["backing"]["type"] == "frosted-glass" else "none"
    return {
        "title_hook": {"text": "{{HOOK}}", "color": pal["colors"][title_spec["fill_role"]],
                       "position": "upper-third-over-photo" if title_spec["position"]["region"] == "upper-third" else "center-over-photo",
                       "backing": backing, "hold_s": min(4, title_spec["timing"]["hold_s"])},
        "duration_s": 64, "format": fmt, "scenes": scenes,
        "captions": [{"start_s": 2.4, "end_s": 4.2, "text": "{{CAPTION_1}}", "pop_word": "{{KEYWORD_1}}"}],
        "narration": {"engine": "{{TTS_ENGINE}}", "voice": "{{VOICE}}", "words_per_minute": wpm},
        "music": {"title": "{{MUSIC_TITLE}}", "licence": "{{MUSIC_LICENCE}}", "gain_db": -18},
        "sources": [],
    }
