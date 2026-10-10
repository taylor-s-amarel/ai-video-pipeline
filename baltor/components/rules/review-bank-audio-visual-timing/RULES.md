# Adversarial review bank: D025 audio visual timing (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D025 audio visual timing". The questions below are the
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

- Severity: 21 high, 11 medium.
- Modes: 29 visual, 32 auditory, 20 machine, 14 human-audience.
- Need listening: 32 (none are listening-only).
- Need a human audience: 14.
- Only answerable at final encode or delivery: `AVQ-025-004`, `AVQ-025-012`, `AVQ-025-013`, `AVQ-025-014`, `AVQ-025-027`, `AVQ-025-028`, `AVQ-025-031`.
- Limited by style filter: `AVQ-025-001` (live-action, fiction, 3d, cutout), `AVQ-025-002` (3d, cutout, stop-motion, fiction, live-action), `AVQ-025-003` (fiction), `AVQ-025-006` (educational), `AVQ-025-007` (educational), `AVQ-025-017` (educational, live-action, 3d), `AVQ-025-018` (puzzle), `AVQ-025-019` (educational), `AVQ-025-020` (screen-recording, educational, typographic), `AVQ-025-022` (vector, typographic), `AVQ-025-023` (educational), `AVQ-025-025` (fiction), `AVQ-025-029` (live-action, fiction, 3d).

## Named passes that draw on this area

- `default_32`: `AVQ-025-001`
- `sound`: `AVQ-025-001`, `AVQ-025-002`, `AVQ-025-003`, `AVQ-025-004`, `AVQ-025-005`, `AVQ-025-006`, `AVQ-025-007`, `AVQ-025-008`, `AVQ-025-009`, `AVQ-025-010`, `AVQ-025-011`, `AVQ-025-012`, `AVQ-025-013`, `AVQ-025-014`, `AVQ-025-015`, `AVQ-025-016`
- `longer_cardboard_32`: `AVQ-025-002`

## Questions

1. **AVQ-025-001** Do visible lip closures coincide with the corresponding consonants in the delivered dialogue?
   - Failure hypothesis: Mouth animation uses a nearby but perceptually wrong phoneme timing.
   - Check or fix: Listen with picture and inspect exposed consonants frame by frame.
   - Severity: high. Modes: machine, visual, auditory. Stages: edit, final-encode. Style filters: live-action, fiction, 3d, cutout. Passes: default_32, sound.
2. **AVQ-025-002** Does a footstep sound land on weight-bearing contact rather than on the foot's lowest airborne position?
   - Failure hypothesis: Naive motion markers misidentify the actual contact event.
   - Check or fix: Listen with the walk and align cues to verified contact frames.
   - Severity: high. Modes: machine, visual, auditory. Stages: production, edit, final-encode. Style filters: 3d, cutout, stop-motion, fiction, live-action. Passes: sound, longer_cardboard_32.
3. **AVQ-025-003** Are musical accents aligned to the perceptually important phase of a gesture rather than merely its keyframe timestamp?
   - Failure hypothesis: Technical alignment misses the gesture's experienced peak.
   - Check or fix: Listen at normal speed and compare anticipation, peak, and settle placements.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: fiction. Passes: sound.
4. **AVQ-025-004** Does synchronization drift progressively from the beginning to the end of the video?
   - Failure hypothesis: Audio and picture were interpreted under different clock or rate assumptions.
   - Check or fix: Compare early and late landmarks and listen through the delivered file.
   - Severity: high. Modes: machine, visual, auditory. Stages: final-encode. Style filters: any. Passes: sound.
5. **AVQ-025-005** Is a constant global audio offset shifting every sound ahead of or behind the picture?
   - Failure hypothesis: Container or timeline offset moves the entire soundtrack.
   - Check or fix: Measure several independent landmarks and verify the correction by listening.
   - Severity: high. Modes: machine, visual, auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
6. **AVQ-025-006** When narration says 'this part,' is the intended object already visible and still highlighted?
   - Failure hypothesis: Spoken reference and visual focus occupy different intervals.
   - Check or fix: Listen with picture and align each deictic phrase to its referent.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: script, animatic, edit. Style filters: educational. Passes: sound.
7. **AVQ-025-007** Does a spoken explanation introduce a diagram feature before the feature changes beyond recognition?
   - Failure hypothesis: The image advances while the voice still describes its prior state.
   - Check or fix: Listen with the animation and hold the referenced state through the phrase.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: educational. Passes: sound.
