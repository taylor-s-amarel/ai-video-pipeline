# ffmpeg progress parser

Parses ffmpeg -progress key=value blocks into frame, fps, output time, speed, percent and ETA, and runs a render with a progress callback (no shell).

## Use

```python
import ffmpeg_progress_parser
```

Placed by `baltor_catalog.py place ffmpeg_progress_parser <step-dir>` under `.baltor/lib/ffmpeg-progress-parser/`.
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
