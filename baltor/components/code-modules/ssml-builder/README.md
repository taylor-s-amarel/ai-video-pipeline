# SSML builder

Builds valid, escaped SSML 1.1 (speak, break, prosody, emphasis, say-as, sub, phoneme) with value validation, plus a stripper that turns SSML back into plain text for engines without SSML.

## Use

```python
import ssml_builder
```

Placed by `baltor_catalog.py place ssml_builder <step-dir>` under `.baltor/lib/ssml-builder/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## References

- https://www.w3.org/TR/speech-synthesis11/

## Licence

MIT. Original work for the Baltor public-good collection.
