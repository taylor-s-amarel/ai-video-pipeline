---
name: "palette-history-archive"
description: "Use when choosing colours for a short ('History archive'): role colours, frosted panel tint and opacity, and only text/background pairs that pass WCAG contrast (worst case over any video)."
---

# History archive

Battles, eras and biographies with a dark sepia base. Mode: dark. Frosted panels use `#19130C` at 72%.

## Colours

| Role | Hex |
|---|---|
| background | `#1E1710` |
| surface | `#2E241A` |
| panel_tint | `#19130C` |
| text | `#F5ECD9` |
| title | `#E8C27A` |
| keyword | `#F6B878` |
| accent | `#B08D57` |
| accent_2 | `#6E8B9C` |
| stroke | `#0E0A06` |
| light | `#F3D9A4` |
| particle | `#F5ECD9` |

Gradient: `#1E1710` -> `#4A3A28`. Five-stop ramp for recolouring procedural backgrounds:
`#0E0A06`, `#1E1710`, `#4A3A28`, `#B08D57`, `#F5ECD9` (dark to light).

## Text pairs that pass

| Text | On | Ratio | Use |
|---|---|---|---|
| text `#F5ECD9` | panel_tint@panel `#19130C` at 72% | 6.28:1 | any-size |
| title `#E8C27A` | panel_tint@panel `#19130C` at 72% | 4.36:1 | large-bold-only |
| keyword `#F6B878` | panel_tint@panel `#19130C` at 72% | 4.23:1 | large-bold-only |
| text `#F5ECD9` | background `#1E1710` | 15.08:1 | any-size |
| title `#E8C27A` | background `#1E1710` | 10.48:1 | any-size |
| keyword `#F6B878` | background `#1E1710` | 10.16:1 | any-size |
| accent `#B08D57` | background `#1E1710` | 5.73:1 | any-size |
| text `#F5ECD9` | surface `#2E241A` | 12.92:1 | any-size |
| keyword `#F6B878` | surface `#2E241A` | 8.70:1 | any-size |
| text `#F5ECD9` | stroke `#0E0A06` | 16.79:1 | any-size |
| title `#E8C27A` | stroke `#0E0A06` | 11.67:1 | any-size |
| background `#1E1710` | keyword@card95 `#F6B878` at 95% | 9.15:1 | any-size |
| background `#1E1710` | title@card95 `#E8C27A` at 95% | 9.43:1 | any-size |
| background `#1E1710` | accent@card95 `#B08D57` at 95% | 5.21:1 | any-size |

`any-size` pairs reach 4.5:1. `large-bold-only` pairs reach 3:1 and may only be used for text that is at least
24 px and weight 700. Ratios on `@panel` and `@card95` backgrounds are worst cases over any video underneath.
0 candidate pair(s) fell below 3:1 and are deliberately not listed; do not use them for text.

## Apply it

- ffmpeg: `drawtext=...:fontcolor=0xF5ECD9` for captions, `fontcolor=0xE8C27A` for titles;
  frosted panels: `drawbox=...:color=0x19130C@0.72:t=fill` over a blurred crop.
- Pillow: `ImageDraw.text(..., fill="#F5ECD9")`; `kit.frosted_panel(frame, box, "#19130C", 0.72)`.
- Backgrounds: the `bg_layer_*_in_history_archive` variants are the procedural backgrounds recoloured with this ramp.

Recompute any pair yourself:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
print(kit.panel_contrast("#F5ECD9", "#19130C", 0.72))
print(round(kit.contrast_ratio("#F5ECD9", "#1E1710"), 2))
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `palette_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- WCAG contrast minimum: https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum
- Relative luminance definition: https://www.w3.org/WAI/WCAG22/Understanding/relative-luminance.html
