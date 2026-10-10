# Adversarial review bank: D020 text typography (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D020 text typography". The questions below are the
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

- Severity: 22 high, 10 medium.
- Modes: 32 visual, 1 auditory, 17 machine, 21 human-audience.
- Need listening: 1 (none are listening-only).
- Need a human audience: 21.
- Only answerable at final encode or delivery: none.
- Limited by style filter: `AVQ-020-002` (typographic), `AVQ-020-003` (screen-recording, educational, typographic), `AVQ-020-005` (typographic, educational), `AVQ-020-007` (typographic, educational), `AVQ-020-008` (educational), `AVQ-020-009` (typographic), `AVQ-020-011` (vector, educational, 3d), `AVQ-020-012` (educational, 3d, vector), `AVQ-020-013` (typographic), `AVQ-020-014` (educational, typographic), `AVQ-020-015` (typographic), `AVQ-020-017` (typographic, educational), `AVQ-020-018` (educational, live-action), `AVQ-020-019` (vector, typographic), `AVQ-020-020` (typographic), `AVQ-020-021` (typographic), `AVQ-020-022` (educational, typographic), `AVQ-020-023` (educational), `AVQ-020-024` (typographic, 3d), `AVQ-020-025` (educational, typographic), `AVQ-020-026` (typographic), `AVQ-020-027` (educational), `AVQ-020-028` (3d, live-action), `AVQ-020-029` (typographic), `AVQ-020-030` (educational).

## Named passes that draw on this area

- `default_32`: `AVQ-020-001`
- `accessible_text`: `AVQ-020-001`, `AVQ-020-002`, `AVQ-020-003`, `AVQ-020-004`, `AVQ-020-005`, `AVQ-020-006`, `AVQ-020-007`, `AVQ-020-008`, `AVQ-020-009`, `AVQ-020-010`
- `longer_cardboard_32`: `AVQ-020-001`

## Questions

1. **AVQ-020-001** Can the smallest essential label be read at the intended phone viewing size without zooming?
   - Failure hypothesis: Native-resolution review hides text that collapses at delivery scale.
   - Check or fix: Inspect the encoded video at ordinary phone size and enlarge necessary labels.
   - Severity: high. Modes: visual, human-audience. Stages: edit, final-encode, delivery. Style filters: any. Passes: default_32, accessible_text, longer_cardboard_32.
2. **AVQ-020-002** Do thin letter strokes survive the final encode rather than flicker or disappear?
   - Failure hypothesis: Compression and rasterization erase fine typographic detail.
   - Check or fix: Compare source and encoded crops across several frames.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: typographic. Passes: accessible_text.
3. **AVQ-020-003** Is the typeface's distinction between similar characters sufficient for the exact codes, numbers, or names shown?
   - Failure hypothesis: Ambiguous glyphs change the information a viewer reads.
   - Check or fix: Test the actual strings and replace the face or annotate ambiguous characters.
   - Severity: high. Modes: visual, human-audience. Stages: storyboard, edit. Style filters: screen-recording, educational, typographic. Passes: accessible_text.
4. **AVQ-020-004** Does text remain readable across the brightest and darkest parts of the moving background?
   - Failure hypothesis: A single contrast check misses background changes under the text.
   - Check or fix: Inspect the complete text interval and add a stable backing where needed.
   - Severity: high. Modes: machine, visual. Stages: edit, final-encode. Style filters: any. Passes: accessible_text.
5. **AVQ-020-005** Are line breaks preserving phrases that must be understood together?
   - Failure hypothesis: Awkward wrapping splits negation, quantities, or modifier relationships.
   - Check or fix: Rewrap actual text manually at each delivery layout.
   - Severity: medium. Modes: visual, human-audience. Stages: storyboard, edit. Style filters: typographic, educational. Passes: accessible_text.
6. **AVQ-020-006** Is the typographic hierarchy showing the main claim before its supporting detail?
   - Failure hypothesis: Equal size and weight leave viewers without a reading order.
   - Check or fix: Reduce secondary emphasis and test the first item readers notice.
   - Severity: medium. Modes: visual, human-audience. Stages: storyboard, animatic, edit. Style filters: any. Passes: accessible_text.
7. **AVQ-020-007** Does the animation finish forming each word before the viewer needs to act on it?
   - Failure hypothesis: Letter-by-letter motion delays access to essential instruction.
   - Check or fix: Reveal urgent instructions as complete phrases and retime the action.
   - Severity: high. Modes: machine, visual, human-audience. Stages: animatic, edit. Style filters: typographic, educational. Passes: accessible_text.
