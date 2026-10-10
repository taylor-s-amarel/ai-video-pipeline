---
name: "text-anim-typewriter"
description: "Use when animating captions, titles or numbers with 'Typewriter': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Typewriter

Text animation applied per character.

## When to use
- Archive documents
- dates
- code

## Parameters

| Parameter | Value |
|---|---|
| Unit | character |
| Duration | 1 ms per unit |
| Stagger | 55 ms |
| Tempo | standard |
| Keyframes | t=0, opacity=0.0; t=1.0, opacity=1.0, ease=step |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 1.0, opacity 0.0 |
| 1 | scale 1.0, opacity 1.0 |

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 167, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per character: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
