# ffmpeg raw frame pipe

Context-managed numpy frame reader and writer over ffmpeg pipes (scale, fps, pixel formats, optional audio mux) with shape checks and ffmpeg errors surfaced, for Python frame effects.

## Use

```python
import ffmpeg_raw_frame_pipe
```

Placed by `baltor_catalog.py place ffmpeg_raw_frame_pipe <step-dir>` under `.baltor/lib/ffmpeg-raw-frame-pipe/`.
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
