# Keyword pop ASS tag builder

Builds ASS caption text where the key word scales 1.0->1.12->1.0 over 180 ms when spoken and turns house yellow, with all other text escaped against tag injection.

## Use

```python
import keyword_pop_ass_tags
```

Placed by `baltor_catalog.py place keyword_pop_ass_tags <step-dir>` under `.baltor/lib/keyword-pop-ass-tags/`.
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
