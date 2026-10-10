---
name: "title-quote-card"
description: "Use when placing a hook title or item label (FACT N, STEP N, #N) on a short in the 'Quote card' style: font, colours, backing, upper-third position over the photo, first-frame timing and computed contrast, with an ffmpeg recipe."
---

# Quote card

Title style for Vertical 9:16 (generic) (1080x1920). Palette `palette_history_archive`.

## When to use
- Verified quotations with a source

## Avoid when
- Quotes you cannot attribute to a primary or reputable source

## Parameters

| Parameter | Value |
|---|---|
| Font | Playfair Display 700, 64 px (down to 50 px), as-written |
| Fill | `#F5ECD9` |
| Outline | none |
| Backing | frosted-glass: tint `#19130C` at 72%, blur sigma 30 px, radius 28 px, feather 22 px |
| Position | center, centred at 42% of the height, over the photo, max width 86% |
| Photo | never shrink or move the photo for the title; overlay it |
| Text | 4-24 words, up to 4 line(s), about 29 characters per line |
| Timing | appears when its item starts, hold 4.5 s |
| Entry | `text_anim_word_by_word_reveal` |
| Second line | Source Sans 3 700, 40 px, `#F6B878`: attribution: name, year, source |

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| title | `#F5ECD9` | panel `#19130C` at 72%, worst case over any video | 6.28:1 | 3:1 (>= 24 px bold) |
| secondary | `#F6B878` | panel `#19130C` at 72%, worst case over any video | 4.23:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases over any video underneath (panel colour computed over pure black and pure white).

## Render it

```bash
mkdir -p fonts
curl -L -o "fonts/PlayfairDisplay[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/PlayfairDisplay[wght].ttf" wght=700 -o fonts/PlayfairDisplay-700.ttf
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=490:150:294:730,gblur=sigma=30,drawbox=x=0:y=0:w=iw:h=ih:color=0x19130C@0.72:t=fill,format=yuva420p[glass];color=c=black:s=490x150:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(28-X,X-(W-1-28)),0)*gt(max(28-Y,Y-(H-1-28)),0),(28-hypot(max(max(28-X,X-(W-1-28)),0),max(max(28-Y,Y-(H-1-28)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/22,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=294:730:shortest=1:enable='between(t,0,4.5)',drawtext=fontfile=fonts/PlayfairDisplay-700.ttf:text='YOUR HOOK HERE':fontsize=64:fontcolor=0xF5ECD9:x=(w-text_w)/2:y=806-text_h/2:enable='between(t,0,4.5)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p titled.mp4
```

The graph blurs the region behind the title, tints it at the preset opacity, pastes it back through a
rounded, feathered mask (98% at most, so nothing is fully opaque) and draws the line. For two lines,
add a second `drawtext` with `y` moved by 73 px. For the entry animation, use the
expressions in the `text_anim_word_by_word_reveal` text-animation preset (drawtext `fontsize`/`alpha`) or render the
title as RGBA frames with Pillow:

```python
import json, sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

st = json.load(open("preset.json"))
frame = Image.open("first_frame.png").convert("RGB")
font = ImageFont.truetype("fonts/PlayfairDisplay[wght].ttf", st["font"]["size_px"])
font.set_variation_by_axes([700])  # axis order as in the font
d = ImageDraw.Draw(frame)
w = d.textlength("YOUR HOOK HERE", font=font)
x0 = int((frame.width - w) / 2) - 44
y_c = int(st["position"]["center_y_fraction"] * frame.height)
box = (x0, y_c - 75, frame.width - x0, y_c + 75)
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
