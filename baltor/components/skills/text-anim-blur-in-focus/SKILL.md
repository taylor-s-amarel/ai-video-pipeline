---
name: "text-anim-blur-in-focus"
description: "Use when animating captions, titles or numbers with 'Blur in to focus': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Blur in to focus

Text animation applied per text.

## When to use
- Calm and cinematic titles
- neon looks

## Parameters

| Parameter | Value |
|---|---|
| Unit | text |
| Duration | 350 ms per unit |
| Stagger | 0 ms |
| Tempo | standard |
| Keyframes | t=0, opacity=0.0, blur_px=12, scale=1.06; t=1.0, opacity=1.0, blur_px=0, scale=1.0, ease=ease-out |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 1.06, opacity 0.0, blur_px 12.0 |
| 87 | scale 1.025, opacity 0.576, blur_px 5.091 |
| 175 | scale 1.008, opacity 0.875, blur_px 1.5 |
| 262 | scale 1.001, opacity 0.984, blur_px 0.191 |
| 350 | scale 1.0, opacity 1.0 |

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 351, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per text: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