8. **AVQ-020-008** Are number formatting and units unambiguous for the intended audience?
   - Failure hypothesis: Locale conventions or missing units change the apparent magnitude.
   - Check or fix: Specify units and consistent separators in the exact on-screen values.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, storyboard, edit. Style filters: educational. Passes: accessible_text.
9. **AVQ-020-009** Does justified or stretched text create word spacing that changes readability at short exposure times?
   - Failure hypothesis: Artificial spacing breaks word recognition.
   - Check or fix: Use natural spacing and compare brief-exposure reading.
   - Severity: medium. Modes: visual, human-audience. Stages: storyboard, edit. Style filters: typographic. Passes: accessible_text.
10. **AVQ-020-010** Is text positioned inside the actual safe region after reframing and player overlays?
   - Failure hypothesis: Reframing or controls cover critical words.
   - Check or fix: Preview platform framing and move essentials into verified safe space.
   - Severity: high. Modes: machine, visual. Stages: edit, final-encode, delivery. Style filters: any. Passes: accessible_text.
11. **AVQ-020-011** Do labels stay attached to the objects they describe during camera motion?
   - Failure hypothesis: Screen-space labels drift away from scene-space targets.
   - Check or fix: Track attachment points through the full move or use stable leader lines.
   - Severity: high. Modes: machine, visual. Stages: production, edit. Style filters: vector, educational, 3d.
12. **AVQ-020-012** Are leader lines terminating on distinct targets rather than crossing or pointing into empty space?
   - Failure hypothesis: Annotation geometry creates incorrect object associations.
   - Check or fix: Inspect the crowded state and reroute ambiguous connectors.
   - Severity: high. Modes: machine, visual, human-audience. Stages: production, edit. Style filters: educational, 3d, vector.
13. **AVQ-020-013** Does a kinetic word change its meaning through cropping or motion before the full phrase is available?
   - Failure hypothesis: Moving fragments create an unintended statement.
   - Check or fix: Inspect every intermediate readable fragment and revise the animation.
   - Severity: high. Modes: machine, visual. Stages: production, edit. Style filters: typographic.
14. **AVQ-020-014** Are minus signs, decimal points, superscripts, and exponents visible after scaling?
   - Failure hypothesis: Small mathematical marks disappear while surrounding digits remain readable.
   - Check or fix: Verify each critical mark in the delivered encode at target size.
   - Severity: high. Modes: machine, visual, human-audience. Stages: edit, final-encode. Style filters: educational, typographic.
15. **AVQ-020-015** Is a decorative display face being used for paragraphs that require sustained reading?
   - Failure hypothesis: Ornament impairs word recognition over longer passages.
   - Check or fix: Reserve the display face for short emphasis and simplify body type.
   - Severity: medium. Modes: visual, human-audience. Stages: storyboard, edit. Style filters: typographic.
16. **AVQ-020-016** Do font fallbacks preserve both meaning and layout when the project is reopened elsewhere?
   - Failure hypothesis: Missing fonts change glyphs, wrapping, or timing.
   - Check or fix: Reopen in a clean environment and compare rendered text extents.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode, delivery. Style filters: any.
17. **AVQ-020-017** Does animated emphasis land on the intended word without reversing the sentence's meaning?
   - Failure hypothesis: Highlight timing stresses a qualifier or negation incorrectly.
   - Check or fix: Review the sentence with its actual emphasis sequence.
   - Severity: high. Modes: visual, human-audience. Stages: script, animatic, edit. Style filters: typographic, educational.
18. **AVQ-020-018** Are quotation marks, attribution, and paraphrase styling clear enough to distinguish someone else's words from the narrator's?
   - Failure hypothesis: Typography blurs quotation and authorial assertion.
   - Check or fix: Apply a consistent quotation treatment and verify exact attribution.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, edit. Style filters: educational, live-action.
19. **AVQ-020-019** Does the text remain crisp when transformed, or is a low-resolution raster layer being enlarged?
   - Failure hypothesis: Typography is scaled beyond its raster source resolution.
   - Check or fix: Render at final size or preserve vector text through compositing.
   - Severity: medium. Modes: machine, visual. Stages: production, final-encode. Style filters: vector, typographic.
