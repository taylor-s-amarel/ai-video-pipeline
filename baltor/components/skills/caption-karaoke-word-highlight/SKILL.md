---
name: "caption-karaoke-word-highlight"
description: "Use when adding synced captions to a vertical short and you want the 'Karaoke word highlight' look: exact font, size, colours, backing, safe-area position, keyword emphasis and timing, with WCAG contrast already computed and an ffmpeg/Pillow recipe."
---

# Karaoke word highlight

Caption style for Vertical 9:16 (generic) (1080x1920). Palette `palette_house_yellow_night`. The word being spoken sits in a rounded keyword-colour box with dark text; the box moves word to word.

## When to use
- Narration with word timestamps from TTS or alignment
- Language learning and read-along content

## Avoid when
- No word-level timestamps (the box would drift from the voice)

## Parameters

| Parameter | Value |
|---|---|
| Font | Inter 800, 58 px (shrink to 46 px before wrapping), as-written |
| Fill | `#FFFFFF` |
| Backing | frosted glass: tint `#0B1220` at 62%, blur sigma 24 px, radius 24 px, padding 20/32 px, feather 14 px |
| Outline | none |
| Position | centre at 76% of the height, max width 88%, aligned center |
| Safe area | top 8%, bottom 20%, left 6%, right 6% |
| Lines | 1 line(s), at most 6 words and about 31 characters per line |
| Keyword | box-current-word: colour `#FFD21F`, scale to 1.04x and back over 120 ms (ease-out), text `#0B1220` in a 95% box |
| Timing | within 100 ms of the spoken word; on screen 700-3000 ms |
| Entry | `text_anim_fade_up_soft` |

All numbers are in `preset.json`. Sizes are pixels at 1080x1920.

## Contrast (WCAG 2.x, computed)

| Pair | Text | Against | Ratio | Needs |
|---|---|---|---|---|
| text | `#FFFFFF` | panel `#0B1220` at 62%, worst case over any video | 5.26:1 | 3:1 (>= 24 px bold) |
| keyword_box | `#0B1220` | panel `#FFD21F` at 95%, worst case over any video | 11.60:1 | 3:1 (>= 24 px bold) |

Panel ratios are worst cases: the panel colour is computed over pure black and pure white video, so no
frame underneath can make the text less readable than this. Thresholds: 4.5:1, or 3:1 only for text that
is at least 24 px and weight 700 (stricter than WCAG's large-text rule). See https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.

## Render it

### 1. Fonts (OFL-1.1)

```bash
mkdir -p fonts
curl -L -o "fonts/Inter[opsz,wght].ttf" "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
pip install fonttools   # one-off: make a static weight for ffmpeg drawtext
python3 -m fontTools.varLib.instancer "fonts/Inter[opsz,wght].ttf" wght=800 -o fonts/Inter-800.ttf
```

### 2. One static line with ffmpeg

Draws the panel and line from 0.5 s to 2.5 s over `in.mp4` (1080x1920). Replace the text and times
per caption (one `enable` window per line), or generate the graph per line from `preset.json`.

```bash
ffmpeg -y -i in.mp4 -filter_complex "[0:v]split=2[base][src];[src]crop=770:114:154:1404,gblur=sigma=24,drawbox=x=0:y=0:w=iw:h=ih:color=0x0B1220@0.62:t=fill,format=yuva420p[glass];color=c=black:s=770x114:r=30:d=1,trim=end_frame=1,format=gray,geq=lum='255*0.98*clip(if(gt(max(24-X,X-(W-1-24)),0)*gt(max(24-Y,Y-(H-1-24)),0),(24-hypot(max(max(24-X,X-(W-1-24)),0),max(max(24-Y,Y-(H-1-24)),0))),min(min(X,W-1-X),min(Y,H-1-Y)))/14,0,1)',loop=loop=-1:size=1:start=0,setpts=N/(30*TB)[mask];[glass][mask]alphamerge[panel];[base][panel]overlay=154:1404:shortest=1:enable='between(t,0.5,2.5)',drawtext=fontfile=fonts/Inter-800.ttf:text='One synced line at a time':fontsize=58:fontcolor=0xFFFFFF:x=(w-text_w)/2:y=1461-text_h/2:enable='between(t,0.5,2.5)'[v]" \
  -map "[v]" -map "0:a?" -c:a copy -c:v libx264 -crf 18 -pix_fmt yuv420p captioned.mp4
```

### 3. Per-word effects with Pillow

ffmpeg's drawtext cannot pop one word inside a line. Render those frames with Pillow:

```python
import json, sys
from PIL import Image
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit

style = json.load(open("preset.json"))
frame = Image.open("frame.png").convert("RGB")          # a 1080x1920 frame from your video
words = "One synced line at a time".split()
out = kit.render_caption_preview(frame, words, style, keyword_index=1, t_ms=90,
                                 font_path="fonts/Inter-800.ttf", margins=style["target"]["safe_margins"])
out.save("caption_preview.png")
```

For a full video, extract frames (`ffmpeg -i in.mp4 frames/%06d.png`), draw each caption on the frames inside
its time window with `t_ms` measured from the keyword's start, then encode
(`ffmpeg -framerate 30 -i frames/%06d.png -i in.mp4 -map 0:v -map 1:a? -c:v libx264 -pix_fmt yuv420p out.mp4`).

The `short_style_preset_kit` code module has the maths used here (contrast, easing, springs, zoompan, xfade chains, grids, layer stacks, Pillow frosted panels). Place it with `python3 baltor/tools/baltor_catalog.py place short_style_preset_kit <step-dir>`; it lands in `.baltor/lib/short-style-preset-kit/`.

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `caption_style_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
- ffmpeg filters (drawtext, gblur, alphamerge, overlay): https://ffmpeg.org/ffmpeg-filters.html
- Font licence: https://raw.githubusercontent.com/google/fonts/main/ofl/inter/OFL.txt
