# Cues to transcript

Converts caption cues into a paragraph transcript, removing rolling auto-caption repetition and splitting on pauses, with optional [mm:ss] timestamps.

## Use

```python
import cues_to_transcript
```

Placed by `baltor_catalog.py place cues_to_transcript <step-dir>` under `.baltor/lib/cues-to-transcript/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
