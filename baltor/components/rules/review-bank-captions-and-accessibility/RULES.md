# Adversarial review bank: D021 captions and accessibility (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D021 captions and accessibility". The questions below are the
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

- Severity: 2 critical, 20 high, 10 medium.
- Modes: 27 visual, 13 auditory, 14 machine, 26 human-audience.
- Need listening: 13 (`AVQ-021-012`, `AVQ-021-022` are listening-only).
- Need a human audience: 26.
- Only answerable at final encode or delivery: `AVQ-021-007`, `AVQ-021-016`, `AVQ-021-018`, `AVQ-021-020`, `AVQ-021-024`, `AVQ-021-030`.
- Limited by style filter: `AVQ-021-003` (live-action, fiction), `AVQ-021-005` (puzzle, fiction), `AVQ-021-009` (live-action, fiction), `AVQ-021-011` (educational), `AVQ-021-013` (educational, puzzle), `AVQ-021-017` (educational), `AVQ-021-019` (fiction), `AVQ-021-020` (educational, screen-recording), `AVQ-021-021` (educational, screen-recording, puzzle), `AVQ-021-022` (educational), `AVQ-021-023` (educational), `AVQ-021-025` (puzzle), `AVQ-021-026` (educational, puzzle), `AVQ-021-028` (fiction), `AVQ-021-031` (educational).

## Named passes that draw on this area

- `default_32`: `AVQ-021-001`
- `accessible_text`: `AVQ-021-001`, `AVQ-021-002`, `AVQ-021-003`, `AVQ-021-004`, `AVQ-021-005`, `AVQ-021-006`, `AVQ-021-007`, `AVQ-021-008`, `AVQ-021-009`, `AVQ-021-010`
- `final_delivery`: `AVQ-021-001`, `AVQ-021-002`, `AVQ-021-003`, `AVQ-021-004`, `AVQ-021-005`, `AVQ-021-006`, `AVQ-021-007`, `AVQ-021-008`
- `longer_cardboard_32`: `AVQ-021-001`

## Questions

1. **AVQ-021-001** Do captions preserve every meaning-changing negation, name, and number in the actual spoken track?
   - Failure hypothesis: Automated transcription drops small words that reverse meaning.
   - Check or fix: Listen to the final track against captions and correct consequential mismatches.
   - Severity: high. Modes: machine, auditory, human-audience. Stages: edit, final-encode. Style filters: any. Passes: default_32, accessible_text, final_delivery, longer_cardboard_32.
2. **AVQ-021-002** Are caption boundaries aligned to complete thought groups rather than arbitrary word counts?
   - Failure hypothesis: Fragmented captions force viewers to reconstruct syntax under time pressure.
   - Check or fix: Re-segment by spoken phrasing and test an uninterrupted read-through.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: edit, final-encode. Style filters: any. Passes: accessible_text, final_delivery.
3. **AVQ-021-003** Can viewers identify an off-screen speaker when the voice alone is not available?
   - Failure hypothesis: Untagged dialogue becomes unattributable with sound off.
   - Check or fix: Add concise speaker identifiers at ambiguous entrances.
   - Severity: high. Modes: visual, human-audience. Stages: edit, final-encode. Style filters: live-action, fiction. Passes: accessible_text, final_delivery.
4. **AVQ-021-004** Are story-relevant sounds described when no visible action conveys them?
   - Failure hypothesis: A silent viewer misses an unseen alarm, knock, or approach.
   - Check or fix: Listen for consequential sounds and add concise non-speech captions.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: edit, final-encode. Style filters: any. Passes: accessible_text, final_delivery.
5. **AVQ-021-005** Do captions reveal the answer or punchline before the corresponding performance delivers it?
   - Failure hypothesis: Early cue display spoils suspense or puzzle fairness.
   - Check or fix: Shift cue boundaries so essential reveal words arrive at their intended moment.
   - Severity: high. Modes: machine, visual, human-audience. Stages: edit, final-encode. Style filters: puzzle, fiction. Passes: accessible_text, final_delivery.
6. **AVQ-021-006** Do captions cover faces, hands, demonstrations, or puzzle targets at any moment?
   - Failure hypothesis: A fixed caption region obstructs essential visual evidence.
   - Check or fix: Review full-length overlay playback and relocate captions at conflicts.
   - Severity: high. Modes: machine, visual. Stages: edit, final-encode. Style filters: any. Passes: accessible_text, final_delivery.
7. **AVQ-021-007** Are captions still present and correctly timed after the final trim, speed change, or inserted slate?
   - Failure hypothesis: Subtitle timestamps belong to an earlier edit.
   - Check or fix: Validate the caption track against the exact delivered file.
   - Severity: high. Modes: machine, visual, auditory. Stages: final-encode, delivery. Style filters: any. Passes: accessible_text, final_delivery.
