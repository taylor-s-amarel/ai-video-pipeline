# Ken Burns frame renderer

Renders crop-rectangle paths from a still into output frames with sub-pixel accurate Pillow EXTENT transforms (no zoom jitter), optional supersampling and an ffmpeg pipe argv.

## Use

```python
import ken_burns_frame_renderer
```

Placed by `baltor_catalog.py place ken_burns_frame_renderer <step-dir>` under `.baltor/lib/ken-burns-frame-renderer/`.
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
