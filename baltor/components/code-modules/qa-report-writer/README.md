# QA report writer

Collects pass/fail/not-checked QA results and writes them as a Markdown table, JSON with totals and JUnit XML, never counting unchecked items as passes.

## Use

```python
import qa_report_writer
```

Placed by `baltor_catalog.py place qa_report_writer <step-dir>` under `.baltor/lib/qa-report-writer/`.
Add that directory to `sys.path` (or copy the module next to your script).

## Test

```sh
python3 -m pytest -q .
```

## Licence

MIT. Original work for the Baltor public-good collection.
