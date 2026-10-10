# Narration timing planner

Estimates narration length from words per minute and sentence pauses, solves the rate for a target length and tells you how many words to add or cut to land 60-90 s.

## Use

```python
import narration_timing_planner
```

Placed by `baltor_catalog.py place narration_timing_planner <step-dir>` under `.baltor/lib/narration-timing-planner/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
