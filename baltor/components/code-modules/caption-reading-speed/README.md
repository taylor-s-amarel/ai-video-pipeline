# Caption reading-speed checker

Measures characters per second and words per minute per caption, flags too-fast, too-short and lingering cues, and extends fast cues into free time without overlaps.

## Use

```python
import caption_reading_speed
```

Placed by `baltor_catalog.py place caption_reading_speed <step-dir>` under `.baltor/lib/caption-reading-speed/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
