---
name: "text-anim-mask-reveal-up"
description: "Use when animating captions, titles or numbers with 'Mask reveal from the baseline': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Mask reveal from the baseline

Text animation applied per line.

## When to use
- Lower thirds
- elegant captions

## Parameters

| Parameter | Value |
|---|---|
| Unit | line |
| Duration | 350 ms per unit |
| Stagger | 80 ms |
| Tempo | standard |
| Keyframes | t=0, reveal=0.0, dy_px=24; t=1.0, reveal=1.0, dy_px=0, ease=ease-out |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 1.0, opacity 1.0, dy_px 24.0, reveal 0.0 |
| 87 | scale 1.0, opacity 1.0, dy_px 10.183, reveal 0.576 |
| 175 | scale 1.0, opacity 1.0, dy_px 3.0, reveal 0.875 |
| 262 | scale 1.0, opacity 1.0, dy_px 0.381, reveal 0.984 |
| 350 | scale 1.0, opacity 1.0 |

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 591, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per line: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