8. **AVQ-021-008** Does the caption display duration allow the intended audience to read the longest cue comfortably?
   - Failure hypothesis: Nominal caption presence conceals unreadably fast exposure.
   - Check or fix: Test long cues with target readers and split or extend them.
   - Severity: high. Modes: machine, visual, human-audience. Stages: edit, final-encode. Style filters: any. Passes: accessible_text, final_delivery.
9. **AVQ-021-009** Are overlapping voices represented without implying an order that was not spoken?
   - Failure hypothesis: Captions serialize simultaneous speech into a false exchange.
   - Check or fix: Listen to overlap passages and use clear multi-speaker formatting.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: edit, final-encode. Style filters: live-action, fiction. Passes: accessible_text.
10. **AVQ-021-010** Do automatic captions invent speech during silence, music, or unintelligible audio?
   - Failure hypothesis: Recognition output hallucinates dialogue where none is recoverable.
   - Check or fix: Listen to low-confidence sections and remove unsupported text.
   - Severity: high. Modes: machine, auditory. Stages: edit, final-encode. Style filters: any. Passes: accessible_text.
11. **AVQ-021-011** Can a viewer understand the essential argument with sound muted, including any instruction delivered only by voice?
   - Failure hypothesis: Captions omit or summarize away necessary spoken reasoning.
   - Check or fix: Watch the actual muted delivery and attempt the stated viewer task.
   - Severity: high. Modes: visual, human-audience. Stages: edit, final-encode, delivery. Style filters: educational.
12. **AVQ-021-012** Is the audio description conveying crucial visual changes during gaps without competing with dialogue?
   - Failure hypothesis: Description either omits essential action or masks existing speech.
   - Check or fix: Listen to a description mix with blind or low-vision reviewers when available.
   - Severity: high. Modes: auditory, human-audience. Stages: edit, delivery. Style filters: any.
13. **AVQ-021-013** Do instructions rely on color alone, such as 'follow the red line,' without a second identifier?
   - Failure hypothesis: Viewers cannot identify the referent without the intended color distinction.
   - Check or fix: Add position, pattern, or explicit labels to color-based references.
   - Severity: high. Modes: visual, human-audience. Stages: script, storyboard, edit. Style filters: educational, puzzle.
14. **AVQ-021-014** Does rapid flashing or a strong alternating pattern require a qualified photosensitivity review before release?
   - Failure hypothesis: Visually intense effects may pose a hazard missed by aesthetic review.
   - Check or fix: Run an appropriate flash analysis and review flagged intervals before approval.
   - Severity: critical. Modes: machine, visual. Stages: edit, final-encode, delivery. Style filters: any.
15. **AVQ-021-015** Can prolonged camera sway, rapid zooms, or full-field rotation be reduced without losing the explanation?
   - Failure hypothesis: Unnecessary global motion creates avoidable discomfort.
   - Check or fix: Review motion-heavy intervals with sensitive viewers and test a calmer version.
   - Severity: high. Modes: visual, human-audience. Stages: animatic, edit. Style filters: any.
16. **AVQ-021-016** Are essential captions supplied as usable text tracks when the delivery context needs viewer control or search?
   - Failure hypothesis: Burned-in text alone blocks selectable language or caption preferences.
   - Check or fix: Deliver verified sidecar or embedded tracks supported by the destination.
   - Severity: medium. Modes: machine, visual. Stages: final-encode, delivery. Style filters: any.
17. **AVQ-021-017** Do translated captions preserve technical meaning rather than mirror source-language word order?
   - Failure hypothesis: Literal translation distorts a key relation or instruction.
   - Check or fix: Have a fluent domain-capable reader review the actual rendered translation.
   - Severity: high. Modes: visual, human-audience. Stages: edit, final-encode. Style filters: educational.
18. **AVQ-021-018** Is the caption track labeled with the correct language and accessibility purpose?
   - Failure hypothesis: Incorrect metadata makes viewers choose an unsuitable track.
   - Check or fix: Inspect track labels in the actual delivery player.
   - Severity: medium. Modes: machine, visual. Stages: final-encode, delivery. Style filters: any.
19. **AVQ-021-019** Are meaningful changes in tone, such as sarcasm or whispering, recoverable when they affect the story?
   - Failure hypothesis: Literal words conceal the intended social meaning.
   - Check or fix: Add restrained delivery cues only where the plot depends on them.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: edit, final-encode. Style filters: fiction.
