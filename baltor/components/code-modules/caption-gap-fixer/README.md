# Caption timing gap fixer

Repairs caption timing by trimming overlaps, closing flicker gaps, enforcing a minimum frame gap and duration, and snapping cue times to the video frame grid.

## Use

```python
import caption_gap_fixer
```

Placed by `baltor_catalog.py place caption_gap_fixer <step-dir>` under `.baltor/lib/caption-gap-fixer/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