20. **AVQ-020-020** Are right-to-left runs, mixed-direction numbers, or combined scripts displayed in the correct order?
   - Failure hypothesis: Shaping or bidirectional handling rearranges meaning.
   - Check or fix: Have a fluent reader inspect the exact rendered strings.
   - Severity: high. Modes: visual, human-audience. Stages: production, final-encode. Style filters: typographic.
21. **AVQ-020-021** Do accented characters and non-Latin glyphs match the visual weight and baseline of surrounding text?
   - Failure hypothesis: Partial font coverage produces conspicuous fallback glyphs.
   - Check or fix: Choose full-coverage fonts and inspect representative strings.
   - Severity: medium. Modes: machine, visual. Stages: production, final-encode. Style filters: typographic.
22. **AVQ-020-022** Are automatically emphasized keywords actually important in context, including when they appear in negations or quotations?
   - Failure hypothesis: Keyword matching highlights words whose local meaning should not receive emphasis.
   - Check or fix: Review every emphasis match in its complete sentence and correct semantic false positives.
   - Severity: medium. Modes: machine, visual, human-audience. Stages: script, storyboard, edit. Style filters: educational, typographic.
23. **AVQ-020-023** Is a title's visual treatment making a tentative claim look definitive?
   - Failure hypothesis: Bold headline hierarchy suppresses uncertainty qualifiers.
   - Check or fix: Place the scope and qualifier within the same readable hierarchy.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, edit. Style filters: educational.
24. **AVQ-020-024** Does text cast or receive effects that reduce the counters and internal spaces needed for reading?
   - Failure hypothesis: Glow, shadow, or extrusion closes letter shapes.
   - Check or fix: Compare effect-free and treated text at delivery size.
   - Severity: medium. Modes: visual, human-audience. Stages: production, edit. Style filters: typographic, 3d.
25. **AVQ-020-025** Are tabular numbers aligned so viewers can compare place value rather than infer from uneven glyph widths?
   - Failure hypothesis: Proportional spacing disguises numerical differences.
   - Check or fix: Use tabular figures or a clearly aligned layout.
   - Severity: medium. Modes: visual, human-audience. Stages: storyboard, edit. Style filters: educational, typographic.
26. **AVQ-020-026** Does auto-fitting silently shrink the most important or longest message below the approved minimum?
   - Failure hypothesis: Fit-to-box logic prioritizes containment over readability.
   - Check or fix: Log fitted sizes and redesign outlier text instead of shrinking indefinitely.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: typographic.
27. **AVQ-020-027** Are labels introduced with terminology that matches the narration and later references?
   - Failure hypothesis: Synonyms look like separate concepts in a short film.
   - Check or fix: Reconcile the spoken and displayed term lists.
   - Severity: high. Modes: machine, visual, auditory. Stages: script, edit. Style filters: educational.
28. **AVQ-020-028** Does perspective text become unreadable at oblique angles precisely when its information is needed?
   - Failure hypothesis: Scene-integrated typography sacrifices legibility to perspective.
   - Check or fix: Adjust the camera, text plane, or repeat essentials in a readable view.
   - Severity: high. Modes: visual, human-audience. Stages: production, edit. Style filters: 3d, live-action.
29. **AVQ-020-029** Is the visual reading order preserved when text is rearranged for a vertical version?
   - Failure hypothesis: Responsive placement changes the intended argument sequence.
   - Check or fix: Read each format independently and revise its hierarchy.
   - Severity: high. Modes: visual, human-audience. Stages: edit, delivery. Style filters: typographic.
30. **AVQ-020-030** Does a legal or explanatory footnote contradict the prominent message while being too small to notice?
   - Failure hypothesis: Fine print is used to repair an overbroad headline.
   - Check or fix: Correct the main statement and make material limitations directly readable.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, edit. Style filters: educational.
31. **AVQ-020-031** Are important words ever partially hidden by decorative foreground elements during their reading interval?
   - Failure hypothesis: Layer order allows ornament to occlude essential text.
   - Check or fix: Inspect text visibility masks across the entire interval.
   - Severity: high. Modes: machine, visual. Stages: production, edit, final-encode. Style filters: any.
32. **AVQ-020-032** Can the title be shortened without losing the specific promise, leaving more screen space for the actual evidence?
   - Failure hypothesis: Verbose wording consumes the image needed to support the claim.
   - Check or fix: Test a concise title alongside a larger evidence region.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, edit. Style filters: any.
