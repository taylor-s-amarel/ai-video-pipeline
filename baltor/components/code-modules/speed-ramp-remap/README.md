# Speed ramp time remapping

Maps output time to source time from linearly interpolated speed keyframes (exact integral), with per-frame source indices, duration solving and setpts helpers.

## Use

```python
import speed_ramp_remap
```

Placed by `baltor_catalog.py place speed_ramp_remap <step-dir>` under `.baltor/lib/speed-ramp-remap/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
