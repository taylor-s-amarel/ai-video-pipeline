# Animation and Video Production Master Guide (10 Oct 2026): Adversarial review without checklist theater

Verbatim from `docs/reference/Animation_and_Video_Production_Master_Guide_2026-10-10.md` lines 1328-1362.

## Adversarial review without checklist theater

The final bank contains 1,024 authored questions in 32 domains, with nine defined passes. It is a searchable diagnostic resource, not 1,024 people, audience responses, completed tests, or production capabilities. A default pass selects 32 questions. Domain-specific passes contain 50–64 questions; the longer-cardboard pass selects 32. Applicability depends on the feature and evidence, not on a tag alone.

The earlier focused film application contains 17 scoped records: eleven observed passes, four untested potential improvements, and two audio blockers. The validator suite reports 39 passing regression tests. Three contact-sheet lineages were reproduced from exact MP4s, with matching byte or pixel evidence. Those results protect the review contract; they do not establish that the whole films were watched continuously or listened to independently.

Use the bank twice: first on the brief, storyboard and source state; then on the exact final encode. Final-pixel and listening questions remain untested or blocked during planning. Add a targeted pass after a material camera, rig, sound, caption, factual or rights change. Recheck the changed beat and neighboring beats. Stop after the bounded pass and necessary repairs; do not execute every question to manufacture impressive totals.

### Evidence states

- `untested`: insufficient observation to answer the question; the default.
- `observed-pass`: exact evidence supports a bounded statement for this target.
- `observed-fail`: matching direct evidence shows a defect.
- `blocked`: the check applies, but required access or evidence is missing.
- `not-applicable`: the relevant feature is absent, with a stated reason.

Use `demonstrated_defect` only with an observed failure. Use `potential_improvement` for a design hypothesis that still needs comparison. A viewer may dislike a story despite all measured technical gates passing; this is meaningful feedback and should guide the next story, not be dismissed by the checklist.

```json
{
  "question_id": "AVQ-006-002",
  "target_artifact": "final.mp4",
  "target_sha256": "COMPUTED_FINAL_HASH",
  "status": "untested",
  "finding_type": "none",
  "review_mode": "visual",
  "scope": {"start_frame": null, "end_frame": null, "coverage": "not_observed"},
  "evidence": [],
  "rationale": "Awaiting matching encoded interval",
  "required_recheck_after": ["rig_change", "prop_attachment_change", "camera_change"]
}
```

Real evidence should include its own hash, the target movie hash, the extraction or observation method, locator, coverage, and limitations. Do not retarget a contact sheet to a changed movie by editing its label. Do not mark a listening-only question passed using a waveform statistic. Nonfinite numbers, absent intervals, stale target hashes and unsupported claimed coverage should fail validation.
