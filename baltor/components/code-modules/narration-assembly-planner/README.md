# Narration assembly planner

Places TTS chunks on one timeline with sentence, paragraph and section pauses, shifts chunk word times to global caption times and builds the ffmpeg adelay+amix command.

## Use

```python
import narration_assembly_planner
```

Placed by `baltor_catalog.py place narration_assembly_planner <step-dir>` under `.baltor/lib/narration-assembly-planner/`.
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
