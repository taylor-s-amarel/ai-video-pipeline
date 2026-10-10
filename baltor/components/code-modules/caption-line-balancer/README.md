# Caption line balancer

Splits a caption into one or two lines of balanced rendered width measured with the real font via Pillow, avoiding function-word and number-unit breaks.

## Use

```python
import caption_line_balancer
```

Placed by `baltor_catalog.py place caption_line_balancer <step-dir>` under `.baltor/lib/caption-line-balancer/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
