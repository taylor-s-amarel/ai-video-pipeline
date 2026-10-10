# Ken Burns zoompan filter builder

Builds ffmpeg zoompan filters for eased Ken Burns zooms on a still, cropped to the output aspect and pre-scaled to remove the integer-position jitter zoompan is known for.

## Use

```python
import ken_burns_zoompan_filter
```

Placed by `baltor_catalog.py place ken_burns_zoompan_filter <step-dir>` under `.baltor/lib/ken-burns-zoompan-filter/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://ffmpeg.org/ffmpeg-filters.html#zoompan

## Licence

MIT. Original work for the Baltor public-good collection.
