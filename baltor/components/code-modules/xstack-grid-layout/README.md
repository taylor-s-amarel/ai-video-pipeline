# xstack grid layout builder

Computes rows x columns grids with gutters and margins (even cell sizes) and the matching ffmpeg xstack filter with cover-cropped cells and padded full-frame output.

## Use

```python
import xstack_grid_layout
```

Placed by `baltor_catalog.py place xstack_grid_layout <step-dir>` under `.baltor/lib/xstack-grid-layout/`.
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
