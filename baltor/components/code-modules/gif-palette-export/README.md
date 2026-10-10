# GIF palette export

One-pass ffmpeg palettegen/paletteuse GIF export with validated fps, width, colour count, dither and diff-based palette statistics for crisp previews.

## Use

```python
import gif_palette_export
```

Placed by `baltor_catalog.py place gif_palette_export <step-dir>` under `.baltor/lib/gif-palette-export/`.
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
