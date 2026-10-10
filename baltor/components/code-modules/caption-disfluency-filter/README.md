# Caption disfluency filter

Removes filler words, immediate repeats and stutter fragments from transcripts (optionally discourse markers), normalises punctuation and keeps word timings for captions.

## Use

```python
import caption_disfluency_filter
```

Placed by `baltor_catalog.py place caption_disfluency_filter <step-dir>` under `.baltor/lib/caption-disfluency-filter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
