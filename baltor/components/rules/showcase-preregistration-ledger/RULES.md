
# Showcase pre-registration ledger

Every Baltor showcase task, the SHA-256 of its pre-registered spec and the date that spec was
registered. A run counts only if the `spec_sha256` in its record equals the hash listed here.
9 tasks (coding 4, data-cleaning 2, other 3); 9 negative controls. Study configuration:
claude-code 2.x with claude-sonnet-4-5, tools Bash, Read, Write, Edit, Glob, Grep.

## Rules

1. **Pre-register before any run.** Prompt, inputs, budget, metrics, evaluator, setup, trial count and pass
   rule are in `task.json` and `task_detail.json`, both covered by `spec_sha256`. Publish this ledger (a public
   commit is the timestamp) before the first run.
2. **Same everything except the catalogue.** Same model, harness version, tools, flags, budget (time, tool calls,
   tokens), starting workspace and fixture seed in both arms of a trial. The Baltor arm's prompt adds only the
   access addendum; nothing is pre-placed.
3. **At least 3 paired trials per arm (5 where affordable)**, in randomised order fixed before the first run.
4. **Deterministic local evaluators first.** Subjective outputs may add blind pairwise judging (labels hidden,
   order randomised). Judge scores are secondary evidence, reported separately; LLM-judge results are weaker
   than deterministic tests.
5. **Report every run**: failures, timeouts, over-budget and contaminated runs count as failures for their arm.
   No best-of-N, no selective re-runs.
6. **Effect sizes with uncertainty**: pass-rate and score differences with 95% bootstrap intervals over paired
   trials, plus win rates. Never a single best run.
7. **Negative controls** (9 tasks where Baltor should not matter) use the same protocol to
   detect placebo effects and measure search overhead.
8. **Cost next to quality**: tokens, wall time, tool calls and catalogue calls for every run.
9. **No leakage**: the catalogue served to the Baltor arm omits every `showcase_task_*` package and this ledger;
   private ground truth never sits in the workspace; a run that reads an excluded item is contaminated.
10. **Amendments are visible**: a changed spec gets a new revision, hash and date; runs under an older hash are
    reported under that revision and never pooled with the new one. Withdrawn tasks stay listed.
11. **Conflict of interest**: The tasks, the evaluators, the Baltor catalogue components available to the baltor arm and any report built from these runs come from the same team. Treat results as vendor-run evidence until an independent party reproduces them; every input needed to reproduce a run is in this package.
12. **Data licences**: no third-party dataset is copied into the repository. Kaggle tasks need the user's own
    account and rule acceptance; offline tasks use scikit-learn's bundled datasets or seeded synthetic data.

Check a placed or downloaded task package against this ledger:
`python3 verify_ledger.py path/to/showcase-task-*/` (recomputes `spec_sha256` and every file hash).

## Ledger

Hash method: spec_sha256 = sha256 of the canonical JSON of task.json without the key spec_sha256 (keys sorted, separators ',' ':', UTF-8, ensure_ascii false); task.json lists every other package file in files_sha256.

| Task id | Domain | spec_sha256 | Pre-registered | Revision | Trials/arm |
|---|---|---|---|---:|---:|
| `showcase_task_control_arithmetic_word_problems` | other · control | `70c09804612decf416b3d9da1ae336516d56931726b759413a411f4c7cf78638` | 2026-10-10 | 1 | 5 |
| `showcase_task_control_csv_two_key_sort` | data-cleaning · control | `137c3c0c6bc3d1c5ae782af27a219289102ed24918d6ebc851fd4658cb159f2c` | 2026-10-10 | 1 | 5 |
| `showcase_task_control_fizzbuzz_variant` | coding · control | `2b8b88bf5ddc669ad51c0436d8932a035356ac53d8ee20bea3c7f89229f59172` | 2026-10-10 | 1 | 5 |
| `showcase_task_control_leap_year_function` | coding · control | `8cfe5b3e2b23265f2f9fa1568834f0bac6fd3433b960195b31bfd05df68d9239` | 2026-10-10 | 1 | 5 |
| `showcase_task_control_readme_typo_fix` | other · control | `32c4cfd757ba394b37952f843f68c948500505891b8b52f63f5a0d4dddb9213e` | 2026-10-10 | 1 | 5 |
| `showcase_task_control_rename_function_refactor` | coding · control | `32e13f0a2e1fae91d76bb7435911da049c307bdb6a2d75242c9f143b373b835a` | 2026-10-10 | 1 | 5 |
| `showcase_task_control_unit_conversion_table` | other · control | `541e4f2eb14651fada71efe95ea7eafd946444e417daa956364e6d95afe6360d` | 2026-10-10 | 1 | 5 |
| `showcase_task_control_word_frequency_count` | data-cleaning · control | `d108b27a5a4609962ed10d9d37164e8bda35cb5ebc0b1c424b2083ef3930c79f` | 2026-10-10 | 1 | 5 |
| `showcase_task_control_yaml_to_json` | coding · control | `d30a247f1c9710a5ec23ef79f5223faeec362070a6ed5e9904274c8ab0c32194` | 2026-10-10 | 1 | 5 |
