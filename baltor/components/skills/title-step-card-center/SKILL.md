---
name: "title-step-card-center"
description: "Use when placing a hook title or item label (FACT N, STEP N, #N) on a short in the 'STEP N card' style: font, colours, backing, upper-third position over the photo, first-frame timing and computed contrast, with an ffmpeg recipe."
---

# STEP N card

Title style for Vertical 9:16 (generic) (1080x1920). Palette `palette_okabe_ito_safe`.

## When to use
- Tutorials and how-tos

## Avoid when
- Fact lists (use FACT N)

## Parameters

| Parameter | Value |
|---|---|
| Font | Atkinson Hyperlegible 700, 64 px (down to 52 px), upper |
| Fill | `#F0E442` |
| Outline | none |
| Backing | frosted-glass: tint `#000000` at 66%, blur sigma 24 px, radius 24 px, feather 12 px |
| Position | upper-third, centred at 28% of the height, over the photo, max width 60% |
| Photo | never shrink or move the photo for the title; overlay it |
| Text | template `STEP {n}`, 2-2 words, up to 1 line(s), about 15 characters per line |
| Timing | appears when its item starts, hold 2.4 s |
| Entry | `text_anim_springy_pop_overshoot` |
| Second line | Atkinson Hyperlegible 700, 56 px, `#FFFFFF`: the action in 2-5 words |

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| title | `#F0E442` | panel `#000000` at 66%, worst case over any video | 5.49:1 | 3:1 (>= 24 px bold) |
| secondary | `#FFFFFF` | panel `#000000` at 66%, worst case over any video | 7.25:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases over any video underneath (panel colour computed over pure black and pure white).

## Render it

```bash
mkdir -p fonts
curl -L -o "fonts/AtkinsonHyperlegible-Bold.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/AtkinsonHyperlegible-Bold.ttf"
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=290:118:394:478,gblur=sigma=24,drawbox=x=0:y=0:w=iw:h=ih:color=0x000000@0.66:t=fill,format=yuva420p[glass];color=c=black:s=290x118:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(24-X,X-(W-1-24)),0)*gt(max(24-Y,Y-(H-1-24)),0),(24-hypot(max(max(24-X,X-(W-1-24)),0),max(max(24-Y,Y-(H-1-24)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/12,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=394:478:shortest=1:enable='between(t,0,2.4)',drawtext=fontfile=fonts/AtkinsonHyperlegible-Bold.ttf:text='STEP 1':fontsize=64:fontcolor=0xF0E442:x=(w-text_w)/2:y=537-text_h/2:enable='between(t,0,2.4)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p titled.mp4
```

The graph blurs the region behind the title, tints it at the preset opacity, pastes it back through a
rounded, feathered mask (98% at most, so nothing is fully opaque) and draws the line. For two lines,
add a second `drawtext` with `y` moved by 73 px. For the entry animation, use the
expressions in the `text_anim_springy_pop_overshoot` text-animation preset (drawtext `fontsize`/`alpha`) or render the
title as RGBA frames with Pillow:

```python
import json, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

st = json.load(open("preset.json"))
frame = Image.open("first_frame.png").convert("RGB")
font = ImageFont.truetype("fonts/AtkinsonHyperlegible-Bold.ttf", st["font"]["size_px"])
# static font: no axes to set
d = ImageDraw.Draw(frame)
w = d.textlength("STEP 1", font=font)
x0 = int((frame.width - w) / 2) - 34
y_c = int(st["position"]["center_y_fraction"] * frame.height)
box = (x0, y_c - 59, frame.width - x0, y_c + 59)
frame = kit.frosted_panel(frame, box, st["backing"]["tint"], st["backing"]["opacity"], st["backing"].get("blur_px", 1), st["backing"].get("radius_px", 0), st["backing"].get("feather_px", 0))
ImageDraw.Draw(frame).text((frame.width / 2, y_c), "STEP 1", font=font, fill=st["fill"], anchor="mm",
                           stroke_width=st["stroke"]["width_px"], stroke_fill=st["stroke"]["color"])
frame.save("title_preview.png")
```

The `short_style_preset_kit` code module has the maths used here (contrast, easing, springs, zoompan, xfade chains, grids, layer stacks, Pillow frosted panels). Place it with `python3 baltor/tools/baltor_catalog.py place short_style_preset_kit <step-dir>`; it lands in `.baltor/lib/short-style-preset-kit/`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `title_style_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- ffmpeg filters: https://ffmpeg.org/ffmpeg-filters.html
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/atkinsonhyperlegible/OFL.txt