8. **AVQ-025-008** Are deliberate anticipatory sounds clearly nonliteral rather than suggesting an impact before contact?
   - Failure hypothesis: An editorial whoosh is mistaken for a physically early collision.
   - Check or fix: Listen with picture and distinguish anticipation from the contact cue.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: any. Passes: sound.
9. **AVQ-025-009** Does an echo or repeated effect make one visible event seem like two separate actions?
   - Failure hypothesis: Audible repetitions imply extra events absent from the picture.
   - Check or fix: Listen without prior context and simplify ambiguous repeats.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: any. Passes: sound.
10. **AVQ-025-010** Does the audiovisual loop return to the same phase in both music and movement?
   - Failure hypothesis: Unequal loop lengths cause a new phase mismatch on each repeat.
   - Check or fix: Play multiple loops and compare shared start landmarks.
   - Severity: high. Modes: machine, visual, auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
11. **AVQ-025-011** Does speed-ramping footage preserve the intended relationship between source motion and sound duration?
   - Failure hypothesis: Picture retiming leaves effects or dialogue at incompatible speeds.
   - Check or fix: Listen across ramps and retime or replace sound intentionally.
   - Severity: high. Modes: machine, visual, auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
12. **AVQ-025-012** Are sharp audio transients still aligned after video frame-rate conversion quantizes the event time?
   - Failure hypothesis: Conforming rounds visual events but leaves sample-accurate audio unchanged.
   - Check or fix: Inspect converted landmarks and listen to the final cadence.
   - Severity: high. Modes: machine, visual, auditory. Stages: final-encode. Style filters: any. Passes: sound.
13. **AVQ-025-013** Does encoder priming or inserted silence delay the first audible event relative to the first visual action?
   - Failure hypothesis: Codec padding alters the beginning of the delivered clip.
   - Check or fix: Decode and listen from the start in target players.
   - Severity: high. Modes: machine, visual, auditory. Stages: final-encode, delivery. Style filters: any. Passes: sound.
14. **AVQ-025-014** Is the last spoken word or sound decay audible before the encoded picture ends?
   - Failure hypothesis: Mismatched stream durations truncate the soundtrack's conclusion.
   - Check or fix: Listen through the actual endpoint and inspect both stream durations.
   - Severity: high. Modes: machine, auditory. Stages: final-encode. Style filters: any. Passes: sound.
15. **AVQ-025-015** Do separately rendered scene segments share one timeline rather than restarting local audio phase at each join?
   - Failure hypothesis: Segment assembly resets a continuous cue or ambience cycle.
   - Check or fix: Listen across all joins and compare segment offsets to the master timeline.
   - Severity: high. Modes: machine, visual, auditory. Stages: edit, final-encode. Style filters: any. Passes: sound.
16. **AVQ-025-016** Does apparent source motion across the screen agree with audible spatial movement?
   - Failure hypothesis: Pan automation follows the wrong trajectory or direction.
   - Check or fix: Listen with headphones and picture, then align spatial cues to the intended path.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: production, edit, final-encode. Style filters: any. Passes: sound.
17. **AVQ-025-017** Is any intended sound-travel delay plausible and distinguishable from accidental desynchronization?
   - Failure hypothesis: Delayed sound appears broken because distance or scale is not established.
   - Check or fix: Listen with the shot and verify the delay rationale and visual distance cue.
   - Severity: medium. Modes: machine, visual, auditory, human-audience. Stages: animatic, edit. Style filters: educational, live-action, 3d.
18. **AVQ-025-018** Does a countdown's audible pulse indicate the same remaining time as its visible numerals?
   - Failure hypothesis: Timer graphics and audio clicks are driven by separate clocks.
   - Check or fix: Listen while stepping through numeral changes and reconcile the time authority.
   - Severity: high. Modes: machine, visual, auditory. Stages: edit, final-encode. Style filters: puzzle.
19. **AVQ-025-019** Are sound cues for simultaneous comparison panels using the same event definition on both sides?
   - Failure hypothesis: One panel sounds at anticipation while the other sounds at completion.
   - Check or fix: Listen to isolated panels and normalize the cue criterion.
   - Severity: high. Modes: machine, visual, auditory. Stages: animatic, edit. Style filters: educational.
