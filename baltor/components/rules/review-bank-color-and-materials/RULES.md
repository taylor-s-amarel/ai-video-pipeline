# Adversarial review bank: D011 color and materials (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D011 color and materials". The questions below are the
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
- Modes: 32 visual, 2 human-audience.
- Need listening: 0; listening-only (no visual or machine route): none.
- Need a human audience: 2.
- Only answerable at final encode or delivery: none.
- Limited by style filter: `AVQ-011-008` (3d, cutout, educational).

## Named passes that draw on this area

- `default_32`: `AVQ-011-001`
- `longer_cardboard_32`: `AVQ-011-014`

## Questions

1. **AVQ-011-001** Can key categories be distinguished without hue alone?
   - Failure hypothesis: Color-only coding excludes some viewers.
   - Check or fix: Add shape, position or label redundancy.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32.
2. **AVQ-011-002** Do material properties match the action's implied friction?
   - Failure hypothesis: Slippery-looking objects behave as high-grip surfaces.
   - Check or fix: Align appearance and motion cues.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
3. **AVQ-011-003** Is the accent color reserved for meaningful emphasis?
   - Failure hypothesis: Every object uses the attention color.
   - Check or fix: Reduce accents on nonessential elements.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
4. **AVQ-011-004** Do adjacent materials separate at delivery resolution?
   - Failure hypothesis: Similar values merge distinct surfaces.
   - Check or fix: Adjust value, roughness or boundary treatment.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
5. **AVQ-011-005** Does the material imply a weight the animation contradicts?
   - Failure hypothesis: Metal-looking prop moves like foam.
   - Check or fix: Revise motion weight or material appearance.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
6. **AVQ-011-006** Are skin or character colors stable across shots?
   - Failure hypothesis: Grading changes identity unintentionally.
   - Check or fix: Compare color references under matched illumination.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
7. **AVQ-011-007** Is transparency revealing the intended contents clearly?
   - Failure hypothesis: Tint and reflections obscure the explanation.
   - Check or fix: Tune opacity and reflection balance.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
8. **AVQ-011-008** Does metallic shading retain shape in the chosen environment?
   - Failure hypothesis: Uninformative reflections make metal look flat.
   - Check or fix: Provide meaningful reflected structure.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: 3d, cutout, educational.
9. **AVQ-011-009** Are roughness changes motivated by actual surface variation?
   - Failure hypothesis: Random roughness looks like damage.
   - Check or fix: Use a coherent material variation map.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
10. **AVQ-011-010** Does the palette support the emotional transition?
   - Failure hypothesis: Color stays emotionally static despite a major turn.
   - Check or fix: Test a restrained motivated palette shift.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
11. **AVQ-011-011** Are warning colors used consistently?
   - Failure hypothesis: Red or amber sometimes means decoration.
   - Check or fix: Audit semantic color assignments.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-011-012** Does a color gradient accidentally imply quantitative data?
   - Failure hypothesis: Decorative shading looks like a heat map.
   - Check or fix: Separate decoration from measured encodings.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-011-013** Are bright saturated regions clipping in the output gamut?
   - Failure hypothesis: Color detail collapses after conversion.
   - Check or fix: Inspect encoded channels and gamut handling.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-011-014** Does a white object retain form on a light background?
   - Failure hypothesis: High-key palette loses boundaries.
   - Check or fix: Use controlled value and shadow separation.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: longer_cardboard_32.
15. **AVQ-011-015** Are cloth, paper and clay differentiated by appropriate cues?
   - Failure hypothesis: Different materials share generic plastic shading.
   - Check or fix: Choose specific roughness, edge and deformation behavior.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-011-016** Does the material scale match the object's physical scale?
   - Failure hypothesis: Grain makes miniature objects look enormous.
   - Check or fix: Compare texture feature size with object dimensions.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-011-017** Is the palette coherent across imported and original assets?
   - Failure hypothesis: Assets carry incompatible color treatments.
   - Check or fix: Normalize them within one approved palette.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-011-018** Do transparent overlays preserve readability underneath?
   - Failure hypothesis: Tint layers reduce contrast unpredictably.
   - Check or fix: Test the busiest underlying frame.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-011-019** Does wetness or gloss appear only where justified?
   - Failure hypothesis: Uniform shine makes every surface look wet.
   - Check or fix: Restrict specularity to material logic.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-011-020** Are color changes signaling state rather than arbitrary variation?
   - Failure hypothesis: Viewers infer a state transition that did not occur.
   - Check or fix: Document and audit state-color rules.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-011-021** Does the final grade preserve the original hierarchy?
   - Failure hypothesis: Global treatment promotes previously quiet colors.
   - Check or fix: Recheck focal contrast after grading.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-011-022** Is the background color compatible with the caption treatment?
   - Failure hypothesis: Changing scenery makes text contrast unstable.
   - Check or fix: Use a stable backing or adaptive verified treatment.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-011-023** Are textures and base colors fighting each other?
   - Failure hypothesis: Surface pattern destroys the intended palette.
   - Check or fix: Reduce texture contrast or recolor it coherently.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-011-024** Does a material's translucency change incorrectly with camera angle?
   - Failure hypothesis: Surface appears to pop between solid and transparent.
   - Check or fix: Inspect angle-dependent shading behavior.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-011-025** Are symbolic colors culturally appropriate for the intended audience?
   - Failure hypothesis: Color meaning is assumed to be universal.
   - Check or fix: Check audience interpretation before relying on symbolism.
   - Severity: medium. Modes: visual, human-audience. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-011-026** Does color distinguish before-and-after states clearly?
   - Failure hypothesis: The transformation is too subtle to notice.
   - Check or fix: Choose a visible state contrast with redundant cues.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-011-027** Are object interiors and cut surfaces materially plausible?
   - Failure hypothesis: Cutaway reveals the wrong material identity.
   - Check or fix: Assign coherent interior materials.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-011-028** Does a stylized material remain consistent through deformation?
   - Failure hypothesis: Texture or highlights detach from the body.
   - Check or fix: Track material coordinates on moving surfaces.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-011-029** Are dark outlines changing the perceived color category?
   - Failure hypothesis: Heavy contour overwhelms small colored regions.
   - Check or fix: Review filled shapes at actual display size.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-011-030** Does the palette accommodate both calm and urgent beats?
   - Failure hypothesis: Only one intensity level is available.
   - Check or fix: Reserve saturation and contrast for escalation.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-011-031** Can the audience tell a material change from a lighting change?
   - Failure hypothesis: Visual cause of transformation is ambiguous.
   - Check or fix: Keep one variable stable during the demonstration.
   - Severity: medium. Modes: visual, human-audience. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-011-032** Would a smaller material vocabulary improve coherence?
   - Failure hypothesis: Too many surface types fragment the world.
   - Check or fix: Consolidate materials by narrative function.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
