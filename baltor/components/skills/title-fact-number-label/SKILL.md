---
name: "title-fact-number-label"
description: "Use when placing a hook title or item label (FACT N, STEP N, #N) on a short in the 'FACT N label with key number' style: font, colours, backing, upper-third position over the photo, first-frame timing and computed contrast, with an ffmpeg recipe."
---

# FACT N label with key number

Title style for Vertical 9:16 (generic) (1080x1920). Palette `palette_house_yellow_night`. The label pops in when a new item starts and the key number (for example "14 DAYS") sits under it.

## When to use
- Numbered fact
- tip or step shorts
- Each time a new item starts

## Avoid when
- Repeating the same label on every caption (one label per item)

## Parameters

| Parameter | Value |
|---|---|
| Font | Montserrat 900, 54 px (down to 44 px), upper |
| Fill | `#FFD21F` |
| Outline | none |
| Backing | frosted-glass: tint `#0B1220` at 62%, blur sigma 24 px, radius 999 px, feather 10 px |
| Position | upper-third, centred at 30% of the height, over the photo, max width 60% |
| Photo | never shrink or move the photo for the title; overlay it |
| Text | template `FACT {n}`, 2-2 words, up to 1 line(s), about 16 characters per line |
| Timing | appears when its item starts, hold 3.0 s |
| Entry | `text_anim_springy_pop_overshoot` |
| Second line | Anton 400, 120 px, `#FFFFFF`: key number with unit |

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| title | `#FFD21F` | panel `#0B1220` at 62%, worst case over any video | 3.63:1 | 3:1 (>= 24 px bold) |
| secondary | `#FFFFFF` | panel `#0B1220` at 62%, worst case over any video | 5.26:1 | 4.5:1 |

Panel ratios are worst cases over any video underneath (panel colour computed over pure black and pure white).

## Render it

```bash
mkdir -p fonts
curl -L -o "fonts/Montserrat[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Montserrat[wght].ttf" wght=900 -o fonts/Montserrat-900.ttf
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=268:98:406:526,gblur=sigma=24,drawbox=x=0:y=0:w=iw:h=ih:color=0x0B1220@0.62:t=fill,format=yuva420p[glass];color=c=black:s=268x98:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(49-X,X-(W-1-49)),0)*gt(max(49-Y,Y-(H-1-49)),0),(49-hypot(max(max(49-X,X-(W-1-49)),0),max(max(49-Y,Y-(H-1-49)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/10,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=406:526:shortest=1:enable='between(t,0,3)',drawtext=fontfile=fonts/Montserrat-900.ttf:text='FACT 1':fontsize=54:fontcolor=0xFFD21F:x=(w-text_w)/2:y=576-text_h/2:enable='between(t,0,3)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p titled.mp4
```

The graph blurs the region behind the title, tints it at the preset opacity, pastes it back through a
rounded, feathered mask (98% at most, so nothing is fully opaque) and draws the line. For two lines,
add a second `drawtext` with `y` moved by 62 px. For the entry animation, use the
expressions in the `text_anim_springy_pop_overshoot` text-animation preset (drawtext `fontsize`/`alpha`) or render the
title as RGBA frames with Pillow:

```python
import json, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

st = json.load(open("preset.json"))
frame = Image.open("first_frame.png").convert("RGB")
font = ImageFont.truetype("fonts/Montserrat[wght].ttf", st["font"]["size_px"])
font.set_variation_by_axes([900])  # axis order as in the font
d = ImageDraw.Draw(frame)
w = d.textlength("FACT 1", font=font)
x0 = int((frame.width - w) / 2) - 30
y_c = int(st["position"]["center_y_fraction"] * frame.height)
box = (x0, y_c - 49, frame.width - x0, y_c + 49)
frame = kit.frosted_panel(frame, box, st["backing"]["tint"], st["backing"]["opacity"], st["backing"].get("blur_px", 1), st["backing"].get("radius_px", 0), st["backing"].get("feather_px", 0))
ImageDraw.Draw(frame).text((frame.width / 2, y_c), "FACT 1", font=font, fill=st["fill"], anchor="mm",
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
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/OFL.txt
