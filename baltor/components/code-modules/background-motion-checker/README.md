# Background motion checker

Pipes downscaled grayscale frames from ffmpeg into numpy and verifies the background region moves in every 2 s window (mean frame difference above 0.6), excluding the photo box.

## Use

```python
import background_motion_checker
```

Placed by `baltor_catalog.py place background_motion_checker <step-dir>` under `.baltor/lib/background-motion-checker/`.
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
