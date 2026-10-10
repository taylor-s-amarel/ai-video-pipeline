# Adversarial review bank: D010 lighting and shadows (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D010 lighting and shadows". The questions below are the
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
- Need listening: 0; listening-only (no visual or machine route): none.
- Need a human audience: 0.
- Only answerable at final encode or delivery: none.
- Limited by style filter: none.

## Named passes that draw on this area

- `default_32`: `AVQ-010-004`
- `longer_cardboard_32`: `AVQ-010-004`

## Questions

1. **AVQ-010-001** Does the key light reveal the important form?
   - Failure hypothesis: Lighting hides the feature being explained.
   - Check or fix: Inspect the focal object without decorative lights.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
2. **AVQ-010-002** Are cast shadows consistent with the apparent light direction?
   - Failure hypothesis: Objects seem lit by unrelated worlds.
   - Check or fix: Trace shadows back toward plausible sources.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
3. **AVQ-010-003** Does the hero's face remain readable through the action?
   - Failure hypothesis: Turning moves expression into unhelpful darkness.
   - Check or fix: Review face values at orientation extrema.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
4. **AVQ-010-004** Are contact shadows close enough to ground objects?
   - Failure hypothesis: Detached shadows create floating.
   - Check or fix: Inspect contact regions at native resolution.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32, longer_cardboard_32.
5. **AVQ-010-005** Does a moving light change all affected layers consistently?
   - Failure hypothesis: Only some objects respond to illumination.
   - Check or fix: Audit shared light influence across the composite.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
6. **AVQ-010-006** Are specular highlights clipping away important detail?
   - Failure hypothesis: Bright reflections erase shape or labels.
   - Check or fix: Inspect highlight values and reduce intensity or roughness.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
7. **AVQ-010-007** Does the background receive more dramatic lighting than the hero?
   - Failure hypothesis: Scenery attracts attention at the wrong time.
   - Check or fix: Rebalance light contrast by narrative priority.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
8. **AVQ-010-008** Are shadows soft at a scale consistent with the light source?
   - Failure hypothesis: Tiny source produces implausibly broad penumbrae.
   - Check or fix: Match source size and shadow softness deliberately.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
9. **AVQ-010-009** Does ambient fill flatten the scene beyond the intended style?
   - Failure hypothesis: All surfaces have similar values.
   - Check or fix: Restore controlled directional contrast.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
10. **AVQ-010-010** Is a rim light motivated or visibly decorative?
   - Failure hypothesis: Artificial outline breaks the material illusion.
   - Check or fix: Reduce rim strength or establish its source.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
11. **AVQ-010-011** Does lighting change continuity across an unbroken action?
   - Failure hypothesis: Cut suggests time or location changed.
   - Check or fix: Compare light direction and exposure at the edit.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-010-012** Are translucent materials transmitting plausible color and light?
   - Failure hypothesis: Glass or wax behaves like opaque plastic.
   - Check or fix: Inspect transmission against the style's material rules.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-010-013** Does the shadow show a different pose than the character?
   - Failure hypothesis: Cached or mismatched shadow reveals inconsistency.
   - Check or fix: Compare pose silhouettes at key frames.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-010-014** Are overhead objects casting shadows onto the right surfaces?
   - Failure hypothesis: Projection ignores receiving geometry.
   - Check or fix: Review receiver masks or shadow geometry.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-010-015** Does a dark scene preserve enough information for the task?
   - Failure hypothesis: Atmosphere makes required evidence unreadable.
   - Check or fix: Raise selective fill rather than global brightness alone.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-010-016** Is the lighting gradient stable during camera movement?
   - Failure hypothesis: Screen-space shading slides over the world.
   - Check or fix: Anchor illumination to the intended coordinate space.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-010-017** Are emissive objects visibly affecting nearby surfaces when needed?
   - Failure hypothesis: Glow looks pasted on rather than luminous.
   - Check or fix: Add restrained local response or clarify graphic style.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-010-018** Does bloom conceal small text or contact edges?
   - Failure hypothesis: Glow spreads over evidence-bearing boundaries.
   - Check or fix: Limit bloom around required information.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-010-019** Are transparent shadows appropriately different from opaque shadows?
   - Failure hypothesis: Glass casts a solid cutout unexpectedly.
   - Check or fix: Adjust transmission or label the stylization.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-010-020** Does ambient occlusion create dirty halos around moving parts?
   - Failure hypothesis: AO exaggeration looks like grime or gaps.
   - Check or fix: Reduce radius or strength at joints.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-010-021** Are shadow transitions temporally stable?
   - Failure hypothesis: Sampling noise flickers as geometry moves.
   - Check or fix: Inspect consecutive encoded frames in shadow regions.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-010-022** Does exposure adaptation pump during a small bright event?
   - Failure hypothesis: Automatic exposure changes the whole scene distracting.
   - Check or fix: Lock or smooth exposure for the shot.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-010-023** Is the eye highlight consistent enough to preserve gaze?
   - Failure hypothesis: Highlights wander independently of head and light.
   - Check or fix: Track highlight placement across expressions.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-010-024** Are light and shadow colors compatible with the palette?
   - Failure hypothesis: Unrelated color temperatures fracture the image.
   - Check or fix: Choose a coherent warm-cool lighting relationship.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-010-025** Does a shadow incorrectly imply a dangerous gap or obstacle?
   - Failure hypothesis: Shadow geometry miscommunicates the route.
   - Check or fix: Inspect shadows separately from solid surfaces.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-010-026** Can the important shape be read without its texture?
   - Failure hypothesis: Lighting relies on painted detail to suggest volume.
   - Check or fix: Review a neutral-material lighting pass.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-010-027** Does a backlit silhouette reveal the intended pose clearly?
   - Failure hypothesis: Merged limbs make backlighting unreadable.
   - Check or fix: Adjust pose or local background light.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-010-028** Are reflections of lights stable on deforming surfaces?
   - Failure hypothesis: Highlight popping exposes normal errors.
   - Check or fix: Inspect normals and roughness through deformation.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-010-029** Does the final grade preserve shadow detail after encoding?
   - Failure hypothesis: Compression crushes subtle dark information.
   - Check or fix: Compare source and decoded shadow regions.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-010-030** Is the time-of-day cue compatible with the story's timeline?
   - Failure hypothesis: Lighting contradicts stated chronology.
   - Check or fix: Check sky, shadow direction and narrative timing.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-010-031** Does lighting support the reveal by changing attention naturally?
   - Failure hypothesis: Reveal arrives in an already cluttered light pattern.
   - Check or fix: Reserve contrast for the newly important element.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-010-032** Would fewer light sources produce a more coherent image?
   - Failure hypothesis: Complex lighting creates contradictory cues.
   - Check or fix: Test a simplified key-fill setup.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
