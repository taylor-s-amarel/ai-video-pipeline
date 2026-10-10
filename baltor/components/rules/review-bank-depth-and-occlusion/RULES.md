# Adversarial review bank: D004 depth and occlusion (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D004 depth and occlusion". The questions below are the
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
- Modes: 32 visual.
- Need listening: 0 (none are listening-only).
- Need a human audience: 0.
- Only answerable at final encode or delivery: none.
- Limited by style filter: `AVQ-004-015` (puzzle, educational).

## Named passes that draw on this area

- `default_32`: `AVQ-004-001`
- `visual_depth_contact`: `AVQ-004-001`, `AVQ-004-002`, `AVQ-004-003`, `AVQ-004-004`, `AVQ-004-005`, `AVQ-004-006`, `AVQ-004-007`, `AVQ-004-008`
- `factual_puzzle`: `AVQ-004-001`, `AVQ-004-002`, `AVQ-004-003`, `AVQ-004-004`, `AVQ-004-005`, `AVQ-004-006`, `AVQ-004-007`, `AVQ-004-008`, `AVQ-004-009`, `AVQ-004-010`
- `longer_cardboard_32`: `AVQ-004-003`

## Questions

1. **AVQ-004-001** Does every overlap agree with the intended front-to-back order?
   - Failure hypothesis: Layer order contradicts scene geometry.
   - Check or fix: Inspect crossings against a depth-order map.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32, visual_depth_contact, factual_puzzle.
2. **AVQ-004-002** Does an occluded object return with the same identity?
   - Failure hypothesis: Reappearance silently substitutes the object.
   - Check or fix: Track stable object IDs through occlusion.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, factual_puzzle.
3. **AVQ-004-003** Are disoccluded areas actually painted or modeled?
   - Failure hypothesis: Camera movement exposes empty holes.
   - Check or fix: Inspect maximum parallax and edge reveals.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, factual_puzzle, longer_cardboard_32.
4. **AVQ-004-004** Does a hand disappear behind the prop it should hold in front?
   - Failure hypothesis: Incorrect depth ordering breaks the grasp.
   - Check or fix: Review hand-prop masks at contact extrema.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, factual_puzzle.
5. **AVQ-004-005** Are transparent surfaces ordered correctly with opaque objects?
   - Failure hypothesis: Transparency sorting creates impossible overlaps.
   - Check or fix: Test each intersecting layer from the final camera.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, factual_puzzle.
6. **AVQ-004-006** Does the hero pass through a foreground object without response?
   - Failure hypothesis: Occlusion hides a geometric collision.
   - Check or fix: Check trajectories against collision silhouettes.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, factual_puzzle.
7. **AVQ-004-007** Do objects change apparent depth without crossing a boundary?
   - Failure hypothesis: Sort order pops during movement.
   - Check or fix: Inspect depth swaps one frame at a time.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, factual_puzzle.
8. **AVQ-004-008** Can the viewer infer which route lies above another?
   - Failure hypothesis: Crossing paths have ambiguous elevation.
   - Check or fix: Add bridge, shadow or cutaway cues.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, factual_puzzle.
9. **AVQ-004-009** Is a distant object larger without an established scale reason?
   - Failure hypothesis: Projection cues imply impossible depth.
   - Check or fix: Compare world scale and camera projection.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: factual_puzzle.
10. **AVQ-004-010** Does parallax direction agree with camera travel?
   - Failure hypothesis: Layers move as if depth were inverted.
   - Check or fix: Plot layer displacement against declared depth.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: factual_puzzle.
