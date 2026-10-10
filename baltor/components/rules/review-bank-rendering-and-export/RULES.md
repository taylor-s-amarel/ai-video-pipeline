# Adversarial review bank: D028 rendering and export (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D028 rendering and export". The questions below are the
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

- Severity: 30 high, 2 medium.
- Modes: 28 visual, 2 auditory, 31 machine, 6 human-audience.
- Need listening: 2 (none are listening-only).
- Need a human audience: 6.
- Only answerable at final encode or delivery: `AVQ-028-004`, `AVQ-028-008`, `AVQ-028-009`, `AVQ-028-018`, `AVQ-028-021`, `AVQ-028-022`, `AVQ-028-023`, `AVQ-028-024`, `AVQ-028-025`, `AVQ-028-026`, `AVQ-028-027`, `AVQ-028-028`, `AVQ-028-029`, `AVQ-028-031`, `AVQ-028-032`.
- Limited by style filter: `AVQ-028-008` (educational, puzzle), `AVQ-028-010` (cutout, vector, 3d), `AVQ-028-011` (educational, puzzle), `AVQ-028-012` (3d, live-action), `AVQ-028-013` (3d), `AVQ-028-014` (vector, 3d, live-action), `AVQ-028-016` (3d), `AVQ-028-017` (3d, cutout), `AVQ-028-019` (vector, typographic, 3d), `AVQ-028-020` (3d, live-action), `AVQ-028-027` (educational, puzzle).

## Named passes that draw on this area

- `default_32`: `AVQ-028-001`
- `final_delivery`: `AVQ-028-001`, `AVQ-028-002`, `AVQ-028-003`, `AVQ-028-004`, `AVQ-028-005`, `AVQ-028-006`, `AVQ-028-007`, `AVQ-028-008`

## Questions

1. **AVQ-028-001** Does the final render contain every intended frame exactly once and in the correct order?
   - Failure hypothesis: Batch rendering omits, duplicates, or misorders frames.
   - Check or fix: Compare the frame sequence against the expected index manifest.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: any. Passes: default_32, final_delivery.
2. **AVQ-028-002** Are nominally adjacent render chunks evaluating animation at the same shared time authority?
   - Failure hypothesis: Local chunk clocks create motion jumps at boundaries.
   - Check or fix: Render boundary overlaps and compare identical-time frames.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: any. Passes: final_delivery.
3. **AVQ-028-003** Is the export using final-resolution assets rather than proxies or preview caches?
   - Failure hypothesis: Low-resolution working material survives a successful render.
   - Check or fix: Audit resolved asset paths and inspect final-scale texture/detail crops.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: any. Passes: final_delivery.
4. **AVQ-028-004** Do the output dimensions and pixel aspect ratio produce the intended display geometry?
   - Failure hypothesis: Correct pixel counts still yield stretched or squeezed playback.
   - Check or fix: Inspect sample/display aspect metadata and compare a known geometric reference.
   - Severity: high. Modes: machine, visual. Stages: final-encode. Style filters: any. Passes: final_delivery.
5. **AVQ-028-005** Is the chosen crop preserving every required subject and label throughout the full camera move?
   - Failure hypothesis: Static framing checks miss content lost at movement extremes.
   - Check or fix: Scan the delivered frame bounds against protected regions over time.
   - Severity: high. Modes: machine, visual. Stages: edit, final-encode. Style filters: any. Passes: final_delivery.
6. **AVQ-028-006** Does the color-management path apply the display transform exactly once?
   - Failure hypothesis: Missing or doubled transforms alter contrast and color.
   - Check or fix: Trace source, working, and output transforms and compare reference patches.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: any. Passes: final_delivery.
7. **AVQ-028-007** Are HDR sources and SDR output being mapped without losing important highlight or shadow information?
   - Failure hypothesis: Automatic tone mapping hides detail or changes intended hierarchy.
   - Check or fix: Inspect controlled reference scenes through the actual output transform.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: any. Passes: final_delivery.
8. **AVQ-028-008** Do saturated colors survive output conversion without clipping away distinctions needed for the task?
   - Failure hypothesis: Gamut conversion merges separate color categories.
   - Check or fix: Compare important color regions before and after export conversion.
   - Severity: high. Modes: machine, visual, human-audience. Stages: final-encode. Style filters: educational, puzzle. Passes: final_delivery.
