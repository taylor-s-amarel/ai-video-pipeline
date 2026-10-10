# ffprobe media info

Runs ffprobe without a shell and summarises streams into typed fields (duration, codecs, rotation-corrected size, fps, VFR flag, audio rate and channels), with a pure summariser for tests.

## Use

```python
import ffprobe_media_info
```

Placed by `baltor_catalog.py place ffprobe_media_info <step-dir>` under `.baltor/lib/ffprobe-media-info/`.
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
