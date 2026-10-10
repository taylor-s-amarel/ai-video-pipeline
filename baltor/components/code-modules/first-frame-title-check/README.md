# First-frame title check

Finds the house-yellow (#FFD21F) hook title on a render's first frame with colour tolerance and checks it exists, sits in the upper 40% and is title-sized.

## Use

```python
import first_frame_title_check
```

Placed by `baltor_catalog.py place first_frame_title_check <step-dir>` under `.baltor/lib/first-frame-title-check/`.
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
