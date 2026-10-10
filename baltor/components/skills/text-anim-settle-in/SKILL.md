---
name: "text-anim-settle-in"
description: "Use when animating captions, titles or numbers with 'Settle in (visible from frame 0)': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Settle in (visible from frame 0)

Text animation applied per text.

## When to use
- First-frame titles that must be readable at 0.0 s

## Parameters

| Parameter | Value |
|---|---|
| Unit | text |
| Duration | 300 ms per unit |
| Stagger | 0 ms |
| Tempo | standard |
| Keyframes | t=0, scale=1.04, opacity=1.0; t=1.0, scale=1.0, opacity=1.0, ease=ease-out |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 1.04, opacity 1.0 |
| 75 | scale 1.017, opacity 1.0 |
| 150 | scale 1.005, opacity 1.0 |
| 225 | scale 1.001, opacity 1.0 |
| 300 | scale 1.0, opacity 1.0 |

### ffmpeg drawtext (whole line)

Starting at T0 = 1.0 s, 96 px base size:

```bash
ffmpeg -y -f lavfi -i "color=c=0x0B1220:s=1080x1920:d=3:r=30" -vf \
  "drawtext=fontfile=fonts/Inter-800.ttf:text='SAMPLE':fontcolor=0xFFD21F:fontsize='96*(if(lt(clip((t-1.0)/0.3,0,1),0),1.04,if(lt(clip((t-1.0)/0.3,0,1),1),(1.04+(-0.04)*(1-pow(1-(((clip((t-1.0)/0.3,0,1))-0)/1),3))),1)))':alpha='if(lt(clip((t-1.0)/0.3,0,1),0),1,if(lt(clip((t-1.0)/0.3,0,1),1),(1+(0)*(1-pow(1-(((clip((t-1.0)/0.3,0,1))-0)/1),3))),1))':x=(w-text_w)/2:y=800-text_h/2:enable='gte(t,1.0)'" \
  -c:v libx264 -pix_fmt yuv420p preview.mp4
```

Replace `1.0` with the line's start time and 96/800 with the size and centre from the caption or title preset.

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 301, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per text: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
