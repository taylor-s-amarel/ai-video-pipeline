# Pronunciation lexicon for TTS

Fixes mispronounced names with whole-word, case-aware respelling before synthesis and exports W3C PLS 1.0 lexicons (alias or IPA) plus JSON for reuse across projects.

## Use

```python
import pronunciation_lexicon
```

Placed by `baltor_catalog.py place pronunciation_lexicon <step-dir>` under `.baltor/lib/pronunciation-lexicon/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## References

- https://www.w3.org/TR/pronunciation-lexicon/

## Licence

MIT. Original work for the Baltor public-good collection.
