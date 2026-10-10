# xfade transition chain builder

Builds ffmpeg filter_complex chains of xfade + acrossfade transitions for N clips with correct cumulative offsets, name validation and overlap checks.

## Use

```python
import xfade_chain_builder
```

Placed by `baltor_catalog.py place xfade_chain_builder <step-dir>` under `.baltor/lib/xfade-chain-builder/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Optional external tools

- `ffmpeg`

They are imported lazily or run as subprocesses; tests that need them are skipped when absent.

## References

- https://ffmpeg.org/ffmpeg-filters.html#xfade

## Licence

MIT. Original work for the Baltor public-good collection.
