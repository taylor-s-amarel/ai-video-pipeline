---
name: "title-top-n-rank"
description: "Use when placing a hook title or item label (FACT N, STEP N, #N) on a short in the 'Top-N rank number' style: font, colours, backing, upper-third position over the photo, first-frame timing and computed contrast, with an ffmpeg recipe."
---

# Top-N rank number

Title style for Vertical 9:16 (generic) (1080x1920). Palette `palette_news_contrast`.

## When to use
- Countdowns and rankings

## Avoid when
- Lists where order means nothing

## Parameters

| Parameter | Value |
|---|---|
| Font | Anton 400, 220 px (down to 160 px), upper |
| Fill | `#FFCC00` |
| Outline | 14 px `#000000` |
| Backing | none; the outline carries the contrast |
| Position | upper-third, centred at 26% of the height, over the background, max width 50% |
| Text | template `#{n}`, 1-1 words, up to 1 line(s), about 5 characters per line |
| Timing | appears when its item starts, hold 2.0 s |
| Entry | `text_anim_kinetic_slam` |
| Second line | Montserrat 800, 56 px, `#FFFFFF`: item name |

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| title | `#FFCC00` | outline `#000000` (14 px) | 13.88:1 | 4.5:1 |
| secondary | `#FFFFFF` | outline `#000000` (14 px) | 21.00:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases over any video underneath (panel colour computed over pure black and pure white).

## Render it

```bash
mkdir -p fonts
curl -L -o "fonts/Anton-Regular.ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf"
ffmpeg -y -i in.mp4 -filter_complex "[0:v]drawtext=fontfile=fonts/Anton-Regular.ttf:text='#1':fontsize=220:fontcolor=0xFFCC00:borderw=14:bordercolor=0x000000:x=(w-text_w)/2:y=499-text_h/2:enable='between(t,0,2)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p titled.mp4
```

The graph blurs the region behind the title, tints it at the preset opacity, pastes it back through a
rounded, feathered mask (98% at most, so nothing is fully opaque) and draws the line. For two lines,
add a second `drawtext` with `y` moved by 252 px. For the entry animation, use the
expressions in the `text_anim_kinetic_slam` text-animation preset (drawtext `fontsize`/`alpha`) or render the
title as RGBA frames with Pillow:

```python
import json, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

st = json.load(open("preset.json"))
frame = Image.open("first_frame.png").convert("RGB")
font = ImageFont.truetype("fonts/Anton-Regular.ttf", st["font"]["size_px"])
# static font: no axes to set
d = ImageDraw.Draw(frame)
w = d.textlength("#1", font=font)
x0 = int((frame.width - w) / 2) - 0
y_c = int(st["position"]["center_y_fraction"] * frame.height)
box = (x0, y_c - 143, frame.width - x0, y_c + 143)
# no panel: the outline carries the contrast
ImageDraw.Draw(frame).text((frame.width / 2, y_c), "#1", font=font, fill=st["fill"], anchor="mm",
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
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/anton/OFL.txt
