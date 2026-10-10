# Render manifest writer

Records every render input and output with SHA-256 and size plus params, tool versions and credits; verifies files later and flags outputs re-delivered under a different job.

## Use

```python
import render_manifest_writer
```

Placed by `baltor_catalog.py place render_manifest_writer <step-dir>` under `.baltor/lib/render-manifest-writer/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
