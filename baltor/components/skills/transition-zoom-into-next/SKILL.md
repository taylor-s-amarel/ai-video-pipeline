---
name: "transition-zoom-into-next"
description: "Use when joining two shots of a short with the 'Zoom into the next shot' transition: exact ffmpeg xfade or concat command with the right offset, duration and tempo, and when not to use it."
---

# Zoom into the next shot

`xfade` transition `zoomin`, 350 ms, tempo standard.

## When to use
- Going deeper into a detail
- Hype intros

## Avoid when
- Back-to-back use (feels repetitive)

## Render it

```bash
A=$(ffprobe -v error -show_entries format=duration -of csv=p=0 A.mp4)
OFF=$(awk -v a="$A" 'BEGIN { printf "%.3f", a - 0.35 }')
ffmpeg -y -i A.mp4 -i B.mp4 -filter_complex \
  "[0:v]settb=AVTB,fps=30,format=yuv420p,setsar=1[a];[1:v]settb=AVTB,fps=30,format=yuv420p,setsar=1[b];[a][b]xfade=transition=zoomin:duration=0.35:offset=${OFF}[v]" \
  -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p joined.mp4
```

`xfade` needs both clips at the same size, frame rate and pixel format, and an `offset` equal to the first clip's length minus the transition (0.35 s). The result is 0.35 s shorter than the two clips together. For audio use `acrossfade=d=0.35` on the same pair.

For many clips, `short_style_preset_kit.xfade_chain(durations, transitions)` writes the whole graph with correct offsets:

```python
import sys
sys.path.insert(0, ".baltor/lib/short-style-preset-kit")  # where `place` puts the short_style_preset_kit module
import style_kit as kit
graph, total = kit.xfade_chain([4.0, 3.5, 5.0], [{"xfade": "zoomin", "duration_ms": 350}, {"cut": True}])
print(total)   # seconds after joining
```

## Check it

```bash
python3 scripts/check_preset.py   # schema, 0.98 opacity cap, contrast recomputed from the colours
```

`schema.json` is a copy of the `transition_preset_schema` contract schema, so the check runs without the catalogue.

## Sources
- ffmpeg xfade and concat filters: https://ffmpeg.org/ffmpeg-filters.html
