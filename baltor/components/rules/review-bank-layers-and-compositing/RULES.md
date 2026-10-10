# Adversarial review bank: D015 layers and compositing (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D015 layers and compositing". The questions below are the
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

- `default_32`: `AVQ-015-001`
- `visual_depth_contact`: `AVQ-015-001`, `AVQ-015-002`, `AVQ-015-003`, `AVQ-015-004`, `AVQ-015-005`, `AVQ-015-006`, `AVQ-015-007`, `AVQ-015-008`
- `final_delivery`: `AVQ-015-001`, `AVQ-015-002`, `AVQ-015-003`, `AVQ-015-004`, `AVQ-015-005`, `AVQ-015-006`, `AVQ-015-007`, `AVQ-015-008`

## Questions

1. **AVQ-015-001** Are all layers transformed by the intended shared camera?
   - Failure hypothesis: Foreground and background drift independently.
   - Check or fix: Compare common landmarks across layer transforms.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any. Passes: default_32, visual_depth_contact, final_delivery.
2. **AVQ-015-002** Do mattes preserve fine features without fringing?
   - Failure hypothesis: Hair or thin limbs are eroded or haloed.
   - Check or fix: Inspect alpha edges against light and dark backgrounds.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any. Passes: visual_depth_contact, final_delivery.
3. **AVQ-015-003** Is premultiplied alpha handled consistently?
   - Failure hypothesis: Dark or bright fringes appear at transparency edges.
   - Check or fix: Verify alpha convention at each compositing boundary.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any. Passes: visual_depth_contact, final_delivery.
4. **AVQ-015-004** Are blend modes appropriate for the intended physical effect?
   - Failure hypothesis: Additive or multiply treatment distorts object identity.
   - Check or fix: Compare isolated and composite layer appearance.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any. Passes: visual_depth_contact, final_delivery.
5. **AVQ-015-005** Does the layer stack reflect causal depth rather than file order?
   - Failure hypothesis: New assets appear above everything accidentally.
   - Check or fix: Use explicit semantic depth ordering.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any. Passes: visual_depth_contact, final_delivery.
6. **AVQ-015-006** Are shadows composited once rather than duplicated?
   - Failure hypothesis: Repeated shadow layers overdarken contact regions.
   - Check or fix: Audit shadow contribution per object.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any. Passes: visual_depth_contact, final_delivery.
7. **AVQ-015-007** Does global grading apply consistently to all intended layers?
   - Failure hypothesis: Overlays and scene assets have mismatched treatment.
   - Check or fix: Document which layers bypass the grade and why.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any. Passes: visual_depth_contact, final_delivery.
8. **AVQ-015-008** Are masks animated in the same coordinate space as their targets?
   - Failure hypothesis: Mask lag exposes hidden content.
   - Check or fix: Track mask-target alignment through the move.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any. Passes: visual_depth_contact, final_delivery.
9. **AVQ-015-009** Does a replacement background preserve existing light and perspective cues?
   - Failure hypothesis: Swap breaks integration while retaining old foreground.
   - Check or fix: Recheck projection, exposure and shadow compatibility.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
10. **AVQ-015-010** Are motion-blurred edges compatible across adjacent layers?
   - Failure hypothesis: Sharp cutouts sit against smeared scenery.
   - Check or fix: Match shutter assumptions or use deliberate graphic separation.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
11. **AVQ-015-011** Do overlays remain crisp without overpowering the scene?
   - Failure hypothesis: UI sharpness makes the world look accidentally soft.
   - Check or fix: Balance overlay contrast and scene detail.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
12. **AVQ-015-012** Are cached layers invalidated after dependent changes?
   - Failure hypothesis: Final composite includes stale animation or lighting.
   - Check or fix: Record dependency hashes and refresh affected caches.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
13. **AVQ-015-013** Does a hidden layer still cast an unintended effect?
   - Failure hypothesis: Invisible object leaves a shadow, glow or reflection.
   - Check or fix: Audit secondary contributions of disabled elements.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