9. **AVQ-028-009** Does limited bit depth introduce visible banding in gradients that were smooth in the working render?
   - Failure hypothesis: Quantization creates contour steps after export.
   - Check or fix: Inspect final encoded gradients at ordinary and stressed viewing conditions.
   - Severity: medium. Modes: machine, visual. Stages: final-encode. Style filters: any.
10. **AVQ-028-010** Are transparent edges composited with the correct premultiplied or straight-alpha interpretation?
   - Failure hypothesis: Alpha mismatch creates dark or bright halos around cutouts.
   - Check or fix: Composite edge tests over light and dark backgrounds.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: cutout, vector, 3d.
11. **AVQ-028-011** Does motion blur erase a puzzle target, contact event, or technical detail needed to verify the action?
   - Failure hypothesis: A cinematic shutter setting destroys required evidence.
   - Check or fix: Review the decisive frames and lower blur selectively where needed.
   - Severity: high. Modes: machine, visual, human-audience. Stages: production, final-encode. Style filters: educational, puzzle.
12. **AVQ-028-012** Are temporal denoising or upscaling leaving ghost trails around moving silhouettes?
   - Failure hypothesis: History-based processing blends incompatible object positions.
   - Check or fix: Inspect moving edges across consecutive final frames.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: 3d, live-action.
13. **AVQ-028-013** Does the sample count support stable shadows and reflections rather than flickering noise?
   - Failure hypothesis: Undersampling turns static surface appearance into distracting temporal variation.
   - Check or fix: Render a short motion test at candidate settings and compare stability.
   - Severity: medium. Modes: machine, visual. Stages: production, final-encode. Style filters: 3d.
14. **AVQ-028-014** Are fine patterns and linework stable under motion after rasterization?
   - Failure hypothesis: Spatial detail exceeds the sampling rate and produces shimmer or moire.
   - Check or fix: Inspect full-speed output and adjust filtering or detail frequency.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: vector, 3d, live-action.
15. **AVQ-028-015** Does frame interpolation invent malformed intermediate geometry or duplicate a decisive event?
   - Failure hypothesis: Synthetic in-between frames distort the action.
   - Check or fix: Inspect interpolated intervals around occlusions and contact.
   - Severity: high. Modes: machine, visual. Stages: edit, final-encode. Style filters: any.
16. **AVQ-028-016** Are cached simulations and rendered layers from the same approved scene revision?
   - Failure hypothesis: Stale caches combine old motion with new geometry or timing.
   - Check or fix: Reconcile cache hashes and invalidate mismatched dependencies.
   - Severity: high. Modes: machine. Stages: production, final-encode. Style filters: 3d.
17. **AVQ-028-017** Are all required render passes actually included in the final composite?
   - Failure hypothesis: A successful beauty export omits masks, shadows, or corrective passes.
   - Check or fix: Compare the pass manifest to the compositing graph and final image.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: 3d, cutout.
18. **AVQ-028-018** Does the export accidentally include guides, bounding boxes, debug text, or temporary watermarks?
   - Failure hypothesis: Review overlays remain enabled in the delivery render.
   - Check or fix: Scan the full encoded file for nonfinal layers and markers.
   - Severity: high. Modes: machine, visual. Stages: final-encode. Style filters: any.
19. **AVQ-028-019** Are procedural expressions and animated effects evaluated correctly by the final renderer rather than only the editor?
   - Failure hypothesis: The export path silently drops unsupported runtime behavior.
   - Check or fix: Compare representative editor and final-render frames at effect extremes.
   - Severity: high. Modes: machine, visual. Stages: production, final-encode. Style filters: vector, typographic, 3d.
20. **AVQ-028-020** Does final depth of field keep necessary labels, clues, and causal contacts identifiable?
   - Failure hypothesis: Preview sharpness differs from the final camera's focus treatment.
   - Check or fix: Inspect final focus at each required observation interval.
   - Severity: high. Modes: machine, visual, human-audience. Stages: production, final-encode. Style filters: 3d, live-action.
