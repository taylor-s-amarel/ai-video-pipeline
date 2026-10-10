# Storyboard grid exporter

Builds storyboard/contact sheets with Pillow (frames in a grid with timestamp and note captions, optional title) plus timestamp pickers and the ffmpeg frame-extract command.

## Use

```python
import storyboard_grid_exporter
```

Placed by `baltor_catalog.py place storyboard_grid_exporter <step-dir>` under `.baltor/lib/storyboard-grid-exporter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