20. **AVQ-021-020** Can viewers pause on a dense diagram without its labels or controls disappearing?
   - Failure hypothesis: Essential information depends on transient UI or animated states.
   - Check or fix: Test pause and seek behavior at the densest explanatory frame.
   - Severity: medium. Modes: machine, visual, human-audience. Stages: final-encode, delivery. Style filters: educational, screen-recording.
21. **AVQ-021-021** Are visual indications of success and failure distinguishable without an audio cue?
   - Failure hypothesis: Feedback meaning is available only through a chime or buzzer.
   - Check or fix: Add clearly different visual outcomes and test muted playback.
   - Severity: high. Modes: visual, human-audience. Stages: animatic, edit. Style filters: educational, screen-recording, puzzle.
22. **AVQ-021-022** Does narration describe a spatial relation precisely enough for a listener who cannot inspect the diagram?
   - Failure hypothesis: Phrases such as 'over here' have no nonvisual referent.
   - Check or fix: Replace deictic wording with meaningful spatial or structural descriptions.
   - Severity: high. Modes: auditory, human-audience. Stages: script, edit. Style filters: educational.
23. **AVQ-021-023** Can viewers with less topic vocabulary follow the caption terminology without pausing for definitions?
   - Failure hypothesis: Unexplained jargon creates an access barrier unrelated to the lesson.
   - Check or fix: Define necessary terms at first use and test with intended novices.
   - Severity: medium. Modes: visual, human-audience. Stages: script, storyboard, edit. Style filters: educational.
24. **AVQ-021-024** Do caption italics, positioning, or color conventions remain understandable when the player ignores their styling?
   - Failure hypothesis: Semantic distinctions depend on formatting the player may discard.
   - Check or fix: Test a plain-text fallback and add textual identifiers where necessary.
   - Severity: medium. Modes: machine, visual, human-audience. Stages: final-encode, delivery. Style filters: any.
25. **AVQ-021-025** Is a visible countdown accessible to someone relying on audio or captions without overwhelming the task?
   - Failure hypothesis: Remaining response time is communicated in only one sensory channel.
   - Check or fix: Provide a restrained redundant time cue and test task completion.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: animatic, edit, final-encode. Style filters: puzzle.
26. **AVQ-021-026** Are instructions given before an irreversible visual event rather than only while it is happening?
   - Failure hypothesis: Slower readers receive the rule after the opportunity to use it.
   - Check or fix: Move the instruction earlier and separate it from execution.
   - Severity: high. Modes: machine, visual, human-audience. Stages: script, animatic, edit. Style filters: educational, puzzle.
27. **AVQ-021-027** Does a picture-in-picture sign-language window remain large enough and unobstructed for its intended viewers?
   - Failure hypothesis: The access layer is reduced or cropped until signing details are unreadable.
   - Check or fix: Review final-size playback with a qualified signer.
   - Severity: high. Modes: visual, human-audience. Stages: edit, final-encode, delivery. Style filters: any.
28. **AVQ-021-028** Are lyrics that carry narrative information captioned distinctly from spoken dialogue?
   - Failure hypothesis: Sung words disappear from access tracks or are mistaken for speech.
   - Check or fix: Listen to relevant lyrics and include accurate, clearly identified cues.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: edit, final-encode. Style filters: fiction.
29. **AVQ-021-029** Does dense simultaneous motion, captioning, and sound make the central task harder for sensory-sensitive viewers?
   - Failure hypothesis: Multiple salience peaks compete without a clear priority.
   - Check or fix: Remove nonessential stimulation and compare task performance.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: any.
30. **AVQ-021-030** Are accessibility claims limited to checks actually performed on the delivered version?
   - Failure hypothesis: A caption file is treated as proof of comprehensive accessibility.
   - Check or fix: List completed checks, reviewer scope, and untested needs explicitly.
   - Severity: high. Modes: machine, human-audience. Stages: final-encode, delivery. Style filters: any.
31. **AVQ-021-031** Does an emergency or safety instruction retain its full meaning across captions, narration, and visual symbols?
   - Failure hypothesis: One access channel drops a condition that makes the advice safe.
   - Check or fix: Reconcile all channels against the verified instruction before release.
   - Severity: critical. Modes: machine, visual, auditory, human-audience. Stages: script, edit, final-encode. Style filters: educational.
32. **AVQ-021-032** Can a transcript substitute preserve references to important figures, sounds, and actions rather than just dialogue?
   - Failure hypothesis: A dialogue-only transcript loses the evidence used by the film.
   - Check or fix: Include concise descriptions at the relevant points and test independent reading.
   - Severity: medium. Modes: visual, human-audience. Stages: edit, delivery. Style filters: any.
