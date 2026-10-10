# Adversarial review bank: D032 reproducibility and maintenance (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D032 reproducibility and maintenance". The questions below are the
owner's exact text. `questions.json` holds the same 32 records in the `adversarial_question` contract.

## How to use this bank (the guide's rules)

- Use this bank as a menu, not a requirement to review every question on every film. Each entry keeps its stable ID, question, failure hypothesis, practical check/fix, severity and modality/stage filters. The evidence contract in the main guide applies to every entry. Tags are candidate filters; they cannot make an irrelevant question applicable or turn missing evidence into a pass. Detailed machine-readable records remain in the preserved source bank.
- Use the bank twice: first on the brief, storyboard and source state; then on the exact final encode. Final-pixel
  and listening questions remain untested or blocked during planning.
- After a material camera, rig, sound, caption, factual or rights change, add a targeted pass: recheck the changed
  beat and neighbouring beats. Stop after the bounded pass and necessary repairs; do not execute every question to
  manufacture impressive totals.
- Every answer is a record in the `adversarial_review_result` contract: `untested` (the default), `observed-pass`,
  `observed-fail`, `blocked` or `not-applicable` (with a stated reason). `demonstrated_defect` only with an observed
  failure; `potential_improvement` for a design hypothesis that still needs comparison.
- Do not mark a listening-only question passed using a waveform statistic. Do not retarget evidence to a changed
  movie by editing its label.

## This area at a glance

- Severity: 1 critical, 22 high, 9 medium.
- Modes: 7 visual, 2 auditory, 32 machine, 2 human-audience.
- Need listening: 2 (none are listening-only).
- Need a human audience: 2.
- Only answerable at final encode or delivery: none.
- Limited by style filter: `AVQ-032-012` (puzzle, typographic).

## Named passes that draw on this area

- `default_32`: `AVQ-032-001`
- `final_delivery`: `AVQ-032-001`, `AVQ-032-002`, `AVQ-032-003`, `AVQ-032-004`, `AVQ-032-005`, `AVQ-032-006`, `AVQ-032-007`, `AVQ-032-008`

## Questions

1. **AVQ-032-001** Can another authorized machine open the native project without relying on the creator's private absolute paths?
   - Failure hypothesis: Hidden local paths make the handoff nonportable.
   - Check or fix: Reopen from a clean location and repair unresolved relative dependencies.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any. Passes: default_32, final_delivery.
2. **AVQ-032-002** Are all required source assets present at the exact versions used for the approved render?
   - Failure hypothesis: Similar filenames conceal missing or changed source bytes.
   - Check or fix: Verify a complete asset manifest against cryptographic hashes.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any. Passes: final_delivery.
3. **AVQ-032-003** Is the actual renderer, application, plugin, and model version recorded rather than only a generic tool name?
   - Failure hypothesis: Environment drift prevents reproducing the approved appearance.
   - Check or fix: Capture the versions used by the successful build.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any. Passes: final_delivery.
4. **AVQ-032-004** Does the project declare which dependencies are installed separately because they cannot be bundled?
   - Failure hypothesis: A supposedly self-contained package omits essential external components.
   - Check or fix: Separate included assets from required external dependencies and acquisition steps.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any. Passes: final_delivery.
5. **AVQ-032-005** Can the render be reproduced using the documented command without undocumented manual editor state?
   - Failure hypothesis: Hidden UI settings or selection state determine the output.
   - Check or fix: Rebuild from a fresh session following only the handoff.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any. Passes: final_delivery.
6. **AVQ-032-006** Are random seeds and generation inputs retained wherever stochastic output affects the film?
   - Failure hypothesis: Re-running changes placement, motion, or generated assets unpredictably.
   - Check or fix: Save seeds, exact inputs, and generated source bytes.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any. Passes: final_delivery.
7. **AVQ-032-007** Does the workflow distinguish reproducible procedural assets from generation steps that cannot be rerun identically?
   - Failure hypothesis: A prompt is treated as sufficient to recreate nondeterministic output.
   - Check or fix: Preserve exact generated files and state the repeatability boundary.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any. Passes: final_delivery.
