# Adversarial review bank: D003 foreground background separation (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D003 foreground background separation". The questions below are the
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
- Limited by style filter: none.

## Named passes that draw on this area

- `default_32`: `AVQ-003-001`
- `visual_depth_contact`: `AVQ-003-001`, `AVQ-003-002`, `AVQ-003-003`, `AVQ-003-004`, `AVQ-003-005`, `AVQ-003-006`, `AVQ-003-007`, `AVQ-003-008`
- `accessible_text`: `AVQ-003-001`, `AVQ-003-002`, `AVQ-003-003`, `AVQ-003-004`, `AVQ-003-005`, `AVQ-003-006`, `AVQ-003-007`, `AVQ-003-008`, `AVQ-003-009`, `AVQ-003-010`
- `longer_cardboard_32`: `AVQ-003-001`

## Questions

1. **AVQ-003-001** Does the hero's outline merge with the scenery at any key pose?
   - Failure hypothesis: Matching values erase the silhouette.
   - Check or fix: Inspect key poses over grayscale backgrounds.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: default_32, visual_depth_contact, accessible_text, longer_cardboard_32.
2. **AVQ-003-002** Are foreground and background equally sharp without a reason?
   - Failure hypothesis: Every layer demands equal attention.
   - Check or fix: Use controlled detail or focus hierarchy.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, accessible_text.
3. **AVQ-003-003** Does background motion compete with the hero's reaction?
   - Failure hypothesis: Ambient activity masks the meaningful gesture.
   - Check or fix: Pause or reduce background motion during the reaction.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, accessible_text.
4. **AVQ-003-004** Is a dark costume lost against a dark set region?
   - Failure hypothesis: Local contrast collapses along the path.
   - Check or fix: Track costume-background contrast throughout movement.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, accessible_text.
5. **AVQ-003-005** Do background objects resemble extra limbs on the hero?
   - Failure hypothesis: Aligned props create anatomical ambiguity.
   - Check or fix: Move the prop or change camera angle.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, accessible_text.
6. **AVQ-003-006** Does the hero cross a bright patch just before the payoff?
   - Failure hypothesis: Background flash hijacks the eye.
   - Check or fix: Reduce patch contrast or retime the crossing.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, accessible_text.
7. **AVQ-003-007** Are labels visually mistaken for physical scene objects?
   - Failure hypothesis: Overlay styling implies false spatial membership.
   - Check or fix: Use a consistent annotation treatment.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, accessible_text.
8. **AVQ-003-008** Can target objects be distinguished from background texture?
   - Failure hypothesis: Texture contains target-like forms.
   - Check or fix: Inspect texture without target layers present.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: visual_depth_contact, accessible_text.
9. **AVQ-003-009** Does atmospheric depth weaken an essential distant clue?
   - Failure hypothesis: Depth treatment removes required information.
   - Check or fix: Keep evidence contrast above the chosen viewing threshold.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: accessible_text.
10. **AVQ-003-010** Are background crowds individual when the story needs a mass?
   - Failure hypothesis: Excess individuality produces visual noise.
   - Check or fix: Group distant figures while preserving meaningful identities.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any. Passes: accessible_text.
11. **AVQ-003-011** Do foreground silhouettes block facial reactions?
   - Failure hypothesis: Framing elements cover expression at the worst moment.
   - Check or fix: Plot overlap during the full reaction interval.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
12. **AVQ-003-012** Does scenery contain a stronger face-like pattern than the hero?
   - Failure hypothesis: Pareidolia steals attention from intended characters.
   - Check or fix: Simplify face-like background clusters.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
13. **AVQ-003-013** Are foreground edge treatments consistent with the background medium?
   - Failure hypothesis: Cutout edges look pasted onto incompatible art.
   - Check or fix: Match appropriate softness, grain and contour logic.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
14. **AVQ-003-014** Does foreground saturation overwhelm subtle background evidence?
   - Failure hypothesis: Accent color makes the clue easy to miss.
   - Check or fix: Rebalance saturation around the evidence beat.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