20. **AVQ-025-020** Does an audio-reactive graphic actually derive from the delivered audio rather than a different draft?
   - Failure hypothesis: A plausible waveform or meter displays unrelated signal data.
   - Check or fix: Compare audio features to graphic timing and listen at mismatched peaks.
   - Severity: high. Modes: machine, visual, auditory. Stages: production, final-encode. Style filters: screen-recording, educational, typographic.
21. **AVQ-025-021** Does automatic beat detection identify the pulse listeners actually hear in this cue?
   - Failure hypothesis: An estimator locks onto subdivisions or half-time accents.
   - Check or fix: Listen and tap the pulse, then compare it with detected beats.
   - Severity: medium. Modes: machine, auditory, human-audience. Stages: animatic, edit. Style filters: any.
22. **AVQ-025-022** Are repeated visual accents distributed musically when the beat period is not an integer number of video frames?
   - Failure hypothesis: Naive rounding accumulates jitter or duplicates accent frames.
   - Check or fix: Inspect frame scheduling and listen to the long repeated sequence.
   - Severity: medium. Modes: machine, visual, auditory. Stages: production, final-encode. Style filters: vector, typographic.
23. **AVQ-025-023** Does a frozen image accompanied by continuing action sounds imply an event the viewer can no longer verify?
   - Failure hypothesis: Audio continuation creates false off-screen progress during a freeze.
   - Check or fix: Listen with picture and either justify the off-screen action or change the cue.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: educational.
24. **AVQ-025-024** Does reversing a shot leave sound envelopes that suggest forward action or an impossible sequence?
   - Failure hypothesis: Reversed visuals retain incompatible attack and decay cues.
   - Check or fix: Listen to the reversed sequence and redesign sound for the intended event.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: edit, final-encode. Style filters: any.
25. **AVQ-025-025** Are emotional vocal pauses coordinated with visible reactions instead of overwritten by unrelated movement?
   - Failure hypothesis: The body advances while the voice is still processing the moment.
   - Check or fix: Listen with performance and retime reaction beats around the spoken thought.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: fiction.
26. **AVQ-025-026** Does a visual beat tied to spoken wording still work in a translated or alternate-voice version?
   - Failure hypothesis: Different phrase lengths break an alignment inherited from the original.
   - Check or fix: Listen to every language version with its actual picture timing.
   - Severity: high. Modes: visual, auditory, human-audience. Stages: edit, final-encode, delivery. Style filters: any.
27. **AVQ-025-027** Is the audio track paired with the exact picture revision it was mixed against?
   - Failure hypothesis: A correctly timed soundtrack is attached to a different cut.
   - Check or fix: Verify version hashes and listen at each changed edit boundary.
   - Severity: high. Modes: machine, visual, auditory. Stages: final-encode. Style filters: any.
28. **AVQ-025-028** Does seeking or resuming playback introduce an audiovisual offset that continuous playback does not reveal?
   - Failure hypothesis: Player buffering or timestamps cause transient desynchronization after navigation.
   - Check or fix: Test real seek/resume behavior and listen at recognizable sync events.
   - Severity: high. Modes: machine, visual, auditory. Stages: delivery. Style filters: any.
29. **AVQ-025-029** Are scene ambience changes synchronized with the intended acoustic boundary rather than arbitrary cut points?
   - Failure hypothesis: Sound changes rooms before the character crosses the doorway.
   - Check or fix: Listen with spatial action and place the acoustic transition at the justified moment.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: edit. Style filters: live-action, fiction, 3d.
30. **AVQ-025-030** Does a note or effect trigger twice when a visual event sits on a segment or loop boundary?
   - Failure hypothesis: Inclusive boundary logic schedules the same event in both adjacent blocks.
   - Check or fix: Audit event IDs and listen across the affected boundary.
   - Severity: high. Modes: machine, auditory. Stages: production, final-encode. Style filters: any.
31. **AVQ-025-031** Can the apparent synchronization be verified on the actual destination rather than inferred from an editor preview?
   - Failure hypothesis: Preview playback compensation hides delivery-specific timing problems.
   - Check or fix: Listen and watch the uploaded or delivered rendition on its real player.
   - Severity: high. Modes: machine, visual, auditory. Stages: delivery. Style filters: any.
32. **AVQ-025-032** If a cue is deliberately off-beat, does that mismatch read as expressive timing rather than an error?
   - Failure hypothesis: Intentional displacement is too weakly motivated to be perceived as design.
   - Check or fix: Listen with unbriefed viewers and compare an aligned version.
   - Severity: medium. Modes: visual, auditory, human-audience. Stages: animatic, edit. Style filters: any.
