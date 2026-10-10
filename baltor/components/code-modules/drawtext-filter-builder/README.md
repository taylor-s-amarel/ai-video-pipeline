# drawtext filter builder

Builds ffmpeg drawtext filters that render any literal text safely (expansion off, two-level escaping) with colour/opacity, border, shadow, backing box, time window and alpha fades.

## Use

```python
import drawtext_filter_builder
```

Placed by `baltor_catalog.py place drawtext_filter_builder <step-dir>` under `.baltor/lib/drawtext-filter-builder/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://ffmpeg.org/ffmpeg-filters.html#drawtext-1

## Licence

MIT. Original work for the Baltor public-good collection.