8. **AVQ-032-008** Are scene units, coordinate conventions, and frame-rate assumptions explicit in the handoff?
   - Failure hypothesis: Reopening or importing changes scale, orientation, or time interpretation.
   - Check or fix: Record conventions and verify a known reference object and event.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any. Passes: final_delivery.
9. **AVQ-032-009** Is there one authoritative timeline and scene transform for camera, targets, masks, and audio?
   - Failure hypothesis: Parallel timing or transform systems drift when the scene changes.
   - Check or fix: Map shared authorities and test a controlled timing/camera edit.
   - Severity: high. Modes: machine, visual, auditory. Stages: production. Style filters: any.
10. **AVQ-032-010** Can a maintainer change one character or prop without breaking unrelated layers or hidden references?
   - Failure hypothesis: Tight coupling turns a local edit into widespread damage.
   - Check or fix: Perform a bounded substitution in a copy and inspect dependent outputs.
   - Severity: medium. Modes: machine, visual. Stages: production. Style filters: any.
11. **AVQ-032-011** Do layer names and ownership describe real independently controllable roles rather than arbitrary duplicates?
   - Failure hypothesis: Inflated layer counts conceal an unmaintainable monolithic composition.
   - Check or fix: Audit each layer's purpose and demonstrate meaningful isolation.
   - Severity: medium. Modes: machine, visual. Stages: production. Style filters: any.
12. **AVQ-032-012** Are the clean puzzle, reveal annotations, captions, and audio separable for future revisions?
   - Failure hypothesis: Flattened deliverables force destructive edits for routine updates.
   - Check or fix: Verify editable source separation for the promised revision types.
   - Severity: high. Modes: machine, visual. Stages: production, delivery. Style filters: puzzle, typographic.
13. **AVQ-032-013** Does changing a source asset invalidate all caches that depend on it?
   - Failure hypothesis: A render appears updated while stale cached geometry or frames persist.
   - Check or fix: Alter a controlled fixture and trace cache invalidation through the pipeline.
   - Severity: high. Modes: machine. Stages: production. Style filters: any.
14. **AVQ-032-014** Are generated intermediates distinguishable from authoritative source files?
   - Failure hypothesis: A maintainer edits disposable output and loses changes on regeneration.
   - Check or fix: Label source-of-truth files and document regeneration boundaries.
   - Severity: medium. Modes: machine. Stages: production, delivery. Style filters: any.
15. **AVQ-032-015** Can a failed long render resume without silently skipping or mixing frames from another revision?
   - Failure hypothesis: Resume logic treats stale partial output as valid progress.
   - Check or fix: Test interruption and restart with per-frame provenance checks.
   - Severity: high. Modes: machine. Stages: production. Style filters: any.
16. **AVQ-032-016** Does the build fail clearly when an asset, font, or plugin is missing instead of silently substituting it?
   - Failure hypothesis: Fallback behavior produces plausible but incorrect output.
   - Check or fix: Remove a controlled dependency in a test copy and inspect the failure mode.
   - Severity: high. Modes: machine. Stages: production. Style filters: any.
17. **AVQ-032-017** Are configuration defaults safe when a new episode omits a required field?
   - Failure hypothesis: An inherited default silently supplies the wrong story, count, or export setting.
   - Check or fix: Validate required fields and test intentionally incomplete inputs.
   - Severity: high. Modes: machine. Stages: production. Style filters: any.
18. **AVQ-032-018** Are output filenames and directories derived from stable project/version identifiers rather than mutable titles alone?
   - Failure hypothesis: Renaming or duplicate titles overwrite unrelated work.
   - Check or fix: Test collision cases and include stable IDs in the build manifest.
   - Severity: medium. Modes: machine. Stages: production. Style filters: any.
19. **AVQ-032-019** Can automated checks detect a deliberately wrong target count, missing frame, or stale caption file?
   - Failure hypothesis: Green test reports prove only that the test runner executed.
   - Check or fix: Seed representative known-wrong fixtures and verify expected failures.
   - Severity: high. Modes: machine. Stages: production. Style filters: any.
