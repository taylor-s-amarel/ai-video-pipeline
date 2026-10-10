# SRT subtitle reader and writer

Tolerant SubRip parser (BOM, CRLF, dot milliseconds, missing blank lines) and strict writer with cue validation for overlaps, empty text and too-short cues.

## Use

```python
import srt_format
```

Placed by `baltor_catalog.py place srt_format <step-dir>` under `.baltor/lib/srt-format/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
