# ffmpeg detector log parser

Runs ffmpeg blackdetect, freezedetect and silencedetect in one pass (plus cropdetect) and parses their logs into events for QA of black gaps, frozen video, dead air and letterboxing.

## Use

```python
import ffmpeg_detect_log_parser
```

Placed by `baltor_catalog.py place ffmpeg_detect_log_parser <step-dir>` under `.baltor/lib/ffmpeg-detect-log-parser/`.
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
