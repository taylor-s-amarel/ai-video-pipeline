# SMPTE timecode conversion

Converts frames to and from HH:MM:SS:FF timecode, including 29.97 and 59.94 drop-frame, with validation of labels that do not exist in drop-frame.

## Use

```python
import smpte_timecode
```

Placed by `baltor_catalog.py place smpte_timecode <step-dir>` under `.baltor/lib/smpte-timecode/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
