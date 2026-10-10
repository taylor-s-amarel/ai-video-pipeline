# Caption case styler

Converts caption text to UPPER, Title or Sentence case while keeping acronyms and fixed-case brand or science terms (NASA, DNA, iPhone, mRNA) intact.

## Use

```python
import caption_case_styler
```

Placed by `baltor_catalog.py place caption_case_styler <step-dir>` under `.baltor/lib/caption-case-styler/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
