
# Showcase pre-registration ledger

Every Baltor showcase task, the SHA-256 of its pre-registered spec and the date that spec was
registered. A run record is admissible only if the `spec_hash` its evaluator printed equals the
hash listed here for that task. 9 tasks (negative-control 9); 9 negative controls.

## Rules

1. **Pre-register before any run.** Prompt, inputs, budget, metrics, evaluator and setup file hashes,
   trial count and pass rule live in `task.json` and are covered by its spec hash. Commit and publish this
   ledger before the first run; the public commit is the timestamp.
2. **Same everything except the catalogue.** Same model and settings, harness version, budget (time, tool
   calls, tokens), starting workspace and fixture seed in both arms. The treatment prompt adds one sentence
   saying the catalogue exists; nothing is pre-placed.
3. **At least 3 paired trials per arm (5 where affordable).** Arm order per trial and fixture seeds come
   from the spec hash (`showcase_eval.run_plan`), so nobody chooses them after seeing results.
4. **Deterministic local evaluators first.** Subjective outputs may add blind pairwise judging (labels hidden,
   order randomised); those results are secondary evidence and reported separately. LLM-judge results are
   weaker evidence than deterministic tests.
5. **Report every run**, including failures, timeouts, contaminated runs and losses. No best-of-N.
6. **Effect sizes with uncertainty.** Pass-rate and score differences with 95% bootstrap intervals over paired
   trials, and win rates. Never a single best run.
7. **Negative controls** (tasks where Baltor should not help) are run and reported with the same protocol to
   detect placebo effects and measure search overhead.
8. **Cost next to quality**: tokens, wall time, tool calls and catalogue calls for every run.
9. **No leakage.** Showcase task packages and this ledger are excluded from the treatment arm's catalogue;
   hidden ground truth stays outside the workspace; reading an excluded item marks a run contaminated.
10. **Amendments are visible.** Changing a spec creates a new revision with a new hash and date; runs recorded
    under an older hash are reported under that revision, never mixed. Withdrawn tasks stay listed.
11. **Disclose the conflict of interest**: the same team wrote the tasks, evaluators and components.
12. **Data licences.** No third-party dataset is copied into the repository. Kaggle tasks need the user's own
    account and rule acceptance; offline tasks use scikit-learn's bundled datasets or seeded synthetic data.

Verify a placed or downloaded task package against this ledger:
`python3 verify_ledger.py path/to/showcase-task-*/` (recomputes each spec hash and checks every
setup and evaluator file hash).

## Ledger

Hash method: sha256 of the canonical JSON of task.json without the keys spec_hash and preregistration (keys sorted, separators ',' ':', UTF-8, ensure_ascii false); see showcase_eval.compute_spec_hash.

| Task id | Domain | Spec hash | Pre-registered | Revision | Trials/arm |
|---|---|---|---|---:|---:|
| `showcase_task_control_arithmetic_word_problems` | negative-control (control) | `cfd17698c33e4f2098c66a9ae701397ee0683dba93d3d7708e3542f43b2ecd99` | 2026-10-10 | 2 | 5 |
| `showcase_task_control_csv_two_key_sort` | negative-control (control) | `a75a936b115c54769d181dabc452d668d9863b6fab65fd7f27f7f4ee908af1b6` | 2026-10-10 | 2 | 5 |
| `showcase_task_control_fizzbuzz_variant` | negative-control (control) | `5ca77da9f6d09146c7a0f88c8783e143ca403d3dd3372cb73dcbd82203847eef` | 2026-10-10 | 2 | 5 |
| `showcase_task_control_leap_year_function` | negative-control (control) | `8380a8a928dba0fbd9f5ce0a71e14bc756c2601d3310676a1c8e034b39630d64` | 2026-10-10 | 2 | 5 |
| `showcase_task_control_readme_typo_fix` | negative-control (control) | `b5fb0e340b84d677a6312bead6e2dfc0b70fed7cd842a63576137b277f2a0cd6` | 2026-10-10 | 2 | 5 |
| `showcase_task_control_rename_function_refactor` | negative-control (control) | `26384af9ebfc49578482c748e295a8014bb71157978b855fe28563efec0c6248` | 2026-10-10 | 2 | 5 |
| `showcase_task_control_unit_conversion_table` | negative-control (control) | `c8de5b5f2a8846a994826f627bba09c296bc3f81a1c1f84114aea5929a3f0b5f` | 2026-10-10 | 2 | 5 |
| `showcase_task_control_word_frequency_count` | negative-control (control) | `2831859025b90b1b4b798e0e507288ba40143450b4b7e72484039bb7faa32a22` | 2026-10-10 | 2 | 5 |
| `showcase_task_control_yaml_to_json` | negative-control (control) | `baa62ce6003d6cb72ee3df2f24ffb0405f2b68b0de579bccfd530647be9bcada` | 2026-10-10 | 2 | 5 |
