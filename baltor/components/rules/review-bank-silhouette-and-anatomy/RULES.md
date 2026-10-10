# Adversarial review bank: D007 silhouette and anatomy (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D007 silhouette and anatomy". The questions below are the
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
- Need listening: 0 (none are listening-only).
- Need a human audience: 0.
- Only answerable at final encode or delivery: none.
- Limited by style filter: none.

## Named passes that draw on this area

- `default_32`: `AVQ-007-001`
- `visual_depth_contact`: `AVQ-007-001`, `AVQ-007-002`, `AVQ-007-003`, `AVQ-007-004`, `AVQ-007-005`, `AVQ-007-006`, `AVQ-007-007`, `AVQ-007-008`
- `performance_motion`: `AVQ-007-001`, `AVQ-007-002`, `AVQ-007-003`, `AVQ-007-004`, `AVQ-007-005`, `AVQ-007-006`, `AVQ-007-007`, `AVQ-007-008`
- `longer_cardboard_32`: `AVQ-007-001`

## Questions

1. **AVQ-007-001** Can the key pose be recognized as a filled black silhouette?
   - Failure hypothesis: Overlapping limbs conceal the action.
   - Check or fix: Review silhouette-only key poses.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32, visual_depth_contact, performance_motion, longer_cardboard_32.
2. **AVQ-007-002** Are left and right limbs distinguishable during crossings?
   - Failure hypothesis: Limbs swap identity visually.
   - Check or fix: Use depth, spacing or differentiated contour.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
3. **AVQ-007-003** Does the joint bend in the intended anatomical direction?
   - Failure hypothesis: Rig orientation produces inverted elbows or knees.
   - Check or fix: Inspect bend extrema in the final view.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
4. **AVQ-007-004** Does the head remain attached during squash or rotation?
   - Failure hypothesis: Deformation opens an unintended neck gap.
   - Check or fix: Check head-neck overlap through extreme poses.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
5. **AVQ-007-005** Are limb lengths consistent unless deliberate deformation is clear?
   - Failure hypothesis: Uncontrolled stretching changes body proportions.
   - Check or fix: Compare segment lengths across key poses.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
6. **AVQ-007-006** Do feet have enough shape to communicate their orientation?
   - Failure hypothesis: Featureless feet make planted direction ambiguous.
   - Check or fix: Add a readable toe or sole cue.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
7. **AVQ-007-007** Are hands readable at the delivered size?
   - Failure hypothesis: Finger detail collapses into noise.
   - Check or fix: Simplify hand shapes and enlarge important gestures.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
8. **AVQ-007-008** Does a character's tail emerge from a coherent attachment point?
   - Failure hypothesis: Tail floats or changes anatomical origin.
   - Check or fix: Track tail root through turns.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, performance_motion.
9. **AVQ-007-009** Are ears visibly attached throughout expressive motion?
   - Failure hypothesis: Ear pivots detach from the skull.
   - Check or fix: Inspect bases at widest rotations.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
10. **AVQ-007-010** Does the mouth remain on the face during perspective changes?
   - Failure hypothesis: Facial features slide independently of head volume.
   - Check or fix: Use consistent face-space projection.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
11. **AVQ-007-011** Are eyes aligned to the same implied head orientation?
   - Failure hypothesis: Eye placement contradicts skull rotation.
   - Check or fix: Compare eye line and face contour.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-007-012** Does the silhouette distinguish the character from nearby props?
   - Failure hypothesis: Similar shapes obscure identity.
   - Check or fix: Change contour rhythm or local spacing.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-007-013** Are thin limbs lost after encoding?
   - Failure hypothesis: Line width falls below stable display resolution.
   - Check or fix: Inspect encoded limbs at intended screen size.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-007-014** Does a bent torso retain believable structural continuity?
   - Failure hypothesis: Body folds at an arbitrary point.
   - Check or fix: Place curvature around the intended spine or hinge.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-007-015** Are contact poses clear without internal line detail?
   - Failure hypothesis: Interior strokes rescue an unreadable outline.
   - Check or fix: Open the silhouette around the contact.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-007-016** Does the character preserve recognizable proportions in perspective?
   - Failure hypothesis: Foreshortening is applied inconsistently.
   - Check or fix: Compare near and far body segments coherently.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-007-017** Do shoulder attachments permit the demonstrated arm range?
   - Failure hypothesis: Arms rotate through the torso.
   - Check or fix: Review shoulder clearance during reach arcs.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-007-018** Are knees visually separated from the ground during crouches?
   - Failure hypothesis: Bent legs merge into an indistinct base.
   - Check or fix: Adjust pose spacing and camera elevation.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-007-019** Does clothing preserve rather than obscure essential joint action?
   - Failure hypothesis: Costume hides the mechanism of the gesture.
   - Check or fix: Simplify folds around active joints.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-007-020** Are extra apparent limbs created by motion trails?
   - Failure hypothesis: Effects make one actor look anatomically duplicated.
   - Check or fix: Reduce trail opacity or separate trail styling.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-007-021** Does a side-view animal show a coherent leg pairing?
   - Failure hypothesis: Gait reads as an impossible limb count.
   - Check or fix: Track near and far leg silhouettes.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-007-022** Are facial proportions stable across expressions?
   - Failure hypothesis: Expression deformation accidentally changes identity.
   - Check or fix: Compare neutral and extreme landmark relationships.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-007-023** Does the pose communicate balance from its silhouette alone?
   - Failure hypothesis: Center of mass lies outside support without explanation.
   - Check or fix: Align body mass with the support base.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-007-024** Are extreme poses intentional rather than single-frame rig failures?
   - Failure hypothesis: Transient deformation looks broken.
   - Check or fix: Review frames around acceleration peaks.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-007-025** Does the character retain volume during squash and stretch?
   - Failure hypothesis: Deformation arbitrarily gains or loses mass.
   - Check or fix: Compare approximate body area or volume.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-007-026** Are line intersections creating unintended facial expressions?
   - Failure hypothesis: Contours form accidental brows or mouths.
   - Check or fix: Inspect small facial regions at delivery size.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-007-027** Does an occluded limb reappear on the correct side?
   - Failure hypothesis: Depth changes imply anatomical swapping.
   - Check or fix: Track limb identity through overlap intervals.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-007-028** Are articulated cutout seams hidden in normal poses?
   - Failure hypothesis: Joint gaps reveal construction unintentionally.
   - Check or fix: Increase overlap or redesign pivot placement.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-007-029** Can a viewer distinguish a limp from a rigging error?
   - Failure hypothesis: Asymmetry has no narrative or physical context.
   - Check or fix: Establish intentional gait characteristics consistently.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-007-030** Are resting hands posed rather than left in a default spread?
   - Failure hypothesis: Default rig shape undermines natural acting.
   - Check or fix: Pose inactive hands for the character's state.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-007-031** Does the hero's outline remain distinct in the crowd version?
   - Failure hypothesis: Small-scale duplicates lose signature features.
   - Check or fix: Create a simplified distance silhouette.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-007-032** Would reducing internal detail strengthen the acting silhouette?
   - Failure hypothesis: Decorative strokes interfere with pose reading.
   - Check or fix: Compare a simplified contour-first variant.
   - Severity: high. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
