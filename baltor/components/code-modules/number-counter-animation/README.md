# Number counter animation

Eased count-up/count-down frames with thousands separators, decimals, prefix and suffix that land exactly on the final number, plus a self-evaluating ffmpeg drawtext counter.

## Use

```python
import number_counter_animation
```

Placed by `baltor_catalog.py place number_counter_animation <step-dir>` under `.baltor/lib/number-counter-animation/`.
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
