# Amplitude-driven lip sync

Per-frame mouth openness from narration loudness (gated, normalised, attack/release smoothed) quantised to Rhubarb-style mouth letters with a minimum hold.

## Use

```python
import amplitude_lip_sync
```

Placed by `baltor_catalog.py place amplitude_lip_sync <step-dir>` under `.baltor/lib/amplitude-lip-sync/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
