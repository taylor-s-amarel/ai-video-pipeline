---
name: "title-date-stamp-history"
description: "Use when placing a hook title or item label (FACT N, STEP N, #N) on a short in the 'On-this-day date stamp' style: font, colours, backing, upper-third position over the photo, first-frame timing and computed contrast, with an ffmpeg recipe."
---

# On-this-day date stamp

Title style for Vertical 9:16 (generic) (1080x1920). Palette `palette_warm_paper_sepia`.

## When to use
- Today-in-history and anniversary shorts

## Avoid when
- Dates you have not verified against a source

## Parameters

| Parameter | Value |
|---|---|
| Font | Special Elite 400, 58 px (down to 46 px), upper |
| Fill | `#7A2E0E` |
| Outline | none |
| Backing | solid: tint `#FFF8EC` at 78%, radius 4 px, feather 2 px, rotated -1.5 deg |
| Position | upper-third, centred at 18% of the height, over the photo, max width 70% |
| Photo | never shrink or move the photo for the title; overlay it |
| Text | template `ON THIS DAY · {date}`, 3-6 words, up to 1 line(s), about 21 characters per line |
| Timing | visible from frame 0, hold 2.8 s |
| Entry | `text_anim_typewriter` |
| Second line | Playfair Display 800, 76 px, `#2B1D12`: the event headline |

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| title | `#7A2E0E` | panel `#FFF8EC` at 78%, worst case over any video | 5.29:1 | 4.5:1 |
| secondary | `#2B1D12` | panel `#FFF8EC` at 78%, worst case over any video | 9.15:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases over any video underneath (panel colour computed over pure black and pure white).

## Render it

```bash
mkdir -p fonts
curl -L -o "fonts/SpecialElite-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/apache/specialelite/SpecialElite-Regular.ttf"
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=636:102:222:294,drawbox=x=0:y=0:w=iw:h=ih:color=0xFFF8EC@0.78:t=fill,format=yuva420p[glass];color=c=black:s=636x102:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(4-X,X-(W-1-4)),0)*gt(max(4-Y,Y-(H-1-4)),0),(4-hypot(max(max(4-X,X-(W-1-4)),0),max(max(4-Y,Y-(H-1-4)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/2,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=222:294:shortest=1:enable='between(t,0,2.8)',drawtext=fontfile=fonts/SpecialElite-Regular.ttf:text='ON THIS DAY  1 JAN':fontsize=58:fontcolor=0x7A2E0E:x=(w-text_w)/2:y=345-text_h/2:enable='between(t,0,2.8)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p titled.mp4
```

The graph blurs the region behind the title, tints it at the preset opacity, pastes it back through a
rounded, feathered mask (98% at most, so nothing is fully opaque) and draws the line. For two lines,
add a second `drawtext` with `y` moved by 66 px. For the entry animation, use the
expressions in the `text_anim_typewriter` text-animation preset (drawtext `fontsize`/`alpha`) or render the
title as RGBA frames with Pillow:

```python
import json, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

st = json.load(open("preset.json"))
frame = Image.open("first_frame.png").convert("RGB")
font = ImageFont.truetype("fonts/SpecialElite-Regular.ttf", st["font"]["size_px"])
# static font: no axes to set
d = ImageDraw.Draw(frame)
w = d.textlength("ON THIS DAY  1 JAN", font=font)
x0 = int((frame.width - w) / 2) - 28
y_c = int(st["position"]["center_y_fraction"] * frame.height)
box = (x0, y_c - 51, frame.width - x0, y_c + 51)
frame = kit.frosted_panel(frame, box, st["backing"]["tint"], st["backing"]["opacity"], st["backing"].get("blur_px", 1), st["backing"].get("radius_px", 0), st["backing"].get("feather_px", 0))
ImageDraw.Draw(frame).text((frame.width / 2, y_c), "ON THIS DAY  1 JAN", font=font, fill=st["fill"], anchor="mm",
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
- Font licence: https://raw.githubusercontent.com/google/fonts/main/apache/specialelite/LICENSE.txt
