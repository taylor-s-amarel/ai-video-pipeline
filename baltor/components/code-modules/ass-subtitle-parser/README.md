# ASS subtitle parser

Parses .ass/.ssa scripts into info, styles and events using each section's Format line, with override-tag stripping to plain text and cue extraction for QA and transcripts.

## Use

```python
import ass_subtitle_parser
```

Placed by `baltor_catalog.py place ass_subtitle_parser <step-dir>` under `.baltor/lib/ass-subtitle-parser/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
