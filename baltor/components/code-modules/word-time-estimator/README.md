# Word timing estimator

Estimates per-word times inside a timed segment from English syllable counts, number readings and punctuation pauses when no forced aligner is available.

## Use

```python
import word_time_estimator
```

Placed by `baltor_catalog.py place word_time_estimator <step-dir>` under `.baltor/lib/word-time-estimator/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