11. **AVQ-004-011** Are contact shadows behind the correct object?
   - Failure hypothesis: Shadow stacking contradicts grounding.
   - Check or fix: Review shadow masks independently from color layers.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-004-012** Does a mask hide more than the physical occluder should?
   - Failure hypothesis: Loose masks remove visible limbs or props.
   - Check or fix: Compare matte contour to the actual boundary.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-004-013** Are soft alpha edges revealing the hidden layer unnaturally?
   - Failure hypothesis: Premultiplication or feathering creates ghost edges.
   - Check or fix: Inspect compositing over contrasting backgrounds.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-004-014** Does depth-of-field change imply a different focal plane than intended?
   - Failure hypothesis: Focus favors the wrong spatial relationship.
   - Check or fix: Mark focus targets against shot purpose.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-004-015** Can partly occluded characters still be counted fairly?
   - Failure hypothesis: Occlusion leaves ambiguous identity fragments.
   - Check or fix: Review visible identifying features for each counted entity.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: puzzle, educational.
16. **AVQ-004-016** Does the foreground reveal happen before the viewer needs it?
   - Failure hypothesis: Late disocclusion withholds causal information.
   - Check or fix: Move the reveal earlier or add an establishing cue.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-004-017** Are far objects clipped by a near-plane artifact?
   - Failure hypothesis: Camera settings remove legitimate scene geometry.
   - Check or fix: Check clipping planes at closest camera positions.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-004-018** Does a cutaway show interior parts in their real relative positions?
   - Failure hypothesis: Illustrative separation masquerades as spatial truth.
   - Check or fix: Label exploded offsets or restore spatial registration.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-004-019** Are stacked paper planes thick enough to match their shadows?
   - Failure hypothesis: Shadow depth exceeds the depicted material thickness.
   - Check or fix: Align layer spacing and shadow treatment.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-004-020** Does a rotating flat asset expose its lack of volume?
   - Failure hypothesis: Billboard rotation reveals an unintended paper edge.
   - Check or fix: Limit rotation or provide appropriate alternate geometry.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-004-021** Are reflections occluded consistently with the reflecting surface?
   - Failure hypothesis: Reflection content ignores scene boundaries.
   - Check or fix: Compare reflection mask with surface visibility.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-004-022** Does a moving camera reveal duplicate copies of one object?
   - Failure hypothesis: Patch layers overlap as two distinct objects.
   - Check or fix: Inspect seams during the entire camera move.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-004-023** Is an object hidden for so long that its return feels unmotivated?
   - Failure hypothesis: Occlusion becomes an unexplained teleport.
   - Check or fix: Retain an audible or visual continuity cue.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-004-024** Do atmospheric layers correctly exclude nearer objects?
   - Failure hypothesis: Fog paints over the wrong depth range.
   - Check or fix: Inspect depth masks against scene distances.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-004-025** Can depth be understood without relying solely on size?
   - Failure hypothesis: Identical-size assets flatten the scene.
   - Check or fix: Use overlap, ground contact and perspective cues together.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-004-026** Are depth transitions smooth enough for the intended medium?
   - Failure hypothesis: Layer snapping produces unintended spatial jumps.
   - Check or fix: Use controlled sorting boundaries or continuous geometry.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-004-027** Does the background show through a supposedly solid object?
   - Failure hypothesis: Alpha or topology holes contradict solidity.
   - Check or fix: Check object opacity and silhouette interiors.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-004-028** Are multiple viewpoints showing the same occluded state?
   - Failure hypothesis: Views disagree about object visibility and position.
   - Check or fix: Synchronize cameras to one scene-time sample.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-004-029** Does a label's leader line terminate on the visible object?
   - Failure hypothesis: Occluded endpoints attach to the wrong surface.
   - Check or fix: Reproject anchors and inspect final pixels.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-004-030** Is the occlusion itself doing useful storytelling?
   - Failure hypothesis: Obscuration creates difficulty without payoff.
   - Check or fix: Remove arbitrary blockers from the causal beat.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-004-031** Does the depth treatment remain coherent during a zoom?
   - Failure hypothesis: Screen-space layers scale as incompatible distances.
   - Check or fix: Compare scaling rates across near and far planes.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-004-032** Can a viewer tell an intentional hidden clue from missing artwork?
   - Failure hypothesis: Unexplained gaps resemble rendering errors.
   - Check or fix: Design a readable occluder and fair reveal.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