15. **AVQ-003-015** Is the background too blank to establish contact and scale?
   - Failure hypothesis: Minimalism removes grounding cues.
   - Check or fix: Add restrained ground plane and reference details.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
16. **AVQ-003-016** Does a background line continue through the hero as a tangent?
   - Failure hypothesis: Apparent line continuity flattens the layer separation.
   - Check or fix: Break or relocate the line behind the subject.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
17. **AVQ-003-017** Is the hero distinguishable during backlighting?
   - Failure hypothesis: Silhouette merges into an uncontrolled dark mass.
   - Check or fix: Preserve contour or adjust background luminance.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
18. **AVQ-003-018** Are distant outlines heavier than foreground outlines?
   - Failure hypothesis: Line weight reverses the depth hierarchy.
   - Check or fix: Normalize contour weight by intended depth logic.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
19. **AVQ-003-019** Does background contrast rise during narration-heavy passages?
   - Failure hypothesis: Scenery competes with reading and listening.
   - Check or fix: Reduce nonessential contrast during information delivery.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
20. **AVQ-003-020** Can a newcomer identify which objects are interactive?
   - Failure hypothesis: Visual affordances do not distinguish usable props.
   - Check or fix: Give important props clear placement or introduction.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
21. **AVQ-003-021** Does the background change imply a location change unintentionally?
   - Failure hypothesis: Palette or texture shifts break scene identity.
   - Check or fix: Match persistent landmarks across adjacent shots.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
22. **AVQ-003-022** Are foreground particles obscuring the decisive contact frame?
   - Failure hypothesis: Effects conceal whether the action succeeded.
   - Check or fix: Delay or thin particles at the contact moment.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
23. **AVQ-003-023** Does a moving background make a stationary subject seem to drift?
   - Failure hypothesis: Relative motion creates unintended self-motion.
   - Check or fix: Add stable grounding cues or change motion balance.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
24. **AVQ-003-024** Do shadows merge foreground and background into one blob?
   - Failure hypothesis: Shadow design removes object separation.
   - Check or fix: Adjust shadow softness, offset or intensity.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
25. **AVQ-003-025** Does a light outline become a distracting halo?
   - Failure hypothesis: Separation aid looks like a compositing defect.
   - Check or fix: Test subtler contour and local-background adjustments.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
26. **AVQ-003-026** Are foreground and background using incompatible perspective cues?
   - Failure hypothesis: The subject appears pasted into another world.
   - Check or fix: Compare horizon, vanishing directions and scale cues.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
27. **AVQ-003-027** Can background story details be discovered without stealing the main beat?
   - Failure hypothesis: Secondary storytelling competes with primary causality.
   - Check or fix: Place discoveries in quieter intervals.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
28. **AVQ-003-028** Does color grading erase previously good layer separation?
   - Failure hypothesis: Final treatment compresses local contrast.
   - Check or fix: Repeat separation checks on the encoded graded output.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
29. **AVQ-003-029** Are reflected subjects confused with additional real subjects?
   - Failure hypothesis: Reflections lack a clear surface context.
   - Check or fix: Make the reflective boundary and relationship legible.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
30. **AVQ-003-030** Does foreground blur hide information the viewer must use?
   - Failure hypothesis: Depth-of-field prioritizes atmosphere over evidence.
   - Check or fix: Keep task-relevant objects in an inspectable focus range.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
31. **AVQ-003-031** Can the scene remain readable on a dim phone display?
   - Failure hypothesis: Low-end viewing conditions collapse contrast.
   - Check or fix: Preview at modest brightness and intended size.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
32. **AVQ-003-032** Are guide lines strong enough to remain visible in the overview?
   - Failure hypothesis: Navigation cues disappear when the camera pulls back.
   - Check or fix: Compare the wide encoded frame at phone size and adjust guide contrast if needed.
   - Severity: medium. Modes: visual. Stages: storyboard, production, final-encode. Style filters: any.
