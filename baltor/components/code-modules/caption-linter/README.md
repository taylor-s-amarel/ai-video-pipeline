# Caption house-rule linter

Lints caption cues for word and line limits, duration bounds, overlaps, empty text, section labels or progress bars inside captions, and sync within 150 ms of spoken words.

## Use

```python
import caption_linter
```

Placed by `baltor_catalog.py place caption_linter <step-dir>` under `.baltor/lib/caption-linter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
