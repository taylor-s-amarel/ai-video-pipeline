# Adversarial review bank: D012 texture and detail (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D012 texture and detail". The questions below are the
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
- Limited by style filter: `AVQ-012-009` (puzzle, educational), `AVQ-012-015` (3d, cutout, educational).

## Named passes that draw on this area

- `default_32`: `AVQ-012-001`
- `longer_cardboard_32`: `AVQ-012-004`

## Questions

1. **AVQ-012-001** Does texture obscure the smallest important feature?
   - Failure hypothesis: Surface detail competes with evidence.
   - Check or fix: Inspect the feature after downsampling and encoding.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32.
2. **AVQ-012-002** Are texture seams visible during the actual camera move?
   - Failure hypothesis: UV boundaries become exposed in motion.
   - Check or fix: Review all used angles and deformation states.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
3. **AVQ-012-003** Does texture swim across moving geometry?
   - Failure hypothesis: Coordinates are anchored to the wrong space.
   - Check or fix: Track a recognizable texel against the surface.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
4. **AVQ-012-004** Are repeating patterns conspicuous enough to break scale?
   - Failure hypothesis: Tiling reveals asset construction.
   - Check or fix: Vary placement or use a less periodic pattern.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: longer_cardboard_32.
5. **AVQ-012-005** Does fine detail shimmer between frames?
   - Failure hypothesis: Subpixel frequencies alias during movement.
   - Check or fix: Reduce frequency or improve filtering.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
6. **AVQ-012-006** Are distant textures simplified appropriately?
   - Failure hypothesis: High-frequency detail creates background noise.
   - Check or fix: Use distance-aware detail reduction.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
7. **AVQ-012-007** Does grain belong to the image or incorrectly follow objects?
   - Failure hypothesis: Noise behavior contradicts the intended medium.
   - Check or fix: Choose screen-space or surface-space grain deliberately.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
8. **AVQ-012-008** Are texture features consistent with the claimed material?
   - Failure hypothesis: Stone grain appears on paper or fabric.
   - Check or fix: Use material-specific reference logic.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
9. **AVQ-012-009** Does procedural variation produce target-like false positives?
   - Failure hypothesis: Random shapes resemble puzzle objects.
   - Check or fix: Inspect generated backgrounds before placing targets.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: puzzle, educational.
10. **AVQ-012-010** Are scratches and wear located where use would cause them?
   - Failure hypothesis: Random distressing feels decorative and implausible.
   - Check or fix: Place wear around contact and exposure areas.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
11. **AVQ-012-011** Is outline detail stable at the output pixel grid?
   - Failure hypothesis: Thin strokes flicker after rasterization.
   - Check or fix: Test minimum stroke thickness in the final encode.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-012-012** Does detail density change abruptly between adjacent assets?
   - Failure hypothesis: One object looks imported from another production.
   - Check or fix: Normalize detail scale and contrast.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-012-013** Are facial textures preserving expression rather than masking it?
   - Failure hypothesis: Patterning obscures eyes and mouth.
   - Check or fix: Quiet detail around expressive features.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-012-014** Does motion blur turn detailed surfaces into distracting streaks?
   - Failure hypothesis: Texture dominates blur direction.
   - Check or fix: Reduce detail or adjust blur for readability.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-012-015** Are normal maps creating impossible bumps at silhouettes?
   - Failure hypothesis: Shading suggests geometry the outline denies.
   - Check or fix: Check silhouette and bump scale together.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: 3d, cutout, educational.
16. **AVQ-012-016** Does texture remain aligned across a cut or replacement asset?
   - Failure hypothesis: Surface identity changes between views.
   - Check or fix: Compare persistent landmarks on the material.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-012-017** Is decorative text baked into a texture actually readable and correct?
   - Failure hypothesis: Pseudo-lettering looks like misinformation.
   - Check or fix: Replace illegible text with verified lettering or remove it.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-012-018** Are compression blocks strongest in the most important region?
   - Failure hypothesis: Detail consumes bitrate needed for the subject.
   - Check or fix: Simplify noisy areas and test encoding allocation.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-012-019** Does a handmade texture repeat too perfectly?
   - Failure hypothesis: Mechanical repetition contradicts the intended craft feel.
   - Check or fix: Introduce bounded meaningful variation.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-012-020** Are particles sized consistently with the scene scale?
   - Failure hypothesis: Dust or fibers imply the wrong object size.
   - Check or fix: Compare particle dimensions with familiar references.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-012-021** Does detail communicate function rather than merely busyness?
   - Failure hypothesis: Surface complexity adds no useful information.
   - Check or fix: Remove details that neither explain nor characterize.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-012-022** Are rough edges deliberate at all scales?
   - Failure hypothesis: Accidental raster artifacts mimic a broken contour.
   - Check or fix: Inspect vector source and encoded edge behavior.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-012-023** Does a texture atlas leak neighboring colors at borders?
   - Failure hypothesis: Sampling creates unwanted edge stripes.
   - Check or fix: Check padding and filtering around UV islands.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-012-024** Are surface markings distorted by deformation unintentionally?
   - Failure hypothesis: Labels stretch until misleading.
   - Check or fix: Use appropriate attachment or limit deformation.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-012-025** Does a small pattern create moire in the target viewing setup?
   - Failure hypothesis: Repeated lines interfere with the display grid.
   - Check or fix: Preview the intended downscaled output.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-012-026** Are texture transitions gradual enough across level-of-detail changes?
   - Failure hypothesis: Visible popping interrupts motion.
   - Check or fix: Match transition frequency and blend behavior.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-012-027** Does a procedural seed change between frames unexpectedly?
   - Failure hypothesis: Random detail flickers without physical cause.
   - Check or fix: Fix seeds or evolve noise continuously.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-012-028** Are environment textures richer than the hero for a reason?
   - Failure hypothesis: Background detail steals attention.
   - Check or fix: Reduce environmental detail near the focal action.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-012-029** Can the scene still be read when texture is temporarily removed?
   - Failure hypothesis: Texture compensates for weak structure.
   - Check or fix: Review a flat-color structural pass.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-012-030** Does an important printed mark stay legible on curved surfaces?
   - Failure hypothesis: Curvature hides or distorts the identifier.
   - Check or fix: Place the mark on a readable region.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-012-031** Are apparent dirt or damage marks consistent with the story state?
   - Failure hypothesis: Wear changes without an event.
   - Check or fix: Track material-state continuity.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-012-032** Would larger simpler texture features survive delivery better?
   - Failure hypothesis: Microdetail vanishes while retaining visual noise.
   - Check or fix: Test a lower-frequency texture variant.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
