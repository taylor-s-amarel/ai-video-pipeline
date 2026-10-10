# Adversarial review bank: D014 physics and weight (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D014 physics and weight". The questions below are the
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
- Limited by style filter: `AVQ-014-013` (3d, cutout, educational), `AVQ-014-014` (3d, cutout, educational).

## Named passes that draw on this area

- `default_32`: `AVQ-014-010`
- `performance_motion`: `AVQ-014-001`, `AVQ-014-002`, `AVQ-014-003`, `AVQ-014-004`, `AVQ-014-005`, `AVQ-014-006`, `AVQ-014-007`, `AVQ-014-008`
- `longer_cardboard_32`: `AVQ-014-001`, `AVQ-014-019`, `AVQ-014-030`

## Questions

1. **AVQ-014-001** Does the center of mass stay supported during a static pose?
   - Failure hypothesis: Body appears to balance on empty space.
   - Check or fix: Compare mass projection with the support region.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion, longer_cardboard_32.
2. **AVQ-014-002** Is momentum preserved through release and free flight?
   - Failure hypothesis: Object changes speed without an apparent force.
   - Check or fix: Inspect velocity before and after release.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
3. **AVQ-014-003** Does gravity act consistently within the fictional world?
   - Failure hypothesis: Similar objects fall under different unexplained rules.
   - Check or fix: Compare fall trajectories under matched conditions.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
4. **AVQ-014-004** Are collisions resolved at the visible surfaces?
   - Failure hypothesis: Objects react before touching or after interpenetrating.
   - Check or fix: Check contact geometry and reaction frame.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
5. **AVQ-014-005** Does an impact produce an appropriate response in both participants?
   - Failure hypothesis: Only one object acknowledges the collision.
   - Check or fix: Add coherent recoil or justified immovability.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
6. **AVQ-014-006** Are heavy objects harder to start and stop than light ones?
   - Failure hypothesis: Weight cues contradict material identity.
   - Check or fix: Compare acceleration and recovery timing.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
7. **AVQ-014-007** Does a pushed object remain in contact with the pushing hand?
   - Failure hypothesis: Force appears transmitted across a gap.
   - Check or fix: Track hand-surface distance throughout the push.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
8. **AVQ-014-008** Are friction changes motivated by surface changes?
   - Failure hypothesis: Objects suddenly stick or slide without cause.
   - Check or fix: Audit surface states along the trajectory.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: performance_motion.
9. **AVQ-014-009** Does a bouncing object lose or gain energy intentionally?
   - Failure hypothesis: Bounce heights imply unexplained energy creation.
   - Check or fix: Compare successive apex heights and timing.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
10. **AVQ-014-010** Are pendulum or hanging motions constrained to their support?
   - Failure hypothesis: Suspended objects travel outside their allowed arc.
   - Check or fix: Check pivot distance over time.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32.
11. **AVQ-014-011** Does a flexible object respond where force is applied?
   - Failure hypothesis: Deformation ignores load direction.
   - Check or fix: Align bend and stretch with force cues.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-014-012** Are stacked objects stable under the depicted load?
   - Failure hypothesis: Top-heavy arrangements defy the intended realism.
   - Check or fix: Inspect support and center-of-mass relationships.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-014-013** Does water contact match the hull or floating body?
   - Failure hypothesis: Object hovers over or sinks through the surface.
   - Check or fix: Compare waterline and object geometry.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: 3d, cutout, educational.
14. **AVQ-014-014** Is a floating object's buoyancy consistent as weight changes?
   - Failure hypothesis: Added load has no plausible displacement effect.
   - Check or fix: Show or justify the response to loading.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: 3d, cutout, educational.
15. **AVQ-014-015** Are falling objects occluded correctly by intervening geometry?
   - Failure hypothesis: Trajectory visually passes through solid structures.
   - Check or fix: Check swept volumes and depth order together.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-014-016** Does a turning character lean coherently with speed?
   - Failure hypothesis: Body lean contradicts the turn.
   - Check or fix: Compare direction, acceleration and pose.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-014-017** Are feet slipping only when the scene intends a slip?
   - Failure hypothesis: Uncontrolled skating undermines weight.
   - Check or fix: Track support-phase contacts separately from swing.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-014-018** Does a rope or cable transmit tension visibly?
   - Failure hypothesis: Slack cable pulls an object impossibly.
   - Check or fix: Align tension state with the applied action.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-014-019** Are force effects proportional enough to communicate cause?
   - Failure hypothesis: Tiny taps launch huge objects without established stylization.
   - Check or fix: Establish exaggeration rules or rebalance response.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: longer_cardboard_32.
20. **AVQ-014-020** Does a projectile clear the obstacle it visibly crosses?
   - Failure hypothesis: Trajectory intersects geometry between sampled frames.
   - Check or fix: Test the swept path at finer intervals.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-014-021** Are particles inheriting appropriate motion at emission?
   - Failure hypothesis: Debris launches without the source's velocity.
   - Check or fix: Include source motion in initial conditions.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-014-022** Does a rotating object maintain a coherent pivot or axle?
   - Failure hypothesis: Rotation axis wanders without a joint.
   - Check or fix: Track pivot position and orientation.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-014-023** Are gears or wheels synchronized with their visible engagement?
   - Failure hypothesis: Meshing objects rotate incompatibly.
   - Check or fix: Compare tooth counts, direction and angular rates.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-014-024** Does a moving platform carry its passenger consistently?
   - Failure hypothesis: Passenger drifts relative to the support.
   - Check or fix: Track local coordinates during the ride.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-014-025** Are spring-like motions damped in a plausible direction?
   - Failure hypothesis: Oscillation grows unexpectedly or never resolves.
   - Check or fix: Inspect amplitude envelope and intended energy input.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-014-026** Does a character's jump include a readable takeoff and landing?
   - Failure hypothesis: Flight starts or ends without force transfer.
   - Check or fix: Stage compression, extension and recovery.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-014-027** Are collision margins appropriate to visible shape rather than proxy size?
   - Failure hypothesis: Invisible collision boxes stop objects too early.
   - Check or fix: Compare proxy and rendered contact boundaries.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-014-028** Does an offscreen force have enough setup to be understood?
   - Failure hypothesis: Unexplained motion looks like a simulation error.
   - Check or fix: Show or establish the force source.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-014-029** Are physical simplifications disclosed in an educational mechanism?
   - Failure hypothesis: Toy behavior is presented as a universal law.
   - Check or fix: State the model's assumptions and limits.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-014-030** Does the animation distinguish kinematic proof from simulation evidence?
   - Failure hypothesis: Authored paths are mislabeled as physical validation.
   - Check or fix: Record which relationships are tested versus simulated.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any. Passes: longer_cardboard_32.
31. **AVQ-014-031** Are numerical tolerances small enough for the final camera view?
   - Failure hypothesis: World-space error becomes visible after zoom.
   - Check or fix: Convert tolerances to projected pixel error.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-014-032** Would one extra weight cue make the interaction convincing?
   - Failure hypothesis: Correct trajectories still lack perceived effort.
   - Check or fix: Add a clear brace, compression or follow-through.
   - Severity: medium. Modes: visual, machine. Stages: storyboard, production, final-encode. Style filters: any.
