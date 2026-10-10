# Adversarial review bank: D006 contact and props (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D006 contact and props". The questions below are the
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

- Severity: 32 high.
- Modes: 32 visual.
- Need listening: 0; listening-only (no visual or machine route): none.
- Need a human audience: 0.
- Only answerable at final encode or delivery: none.
- Limited by style filter: none.

## Named passes that draw on this area

- `default_32`: `AVQ-006-002`
- `visual_depth_contact`: `AVQ-006-001`, `AVQ-006-002`, `AVQ-006-003`, `AVQ-006-004`, `AVQ-006-005`, `AVQ-006-006`, `AVQ-006-007`, `AVQ-006-008`
- `performance_motion`: `AVQ-006-001`, `AVQ-006-002`, `AVQ-006-003`, `AVQ-006-004`, `AVQ-006-005`, `AVQ-006-006`, `AVQ-006-007`, `AVQ-006-008`
- `longer_cardboard_32`: `AVQ-006-002`, `AVQ-006-003`, `AVQ-006-004`, `AVQ-006-005`, `AVQ-006-021`

## Questions

1. **AVQ-006-001** Do planted feet remain fixed against the ground during a hold?
   - Failure hypothesis: Root movement causes visible foot sliding.
   - Check or fix: Track sole contact points across the hold.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
2. **AVQ-006-002** Does the hand meet the prop before the prop moves?
   - Failure hypothesis: The object responds before physical contact.
   - Check or fix: Inspect approach and first-motion frames.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32, visual_depth_contact, performance_motion, longer_cardboard_32.
3. **AVQ-006-003** Does the grip maintain a consistent attachment point?
   - Failure hypothesis: Held prop drifts through the palm.
   - Check or fix: Track local hand-prop offsets through motion.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, longer_cardboard_32.
4. **AVQ-006-004** Is the prop released before its independent trajectory begins?
   - Failure hypothesis: Constraint persists into the throw.
   - Check or fix: Inspect release frame and neighboring transforms.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, longer_cardboard_32.
5. **AVQ-006-005** Does a receiving hand close around the arriving object?
   - Failure hypothesis: Handoff looks like a teleport between owners.
   - Check or fix: Animate contact, grip and release in order.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion, longer_cardboard_32.
6. **AVQ-006-006** Are fingertips penetrating rigid surfaces visibly?
   - Failure hypothesis: Contact solver places anatomy inside the prop.
   - Check or fix: Inspect close contact frames and adjust offsets.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
7. **AVQ-006-007** Does a carried object rotate plausibly with the wrist?
   - Failure hypothesis: Prop orientation is detached from the grip.
   - Check or fix: Compare wrist and object rotations across the carry.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
8. **AVQ-006-008** Is the object's center of mass supported by the grasp?
   - Failure hypothesis: Heavy prop hangs from an implausible pinch.
   - Check or fix: Change grip, support or stylized weight cues.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
9. **AVQ-006-009** Does the character react to the load being picked up?
   - Failure hypothesis: Object weight has no effect on posture.
   - Check or fix: Add anticipatory brace and weight transfer.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
10. **AVQ-006-010** Are both feet actually supported on a narrow platform?
   - Failure hypothesis: Pose places a sole beyond the supporting edge.
   - Check or fix: Check contact regions from the final camera and geometry.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
11. **AVQ-006-011** Does a prop preserve its dimensions while changing owners?
   - Failure hypothesis: Scaling hides an awkward handoff.
   - Check or fix: Compare object bounds before and after transfer.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-006-012** Is a resting object tangent to rather than floating above its surface?
   - Failure hypothesis: Grounding gap makes the prop hover.
   - Check or fix: Inspect contact shadow and geometric gap.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-006-013** Does a rolling object rotate at a plausible travel rate?
   - Failure hypothesis: Translation and rotation contradict contact.
   - Check or fix: Compare circumference travel with angular rotation.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-006-014** Do dragged objects leave their contact point on the surface?
   - Failure hypothesis: Drag path passes through or above the floor.
   - Check or fix: Project the path onto the intended support plane.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-006-015** Does a hinged prop rotate around its visible hinge?
   - Failure hypothesis: Door or sign pivots around an arbitrary center.
   - Check or fix: Mark hinge position and inspect rotation arcs.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-006-016** Does a mouth-held object align with the actual mouth?
   - Failure hypothesis: Prop floats beside the face.
   - Check or fix: Track mouth anchor and occlusion ordering.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-006-017** Are duplicated props tracked as distinct persistent objects?
   - Failure hypothesis: A single item becomes several during crowd action.
   - Check or fix: Audit ownership and object-ID transitions.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-006-018** Does the original important prop remain identifiable among copies?
   - Failure hypothesis: Payoff loses the object it was built around.
   - Check or fix: Preserve a distinctive feature and ownership trace.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-006-019** Is a pocketed object visibly stowed rather than simply removed?
   - Failure hypothesis: Disappearance breaks continuity.
   - Check or fix: Stage the insertion or show an unambiguous occlusion.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-006-020** Does a prop's shadow move with its actual position?
   - Failure hypothesis: Shadow remains behind after pickup.
   - Check or fix: Bind shadow behavior to the same object state.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-006-021** Are handles and grip surfaces facing the usable direction?
   - Failure hypothesis: Characters hold inaccessible parts of tools.
   - Check or fix: Check affordances against the intended use.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: longer_cardboard_32.
22. **AVQ-006-022** Does a flexible prop bend where force is applied?
   - Failure hypothesis: Deformation originates away from the contact.
   - Check or fix: Align bend region with grip and resistance.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-006-023** Are surface contacts maintained during camera movement?
   - Failure hypothesis: Screen-space fixes fail when the view changes.
   - Check or fix: Recheck contacts from all used cameras.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-006-024** Does a stack of props have believable support relationships?
   - Failure hypothesis: Upper items balance on empty space.
   - Check or fix: Audit support polygons and overlap.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-006-025** Does collision response occur at the visible impact moment?
   - Failure hypothesis: Reaction begins before or after contact.
   - Check or fix: Compare impact frame to motion and sound onset.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-006-026** Can viewers see that the character still owns the key item?
   - Failure hypothesis: Important possession is hidden for too long.
   - Check or fix: Show a clear possession cue before the payoff.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-006-027** Does the prop intersect costume or anatomy during turns?
   - Failure hypothesis: Attachment works only in the front view.
   - Check or fix: Inspect full turn silhouettes and internal overlaps.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-006-028** Are props placed consistently relative to persistent landmarks?
   - Failure hypothesis: Set dressing drifts between shots.
   - Check or fix: Compare landmark-relative coordinates and encoded frames.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-006-029** Does the pickup path avoid passing through another object?
   - Failure hypothesis: Hand or prop clips through nearby scenery.
   - Check or fix: Check the swept motion envelope.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-006-030** Are contact shadows appropriate after an object becomes airborne?
   - Failure hypothesis: Grounded shadow remains glued beneath flight.
   - Check or fix: Adjust shadow offset and softness with height.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-006-031** Does a tool's output begin at its visible working end?
   - Failure hypothesis: Effect originates from an unrelated point.
   - Check or fix: Anchor output to the active tip or nozzle.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-006-032** Would a close contact insert clarify the action better than more labels?
   - Failure hypothesis: Tiny interaction carries too much narrative burden.
   - Check or fix: Test a brief readable contact shot.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
