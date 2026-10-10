---
name: "text-anim-kinetic-slam"
description: "Use when animating captions, titles or numbers with 'Kinetic slam': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Kinetic slam

Text animation applied per text.

## When to use
- Hooks
- rank numbers
- punchlines

## Parameters

| Parameter | Value |
|---|---|
| Unit | text |
| Duration | 220 ms per unit |
| Stagger | 0 ms |
| Tempo | standard |
| Keyframes | t=0, scale=2.4, opacity=0.0; t=0.2, opacity=1.0; t=0.7, scale=0.94, ease=ease-in; t=1.0, scale=1.0, ease=ease-out |
| Shake | 6 px for 3 frames after landing |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 2.4, opacity 0.0 |
| 55 | scale 2.333, opacity 1.0 |
| 110 | scale 1.868, opacity 1.0 |
| 165 | scale 0.965, opacity 1.0 |
| 220 | scale 1.0, opacity 1.0 |

### ffmpeg drawtext (whole line)

Starting at T0 = 1.0 s, 96 px base size:

```bash
ffmpeg -y -f lavfi -i "color=c=0x0B1220:s=1080x1920:d=3:r=30" -vf \
  "drawtext=fontfile=fonts/Inter-800.ttf:text='SAMPLE':fontcolor=0xFFD21F:fontsize='96*(if(lt(clip((t-1.0)/0.22,0,1),0),2.4,if(lt(clip((t-1.0)/0.22,0,1),0.7),(2.4+(-1.46)*pow(((clip((t-1.0)/0.22,0,1))-0)/0.7,3)),if(lt(clip((t-1.0)/0.22,0,1),1),(0.94+(0.06)*(1-pow(1-(((clip((t-1.0)/0.22,0,1))-0.7)/0.3),3))),1))))':alpha='if(lt(clip((t-1.0)/0.22,0,1),0),0,if(lt(clip((t-1.0)/0.22,0,1),0.2),(0+(1)*(((clip((t-1.0)/0.22,0,1))-0)/0.2)),1))':x=(w-text_w)/2:y=800-text_h/2:enable='gte(t,1.0)'" \
  -c:v libx264 -pix_fmt yuv420p preview.mp4
```

Replace `1.0` with the line's start time and 96/800 with the size and centre from the caption or title preset.

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 221, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per text: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
