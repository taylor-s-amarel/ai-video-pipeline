# TTML caption writer and reader

Writes well-formed TTML 1.0 caption documents (styled bottom region, escaped text, line breaks) and reads clock-time or offset-time cues back.

## Use

```python
import ttml_writer
```

Placed by `baltor_catalog.py place ttml_writer <step-dir>` under `.baltor/lib/ttml-writer/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## References

- https://www.w3.org/TR/ttml1/

## Licence

MIT. Original work for the Baltor public-good collection.
