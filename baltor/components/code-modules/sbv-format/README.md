# YouTube SBV caption format

Reads and writes the SBV caption format (H:MM:SS.mmm,H:MM:SS.mmm blocks) exported and accepted by YouTube Studio.

## Use

```python
import sbv_format
```

Placed by `baltor_catalog.py place sbv_format <step-dir>` under `.baltor/lib/sbv-format/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