14. **AVQ-015-014** Are nested transforms applied exactly once?
   - Failure hypothesis: Parent and child scaling double the movement.
   - Check or fix: Test a known anchor through the transform chain.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
15. **AVQ-015-015** Does a screen-space effect remain confined to its intended region?
   - Failure hypothesis: Glow, blur or displacement leaks into captions.
   - Check or fix: Inspect effect masks around protected areas.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
16. **AVQ-015-016** Are depth mattes temporally aligned with color frames?
   - Failure hypothesis: One-frame offset creates edge tearing.
   - Check or fix: Compare frame indices across render passes.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
17. **AVQ-015-017** Does a color key remove similarly colored subject details?
   - Failure hypothesis: Keying erases clothing or props.
   - Check or fix: Review retained subject pixels against the key range.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
18. **AVQ-015-018** Are transparent assets stored with enough edge color information?
   - Failure hypothesis: Resampling reveals contaminated matte colors.
   - Check or fix: Inspect edge pixels before and after scaling.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
19. **AVQ-015-019** Does compositing preserve the intended color space?
   - Failure hypothesis: Linear and display-referred operations are mixed.
   - Check or fix: Document conversions around blends and grading.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
20. **AVQ-015-020** Are repeated elements independently addressable when the story requires it?
   - Failure hypothesis: One baked layer prevents necessary repairs.
   - Check or fix: Separate only the elements needing distinct control.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
21. **AVQ-015-021** Does a foreground wipe reveal the correct underlying shot at every frame?
   - Failure hypothesis: Transition matte exposes stale or wrong content.
   - Check or fix: Inspect the wipe boundary across its full duration.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
22. **AVQ-015-022** Are adjustment layers scoped to the correct shot range?
   - Failure hypothesis: Grade or blur leaks into neighboring scenes.
   - Check or fix: Check in/out boundaries and nested compositions.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
23. **AVQ-015-023** Does a drop shadow imply inappropriate physical depth for text?
   - Failure hypothesis: Labels look like floating solid objects.
   - Check or fix: Use annotation-specific shadow restraint.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
24. **AVQ-015-024** Are compound masks preserving holes and internal contours?
   - Failure hypothesis: Fill rules close intended openings.
   - Check or fix: Inspect even-odd and winding behavior on key shapes.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
25. **AVQ-015-025** Does resampling order unnecessarily soften the subject?
   - Failure hypothesis: Repeated scale operations degrade edges.
   - Check or fix: Composite at an appropriate master scale once.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
26. **AVQ-015-026** Are layer names and IDs sufficient to locate the visible defect?
   - Failure hypothesis: Opaque naming makes targeted repair expensive.
   - Check or fix: Map visible elements to stable source identifiers.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
27. **AVQ-015-027** Does the composite include unintended guide or debug layers?
   - Failure hypothesis: Production scaffolding appears in the final movie.
   - Check or fix: Scan final frames for guides, handles and diagnostics.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
28. **AVQ-015-028** Are reflections derived from the same current scene state?
   - Failure hypothesis: Reflection layer contains outdated poses.
   - Check or fix: Link reflection generation to the shared state.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
29. **AVQ-015-029** Does an effect respect occlusion by nearer objects?
   - Failure hypothesis: Glow or particles appear through solid foregrounds.
   - Check or fix: Apply appropriate depth-aware masks.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
30. **AVQ-015-030** Are per-layer frame rates reconciled explicitly?
   - Failure hypothesis: Different rates create stutter or duplicated motion.
   - Check or fix: Normalize timing while preserving source intent.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
31. **AVQ-015-031** Does a compositing shortcut remain valid at the largest planned camera move?
   - Failure hypothesis: Patch works only in the preview framing.
   - Check or fix: Stress-test the actual camera envelope.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
32. **AVQ-015-032** Would separating one problematic layer enable a much cleaner fix?
   - Failure hypothesis: Baked composite prevents precise correction.
   - Check or fix: Isolate the smallest repairable element.
   - Severity: medium. Modes: visual. Stages: production, edit, final-encode. Style filters: any.
