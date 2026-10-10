# Stepped timing and stop-motion holds

CSS steps() timing with all jump positions, plus on-twos/threes frame holds and an ffmpeg filter for a choppy hand-animated look.

## Use

```python
import steps_timing
```

Placed by `baltor_catalog.py place steps_timing <step-dir>` under `.baltor/lib/steps-timing/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## References

- https://www.w3.org/TR/css-easing-1/

## Licence

MIT. Original work for the Baltor public-good collection.
