---
name: "palette-neon-night"
description: "Use when choosing colours for a short ('Neon night'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# Neon night

AI explainers and synthwave looks. Mode: dark. Frosted panels use `#12062B` at 66%.

## Colours

| Role | Hex |
|---|---|
| background | `#0B0221` |
| surface | `#1A0838` |
| panel_tint | `#12062B` |
| text | `#FFFFFF` |
| title | `#FFE45E` |
| keyword | `#00F0FF` |
| accent | `#FF2E97` |
| accent_2 | `#7A1FA2` |
| stroke | `#0B0221` |
| light | `#FF2E97` |
| particle | `#FFB3E1` |

Gradient: `#0B0221` -> `#2B0A4F`. Five-stop ramp for recolouring procedural backgrounds:
`#0B0221`, `#2B0A4F`, `#7A1FA2`, `#FF2E97`, `#FFE8F5` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#FFFFFF` | panel_tint@panel `#12062B` at 66% | 6.44:1 | any-size |
| title `#FFE45E` | panel_tint@panel `#12062B` at 66% | 5.06:1 | any-size |
| keyword `#00F0FF` | panel_tint@panel `#12062B` at 66% | 4.57:1 | any-size |
| text `#FFFFFF` | background `#0B0221` | 20.09:1 | any-size |
| title `#FFE45E` | background `#0B0221` | 15.80:1 | any-size |
| keyword `#00F0FF` | background `#0B0221` | 14.26:1 | any-size |
| accent `#FF2E97` | background `#0B0221` | 5.82:1 | any-size |
| text `#FFFFFF` | surface `#1A0838` | 18.48:1 | any-size |
| keyword `#00F0FF` | surface `#1A0838` | 13.12:1 | any-size |
| text `#FFFFFF` | stroke `#0B0221` | 20.09:1 | any-size |
| title `#FFE45E` | stroke `#0B0221` | 15.80:1 | any-size |
| background `#0B0221` | keyword@card95 `#00F0FF` at 95% | 12.80:1 | any-size |
| background `#0B0221` | title@card95 `#FFE45E` at 95% | 14.17:1 | any-size |
| background `#0B0221` | accent@card95 `#FF2E97` at 95% | 5.30:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xFFFFFF` for captions, `fontcolor=0xFFE45E` for titles;
  frosted panels: `drawbox=...:color=0x12062B@0.66:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#FFFFFF")`; `kit.frosted_panel(frame, box, "#12062B", 0.66)`.
- Backgrounds: the `bg_layer_*_in_neon_night` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#FFFFFF", "#12062B", 0.66))
print(round(kit.contrast_ratio("#FFFFFF", "#0B0221"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
