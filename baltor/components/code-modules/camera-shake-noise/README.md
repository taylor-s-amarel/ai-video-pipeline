# Camera shake from smooth noise

Deterministic per-frame camera shake (x, y, rotation) from layered value noise with trauma decay, overscan calculation and an ffmpeg crop-based shake filter.

## Use

```python
import camera_shake_noise
```

Placed by `baltor_catalog.py place camera_shake_noise <step-dir>` under `.baltor/lib/camera-shake-noise/`.
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
