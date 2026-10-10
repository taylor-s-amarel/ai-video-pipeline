---
name: "text-anim-word-by-word-reveal"
description: "Use when animating captions, titles or numbers with 'Word-by-word reveal': keyframes or spring constants, computed samples, and ffmpeg drawtext or Pillow instructions."
---

# Word-by-word reveal

Text animation applied per word.

## When to use
- Quotes
- read-along narration

## Parameters

| Parameter | Value |
|---|---|
| Unit | word |
| Duration | 140 ms per unit |
| Stagger | 220 ms |
| Tempo | standard |
| Keyframes | t=0, opacity=0.0, dy_px=10; t=1.0, opacity=1.0, dy_px=0, ease=ease-out |
| Timing source | word timestamps when available, otherwise stagger_ms |

Scale, opacity and offsets multiply the text layer's own values; the text layer's opacity stays at or below 0.98.

## Computed samples

| t (ms) | State of the first unit |
|---|---|
| 0 | scale 1.0, opacity 0.0, dy_px 10.0 |
| 35 | scale 1.0, opacity 0.578, dy_px 4.219 |
| 70 | scale 1.0, opacity 0.875, dy_px 1.25 |
| 105 | scale 1.0, opacity 0.984, dy_px 0.156 |
| 140 | scale 1.0, opacity 1.0 |

### Pillow (any unit)

```python
import json, sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
anim = json.load(open("preset.json"))
for t_ms in range(0, 801, 33):
    states = kit.text_anim_state(anim, t_ms, n_units=4)   # one dict per word: scale, opacity, dy_px, reveal, ...
    # draw each unit with its state (resize the glyph by scale about its centre, multiply alpha by opacity)
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `text_animation_preset_schema` contract schema, so the check runs without the catalogue.
