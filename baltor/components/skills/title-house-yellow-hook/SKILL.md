---
name: "title-house-yellow-hook"
description: "Use when placing a hook title or item label (FACT N, STEP N, #N) on a short in the 'House yellow hook over the photo' style: font, colours, backing, upper-third position over the photo, first-frame timing and computed contrast, with an ffmpeg recipe."
---

# House yellow hook over the photo

Title style for Vertical 9:16 (generic) (1080x1920). Palette `palette_house_yellow_night`. Montserrat at weight 900 is a true bold, so the 3:1 large-bold contrast threshold applies. The hook is its own 2-7 word line, not a copy of the first caption. It is fully visible at 0.0 s; the settle-in animation only scales 1.04 -> 1.0.

**House rules (checked):** fill `#FFD21F`, weight >= 700, centre no lower than 40% of the height, over the main photo, visible on the first frame, frosted backing at 55-75%. A hook is its own 2-7 word line, not the first caption.

## When to use
- The first frame of every house-style short

## Avoid when
- Never move the photo or shrink it to make room; place the title over it

## Parameters

| Parameter | Value |
|---|---|
| Font | Montserrat 900, 92 px (down to 72 px), upper |
| Fill | `#FFD21F` |
| Outline | 3 px `#000000` |
| Backing | frosted-glass: tint `#0B1220` at 62%, blur sigma 28 px, radius 32 px, feather 24 px |
| Position | upper-third, centred at 24% of the height, over the photo, max width 88% |
| Photo | never shrink or move the photo for the title; overlay it |
| Text | 2-7 words, up to 2 line(s), about 14 characters per line |
| Timing | visible from frame 0, hold 2.4 s |
| Entry | `text_anim_settle_in` |

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| title | `#FFD21F` | panel `#0B1220` at 62%, worst case over any video | 3.63:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases over any video underneath (panel colour computed over pure black and pure white).

## Render it

```bash
mkdir -p fonts
curl -L -o "fonts/Montserrat[wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Montserrat[wght].ttf" wght=900 -o fonts/Montserrat-900.ttf
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=920:176:80:372,gblur=sigma=28,drawbox=x=0:y=0:w=iw:h=ih:color=0x0B1220@0.62:t=fill,format=yuva420p[glass];color=c=black:s=920x176:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(32-X,X-(W-1-32)),0)*gt(max(32-Y,Y-(H-1-32)),0),(32-hypot(max(max(32-X,X-(W-1-32)),0),max(max(32-Y,Y-(H-1-32)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/24,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=80:372:shortest=1:enable='between(t,0,2.4)',drawtext=fontfile=fonts/Montserrat-900.ttf:text='YOUR HOOK HERE':fontsize=92:fontcolor=0xFFD21F:borderw=3:bordercolor=0x000000:x=(w-text_w)/2:y=460-text_h/2:enable='between(t,0,2.4)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p titled.mp4
```

The graph blurs the region behind the title, tints it at the preset opacity, pastes it back through a
rounded, feathered mask (98% at most, so nothing is fully opaque) and draws the line. For two lines,
add a second `drawtext` with `y` moved by 105 px. For the entry animation, use the
expressions in the `text_anim_settle_in` text-animation preset (drawtext `fontsize`/`alpha`) or render the
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
w = d.textlength("YOUR HOOK HERE", font=font)
x0 = int((frame.width - w) / 2) - 40
y_c = int(st["position"]["center_y_fraction"] * frame.height)
box = (x0, y_c - 85, frame.width - x0, y_c + 85)
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
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/OFL.txt
