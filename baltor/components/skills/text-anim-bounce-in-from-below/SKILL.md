---
name: "text-anim-bounce-in-from-below"
description: "Use when animating captions, titles or numbers with 'Bounce in from below': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Bounce in from below

Text animation applied per text.

## When to use
- Stickers
- cartoon labels

## Parameters

| Parameter | Value |
|---|---|
| Unit | text |
| Duration | 600 ms per unit |
| Stagger | 0 ms |
| Tempo | standard |
| Spring | stiffness 220.0, damping 12.0, mass 1 |
| Spring behaviour (computed) | damping ratio 0.405, peaks at 1.249 after 0.232 s, settles within 2% by 0.566 s |
| From -> to | {'dy_px': 120.0, 'opacity': 0.0} -> {'dy_px': 0.0, 'opacity': 1.0} |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 1.0, opacity 0.0, dy_px 120.0 |
| 150 | scale 1.0, opacity 1.0, dy_px -2.53 |
| 232 | scale 1.0, opacity 1.0, dy_px -29.9 |
| 300 | scale 1.0, opacity 1.0, dy_px -18.915 |
| 450 | scale 1.0, opacity 0.939, dy_px 7.3 |
| 600 | scale 1.0, opacity 0.996, dy_px 0.471 |

### ffmpeg drawtext (whole line)

Starting at T0 = 1.0 s, 96 px base size:

```bash
ffmpeg -y -f lavfi -i "color=c=0x0B1220:s=1080x1920:d=3:r=30" -vf \
  "drawtext=fontfile=fonts/Inter-800.ttf:text='SAMPLE':fontcolor=0xFFD21F:fontsize=96:alpha='clip((0+(1)*(1-exp(-6.0000*max(0,t-1.0))*(cos(13.5647*max(0,t-1.0))+0.4423*sin(13.5647*max(0,t-1.0))))),0,1)':x=(w-text_w)/2:y='800-text_h/2+((120+(-120)*(1-exp(-6.0000*max(0,t-1.0))*(cos(13.5647*max(0,t-1.0))+0.4423*sin(13.5647*max(0,t-1.0))))))':enable='gte(t,1.0)'" \
  -c:v libx264 -pix_fmt yuv420p preview.mp4
```

Replace `1.0` with the line's start time and 96/800 with the size and centre from the caption or title preset.

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 601, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per text: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
