# 2x2 motion grid compositor

ffmpeg filter_complex for four drifting, feather-masked panels in a 2x2 grid laid over a background at capped opacity, so a grid layer always moves and never shows hard rectangles.

## Use

```python
import motion_grid_2x2
```

Placed by `baltor_catalog.py place motion_grid_2x2 <step-dir>` under `.baltor/lib/motion-grid-2x2/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## Licence

MIT. Original work for the Baltor public-good collection.
