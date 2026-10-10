# WebVTT writer and reader

Writes WebVTT with identifiers, validated cue settings and entity escaping; reads cues while skipping NOTE/STYLE/REGION blocks and optionally stripping inline tags.

## Use

```python
import webvtt_format
```

Placed by `baltor_catalog.py place webvtt_format <step-dir>` under `.baltor/lib/webvtt-format/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## References

- https://www.w3.org/TR/webvtt1/

## Licence

MIT. Original work for the Baltor public-good collection.
