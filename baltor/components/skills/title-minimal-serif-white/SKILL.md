---
name: "title-minimal-serif-white"
description: "Use when placing a hook title or item label (FACT N, STEP N, #N) on a short in the 'Minimal serif title' style: font, colours, backing, upper-third position over the photo, first-frame timing and computed contrast, with an ffmpeg recipe."
---

# Minimal serif title

Title style for Vertical 9:16 (generic) (1080x1920). Palette `palette_forest_canopy`.

## When to use
- Calm nature
- biography and quote shorts

## Avoid when
- Hype edits

## Parameters

| Parameter | Value |
|---|---|
| Font | Playfair Display 800, 84 px (down to 64 px), as-written |
| Fill | `#F4FBEF` |
| Outline | none |
| Backing | frosted-glass: tint `#0A1A0F` at 64%, blur sigma 30 px, radius 30 px, feather 24 px |
| Position | upper-third, centred at 24% of the height, over the photo, max width 86% |
| Photo | never shrink or move the photo for the title; overlay it |
| Text | 2-7 words, up to 2 line(s), about 22 characters per line |
| Timing | visible from frame 0, hold 2.4 s |
| Entry | `text_anim_blur_in_focus` |

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| title | `#F4FBEF` | panel `#0A1A0F` at 64%, worst case over any video | 5.13:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases over any video underneath (panel colour computed over pure black and pure white).

## Render it

```bash
mkdir -p fonts
curl -L -o "fonts/PlayfairDisplay[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/PlayfairDisplay[wght].ttf" wght=800 -o fonts/PlayfairDisplay-800.ttf
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=608:156:236:382,gblur=sigma=30,drawbox=x=0:y=0:w=iw:h=ih:color=0x0A1A0F@0.64:t=fill,format=yuva420p[glass];color=c=black:s=608x156:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(30-X,X-(W-1-30)),0)*gt(max(30-Y,Y-(H-1-30)),0),(30-hypot(max(max(30-X,X-(W-1-30)),0),max(max(30-Y,Y-(H-1-30)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/24,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=236:382:shortest=1:enable='between(t,0,2.4)',drawtext=fontfile=fonts/PlayfairDisplay-800.ttf:text='YOUR HOOK HERE':fontsize=84:fontcolor=0xF4FBEF:x=(w-text_w)/2:y=460-text_h/2:enable='between(t,0,2.4)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p titled.mp4
```

The graph blurs the region behind the title, tints it at the preset opacity, pastes it back through a
rounded, feathered mask (98% at most, so nothing is fully opaque) and draws the line. For two lines,
add a second `drawtext` with `y` moved by 96 px. For the entry animation, use the
expressions in the `text_anim_blur_in_focus` text-animation preset (drawtext `fontsize`/`alpha`) or render the
title as RGBA frames with Pillow:

```python
import json, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

st = json.load(open("preset.json"))
frame = Image.open("first_frame.png").convert("RGB")
font = ImageFont.truetype("fonts/PlayfairDisplay[wght].ttf", st["font"]["size_px"])
font.set_variation_by_axes([800])  # axis order as in the font
d = ImageDraw.Draw(frame)
w = d.textlength("YOUR HOOK HERE", font=font)
x0 = int((frame.width - w) / 2) - 40
y_c = int(st["position"]["center_y_fraction"] * frame.height)
box = (x0, y_c - 78, frame.width - x0, y_c + 78)
frame = kit.frosted_panel(frame, box, st["backing"]["tint"], st["backing"]["opacity"], st["backing"].get("blur_px", 1), st["backing"].get("radius_px", 0), st["backing"].get("feather_px", 0))
ImageDraw.Draw(frame).text((frame.width / 2, y_c), "YOUR HOOK HERE", font=font, fill=st["fill"], anchor="mm",
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
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/OFL.txt