21. **AVQ-028-021** Is the export frame rate the approved rate rather than a default inherited from another project?
   - Failure hypothesis: A preset silently changes duration or motion cadence.
   - Check or fix: Verify nominal and actual frame timestamps against the project contract.
   - Severity: high. Modes: machine. Stages: final-encode. Style filters: any.
22. **AVQ-028-022** Does the render range include the intended final resolved pose without appending an accidental blank or repeated frame?
   - Failure hypothesis: Inclusive/exclusive endpoint confusion damages the ending.
   - Check or fix: Compare requested frame range with decoded first and last frames.
   - Severity: high. Modes: machine, visual. Stages: final-encode. Style filters: any.
23. **AVQ-028-023** Are color-range flags consistent with the actual encoded signal levels?
   - Failure hypothesis: Full/limited-range mismatch produces washed-out or crushed output.
   - Check or fix: Decode with verified interpretation and inspect reference levels.
   - Severity: high. Modes: machine, visual. Stages: final-encode. Style filters: any.
24. **AVQ-028-024** Is the pixel format supported by the intended playback route while retaining required visual detail?
   - Failure hypothesis: A technically valid export is unsuitable for destination decoding or chroma detail.
   - Check or fix: Test the exact format in destination players and inspect critical edges.
   - Severity: high. Modes: machine, visual. Stages: final-encode, delivery. Style filters: any.
25. **AVQ-028-025** Do subtitles, graphics, and audio belong to the same language and revision in a batch export?
   - Failure hypothesis: Reused batch variables combine incompatible version components.
   - Check or fix: Verify each package against its language/revision manifest.
   - Severity: high. Modes: machine, visual, auditory. Stages: final-encode. Style filters: any.
26. **AVQ-028-026** Does the final duration satisfy the requested range without padded silence or black frames?
   - Failure hypothesis: A duration target is met by filler instead of a coherent edit.
   - Check or fix: Measure runtime and review the opening and closing content intervals.
   - Severity: high. Modes: machine, visual, auditory, human-audience. Stages: final-encode. Style filters: any.
27. **AVQ-028-027** Can high-compression output still preserve the smallest essential target and distinction?
   - Failure hypothesis: File-size optimization defeats the video's core viewing task.
   - Check or fix: Compare candidate encodes at intended viewing size using the actual task.
   - Severity: high. Modes: machine, visual, human-audience. Stages: final-encode. Style filters: educational, puzzle.
28. **AVQ-028-028** Does export metadata accidentally mark the file as rotated, stereoscopic, or panoramic when it is ordinary flat video?
   - Failure hypothesis: Inherited metadata causes unintended player transformations.
   - Check or fix: Inspect relevant flags and verify plain playback geometry.
   - Severity: high. Modes: machine, visual. Stages: final-encode, delivery. Style filters: any.
29. **AVQ-028-029** Is the encoded file truly generated from the reviewed source rather than an older render with a new filename?
   - Failure hypothesis: Renaming conceals stale content while appearing current.
   - Check or fix: Verify source/render hashes and compare changed landmarks.
   - Severity: high. Modes: machine, visual. Stages: final-encode. Style filters: any.
30. **AVQ-028-030** Are separate render jobs contaminating one another through shared temporary files or output paths?
   - Failure hypothesis: Concurrent jobs overwrite assets or frames silently.
   - Check or fix: Use isolated job directories and reconcile per-job output hashes.
   - Severity: high. Modes: machine. Stages: production, final-encode. Style filters: any.
31. **AVQ-028-031** Does an interrupted export leave a partial file that could be mistaken for a complete deliverable?
   - Failure hypothesis: File existence is treated as render success.
   - Check or fix: Require successful completion plus full decode and duration validation.
   - Severity: high. Modes: machine. Stages: final-encode. Style filters: any.
32. **AVQ-028-032** Are final-render quality claims supported by viewing the whole encoded result rather than selected attractive stills?
   - Failure hypothesis: Still-frame inspection misses motion, transition, and temporal defects.
   - Check or fix: Watch the full delivered encode and record timecoded findings.
   - Severity: high. Modes: visual, human-audience. Stages: final-encode. Style filters: any.
