# Adversarial review bank: D013 motion and easing (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D013 motion and easing". The questions below are the
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

- Severity: 32 medium.
- Modes: 32 visual, 32 machine.
- Need listening: 0 (none are listening-only).
- Need a human audience: 0.
- Only answerable at final encode or delivery: none.
- Limited by style filter: none.

## Named passes that draw on this area

- `default_32`: `AVQ-013-010`
- `performance_motion`: `AVQ-013-001`, `AVQ-013-002`, `AVQ-013-003`, `AVQ-013-004`, `AVQ-013-005`, `AVQ-013-006`, `AVQ-013-007`, `AVQ-013-008`
- `longer_cardboard_32`: `AVQ-013-010`

## Questions

1. **AVQ-013-001** Does the action accelerate for a physical or expressive reason?
   - Failure hypothesis: Uniform motion feels mechanical.
   - Check or fix: Shape speed around intention and resistance.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
2. **AVQ-013-002** Are holds truly still where the pose should be planted?
   - Failure hypothesis: Residual interpolation creates unwanted drift.
   - Check or fix: Inspect held channels and encoded landmarks.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
3. **AVQ-013-003** Does easing delay the action until the beat has passed?
   - Failure hypothesis: Overlong ease-in weakens timing.
   - Check or fix: Compare onset with the narrative cue.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
4. **AVQ-013-004** Is the motion arc smooth through intermediate poses?
   - Failure hypothesis: Keyframe interpolation creates corners.
   - Check or fix: Plot and inspect the path between keys.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
5. **AVQ-013-005** Do different body parts lead and follow coherently?
   - Failure hypothesis: All parts start together like a rigid cutout.
   - Check or fix: Stagger initiation and follow-through.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
6. **AVQ-013-006** Does overshoot fit the material and emotional tone?
   - Failure hypothesis: Elastic easing makes rigid objects rubbery.
   - Check or fix: Tune overshoot by object and intent.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
7. **AVQ-013-007** Are direction reversals prepared rather than instantaneous?
   - Failure hypothesis: Velocity flips without anticipation.
   - Check or fix: Add braking, weight shift or stylized punctuation.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
8. **AVQ-013-008** Does a repeated cycle visibly snap at its seam?
   - Failure hypothesis: First and last poses or velocities disagree.
   - Check or fix: Compare seam position and derivatives.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
9. **AVQ-013-009** Are walk cycles matched to actual travel speed?
   - Failure hypothesis: Stride frequency causes skating.
   - Check or fix: Relate stride distance to root displacement.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
10. **AVQ-013-010** Does motion remain readable after temporal sampling?
   - Failure hypothesis: Fast gesture disappears between delivered frames.
   - Check or fix: Adjust duration or pose emphasis at output frame rate.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32, longer_cardboard_32.
11. **AVQ-013-011** Are interpolation handles creating hidden extreme poses?
   - Failure hypothesis: Spline overshoot produces unintended excursions.
   - Check or fix: Inspect curves and sampled extrema.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-013-012** Does a settle end with a clear stable pose?
   - Failure hypothesis: Endless damping prevents the beat from landing.
   - Check or fix: Choose a meaningful final hold.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-013-013** Is anticipation proportionate to the upcoming action?
   - Failure hypothesis: Large preparation promises an underwhelming result.
   - Check or fix: Balance preparation and payoff amplitude.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-013-014** Are motion trails consistent with trajectory and timing?
   - Failure hypothesis: Trails suggest an incorrect movement path.
   - Check or fix: Derive trails from actual sampled motion.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-013-015** Does secondary motion stop before it becomes distracting?
   - Failure hypothesis: Hair or scarf continues competing with the next beat.
   - Check or fix: Control decay around attention shifts.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-013-016** Are camera and object easing accidentally canceling each other?
   - Failure hypothesis: Combined motion makes the subject appear stalled.
   - Check or fix: Inspect relative screen-space velocity.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-013-017** Does a crowd cycle repeat in obvious synchronized bands?
   - Failure hypothesis: Shared phase exposes duplication.
   - Check or fix: Vary phase while preserving causal coordination.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-013-018** Is a slow action slow because it is meaningful?
   - Failure hypothesis: Unmotivated slowness wastes the viewer's attention.
   - Check or fix: Shorten or enrich the information-bearing interval.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-013-019** Do moving labels remain attached without jitter?
   - Failure hypothesis: Annotation smoothing lags or oscillates.
   - Check or fix: Use stable anchors and inspect final projection.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-013-020** Are speed changes legible without relying on motion blur?
   - Failure hypothesis: Blur hides the actual acceleration.
   - Check or fix: Review a no-blur motion pass.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-013-021** Does a character stop with a plausible transfer of weight?
   - Failure hypothesis: Root halts while limbs continue incorrectly.
   - Check or fix: Coordinate braking steps and torso settle.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-013-022** Are path corners rounded enough for the object's turning ability?
   - Failure hypothesis: Motion cuts through corners or rotates unnaturally.
   - Check or fix: Match turn radius to body and environment.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-013-023** Does the motion preserve screen direction across edits?
   - Failure hypothesis: Action reverses unintentionally at the cut.
   - Check or fix: Compare outgoing and incoming velocity vectors.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-013-024** Are tiny idle loops visible as repetitive nervousness?
   - Failure hypothesis: Subtle cycles become distracting over long holds.
   - Check or fix: Reduce frequency or use noncyclic pauses.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-013-025** Does a scale animation imply intentional deformation rather than camera error?
   - Failure hypothesis: Object growth looks like accidental zoom.
   - Check or fix: Pair deformation with appropriate contour and timing cues.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-013-026** Are separate layers driven by one time authority?
   - Failure hypothesis: Animation drifts because clocks differ.
   - Check or fix: Sample all layers from the same timeline.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-013-027** Does a delayed reaction still feel causally connected?
   - Failure hypothesis: Lag becomes too long to read as response.
   - Check or fix: Test the cue-to-reaction interval in context.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-013-028** Is the movement envelope compatible with safe areas?
   - Failure hypothesis: Easing overshoot pushes important content offscreen.
   - Check or fix: Check extrema rather than only key positions.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-013-029** Do repeated actions escalate meaningfully in timing or strategy?
   - Failure hypothesis: Cycles repeat without advancing the story.
   - Check or fix: Change the consequential variable per attempt.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-013-030** Are contact constraints preserved through interpolation?
   - Failure hypothesis: Valid keys hide invalid in-between contacts.
   - Check or fix: Sample the full interval at delivery rate or finer.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-013-031** Does stylized stepped motion use a consistent cadence?
   - Failure hypothesis: Uneven holds resemble dropped frames.
   - Check or fix: Document and inspect intended pose exposure timing.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-013-032** Would fewer moving elements make the main action clearer?
   - Failure hypothesis: Continuous animation overloads attention.
   - Check or fix: Mute secondary motion and compare comprehension.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
