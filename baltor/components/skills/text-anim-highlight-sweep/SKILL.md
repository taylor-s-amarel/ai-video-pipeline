---
name: "text-anim-highlight-sweep"
description: "Use when animating captions, titles or numbers with 'Highlighter sweep': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Highlighter sweep

Text animation applied per word.

## When to use
- Tutorials and handwritten looks

## Parameters

| Parameter | Value |
|---|---|
| Unit | word |
| Duration | 300 ms per unit |
| Stagger | 0 ms |
| Tempo | standard |
| Keyframes | t=0, reveal=0.0; t=1.0, reveal=1.0, ease=ease-out |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 1.0, opacity 1.0, reveal 0.0 |
| 75 | scale 1.0, opacity 1.0, reveal 0.578 |
| 150 | scale 1.0, opacity 1.0, reveal 0.875 |
| 225 | scale 1.0, opacity 1.0, reveal 0.984 |
| 300 | scale 1.0, opacity 1.0 |

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 301, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per word: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