20. **AVQ-032-020** Can a maintainer recover why the current creative choice was selected over the rejected alternatives?
   - Failure hypothesis: Missing decision history causes discarded approaches to be repeated as new improvements.
   - Check or fix: Retain representative alternatives with dated, evidence-linked selection reasons.
   - Severity: medium. Modes: machine, human-audience. Stages: production, delivery. Style filters: any.
21. **AVQ-032-021** Are visual regression comparisons tolerant of harmless variation but sensitive to meaningful defects?
   - Failure hypothesis: Pixel diffs either flood reviewers with noise or miss semantic failures.
   - Check or fix: Calibrate against accepted variations and known consequential defects.
   - Severity: medium. Modes: machine, visual. Stages: production. Style filters: any.
22. **AVQ-032-022** Is there a small representative fixture for each risky renderer, codec, or plugin upgrade?
   - Failure hypothesis: Upgrades are tested only by rerendering the entire film after failure.
   - Check or fix: Preserve minimal scenes covering contact, text, transparency, sound, and timing risks.
   - Severity: medium. Modes: machine, visual, auditory. Stages: production. Style filters: any.
23. **AVQ-032-023** Can the previous approved version be restored after an unsuccessful edit or dependency upgrade?
   - Failure hypothesis: The workflow overwrites the only working source and output.
   - Check or fix: Verify versioned backups and perform a bounded restore test.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any.
24. **AVQ-032-024** Are external URLs or cloud services required at render time documented with an offline fallback where feasible?
   - Failure hypothesis: Network changes make a previously working local project fail.
   - Check or fix: Test dependency availability and preserve authorized local inputs.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any.
25. **AVQ-032-025** Does the package avoid including credentials, session tokens, or machine-specific secrets?
   - Failure hypothesis: Reproducibility packaging leaks authentication material.
   - Check or fix: Inspect configuration and archives for secrets without exposing their values.
   - Severity: critical. Modes: machine. Stages: production, delivery. Style filters: any.
26. **AVQ-032-026** Are expected runtime, memory, storage, and temporary-file requirements recorded from an actual run?
   - Failure hypothesis: Another machine cannot reproduce the output within available resources.
   - Check or fix: Capture resource use and distinguish measurements from estimates.
   - Severity: medium. Modes: machine. Stages: production, delivery. Style filters: any.
27. **AVQ-032-027** Does automated cleanup preserve authoritative sources and only remove declared disposable outputs?
   - Failure hypothesis: Broad deletion patterns destroy irreplaceable project material.
   - Check or fix: Review cleanup scope and test it against a protected fixture tree.
   - Severity: high. Modes: machine. Stages: production. Style filters: any.
28. **AVQ-032-028** Can a maintainer trace a delivered frame or sound back to its source revision and responsible edit?
   - Failure hypothesis: Final output provenance is lost across transformations.
   - Check or fix: Retain build manifests linking outputs, source commits, and asset versions.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any.
29. **AVQ-032-029** Are known defects and untested routes documented so a future maintainer does not repeat disproven assumptions?
   - Failure hypothesis: A clean handoff conceals unresolved problems and failed approaches.
   - Check or fix: Record reproducible defects and distinguish untested alternatives from working routes.
   - Severity: medium. Modes: machine. Stages: production, delivery. Style filters: any.
30. **AVQ-032-030** Does a format round trip preserve the specific hierarchy, animation, or editability promised to the recipient?
   - Failure hypothesis: Export/import success is mistaken for preservation of native behavior.
   - Check or fix: Round-trip a representative source and compare promised features explicitly.
   - Severity: high. Modes: machine, visual. Stages: production, delivery. Style filters: any.
31. **AVQ-032-031** Are factual, rights, and dependency records linked to the assets they must be rechecked against when those assets change?
   - Failure hypothesis: Maintenance updates bypass the reviews invalidated by the change.
   - Check or fix: Define review triggers from the dependency graph and test one controlled replacement.
   - Severity: high. Modes: machine. Stages: production, delivery. Style filters: any.
32. **AVQ-032-032** Can a new maintainer complete one realistic revision using only the package and its instructions?
   - Failure hypothesis: Documentation looks complete but omits practical steps needed to work.
   - Check or fix: Run a bounded handoff exercise and repair observed gaps.
   - Severity: high. Modes: machine, human-audience. Stages: production, delivery. Style filters: any.
