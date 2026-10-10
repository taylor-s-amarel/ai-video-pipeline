---
name: "text-anim-springy-pop-overshoot"
description: "Use when animating captions, titles or numbers with 'Springy pop with overshoot': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Springy pop with overshoot

Text animation applied per word.

## When to use
- Captions and labels that should feel lively

## Parameters

| Parameter | Value |
|---|---|
| Unit | word |
| Duration | 450 ms per unit |
| Stagger | 60 ms |
| Tempo | standard |
| Spring | stiffness 300.0, damping 18.0, mass 1 |
| Spring behaviour (computed) | damping ratio 0.52, peaks at 1.148 after 0.212 s, settles within 2% by 0.45 s |
| From -> to | {'scale': 0.0, 'opacity': 0.0} -> {'scale': 1.0, 'opacity': 1.0} |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 0.0, opacity 0.0 |
| 112 | scale 0.81, opacity 0.81 |
| 212 | scale 1.148, opacity 1.0 |
| 225 | scale 1.145, opacity 1.0 |
| 337 | scale 1.015, opacity 1.0 |
| 450 | scale 0.98, opacity 0.98 |

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 631, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per word: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
