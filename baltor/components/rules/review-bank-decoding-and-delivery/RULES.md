# Adversarial review bank: D029 decoding and delivery (32 questions)

This is the owner's authoritative adversarial review bank: the 1,024 questions of Appendix E of the Animation and Video Production Master Guide (10 Oct 2026), transcribed with the owner's exact text, ids, filters and pass membership. Another builder in this catalogue (harness_kit) independently wrote a different 1,024-question bank; it is not this set and does not override it.

Source: Animation and Video Production Master Guide (10 Oct 2026), Appendix E, section "D029 decoding and delivery". The questions below are the
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

- Severity: 1 critical, 23 high, 8 medium.
- Modes: 17 visual, 3 auditory, 29 machine, 9 human-audience.
- Need listening: 3 (`AVQ-029-030` are listening-only).
- Need a human audience: 9.
- Only answerable at final encode or delivery: `AVQ-029-001`, `AVQ-029-002`, `AVQ-029-003`, `AVQ-029-004`, `AVQ-029-005`, `AVQ-029-006`, `AVQ-029-007`, `AVQ-029-008`, `AVQ-029-009`, `AVQ-029-010`, `AVQ-029-011`, `AVQ-029-012`, `AVQ-029-013`, `AVQ-029-014`, `AVQ-029-015`, `AVQ-029-016`, `AVQ-029-017`, `AVQ-029-018`, `AVQ-029-019`, `AVQ-029-020`, `AVQ-029-021`, `AVQ-029-022`, `AVQ-029-023`, `AVQ-029-024`, `AVQ-029-025`, `AVQ-029-026`, `AVQ-029-027`, `AVQ-029-028`, `AVQ-029-029`, `AVQ-029-030`, `AVQ-029-031`, `AVQ-029-032`.
- Limited by style filter: `AVQ-029-007` (educational, puzzle), `AVQ-029-010` (puzzle, fiction).

## Named passes that draw on this area

- `default_32`: `AVQ-029-001`
- `accessible_text`: `AVQ-029-001`, `AVQ-029-002`, `AVQ-029-003`, `AVQ-029-004`, `AVQ-029-005`, `AVQ-029-006`, `AVQ-029-007`, `AVQ-029-008`, `AVQ-029-009`, `AVQ-029-010`
- `final_delivery`: `AVQ-029-001`, `AVQ-029-002`, `AVQ-029-003`, `AVQ-029-004`, `AVQ-029-005`, `AVQ-029-006`, `AVQ-029-007`, `AVQ-029-008`

## Questions

1. **AVQ-029-001** Does the delivered filename's extension agree with the actual media container and streams?
   - Failure hypothesis: A renamed file is mistaken for a valid export in the promised format.
   - Check or fix: Inspect file signatures and stream metadata rather than trusting the name.
   - Severity: high. Modes: machine. Stages: final-encode, delivery. Style filters: any. Passes: default_32, accessible_text, final_delivery.
2. **AVQ-029-002** Are the downloaded bytes identical to the approved deliverable when no destination transcoding is intended?
   - Failure hypothesis: Transfer or packaging corruption changes the approved file.
   - Check or fix: Compare cryptographic hashes before and after the real download path.
   - Severity: high. Modes: machine. Stages: delivery. Style filters: any. Passes: accessible_text, final_delivery.
3. **AVQ-029-003** Can the complete delivered file be decoded without errors, including its final frames?
   - Failure hypothesis: Header inspection misses corruption late in the media stream.
   - Check or fix: Run a full decode and review every reported error.
   - Severity: high. Modes: machine. Stages: final-encode, delivery. Style filters: any. Passes: accessible_text, final_delivery.
4. **AVQ-029-004** Does the exact codec profile and level play on the lowest supported device?
   - Failure hypothesis: General codec support is mistaken for support of every profile and resolution.
   - Check or fix: Test the delivered file on the stated minimum device/player.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any. Passes: accessible_text, final_delivery.
5. **AVQ-029-005** Is hardware acceleration required for smooth playback on the intended audience's devices?
   - Failure hypothesis: A demanding encode stutters on realistic decoding hardware.
   - Check or fix: Measure dropped frames and responsiveness on representative devices.
   - Severity: high. Modes: machine, visual, human-audience. Stages: delivery. Style filters: any. Passes: accessible_text, final_delivery.
6. **AVQ-029-006** Can progressive playback begin promptly without downloading the entire file first?
   - Failure hypothesis: Container layout delays access to essential playback metadata.
   - Check or fix: Test a fresh download over the expected connection and inspect startup behavior.
   - Severity: medium. Modes: machine. Stages: delivery. Style filters: any. Passes: accessible_text, final_delivery.
7. **AVQ-029-007** Does the video remain useful under the destination's lowest likely adaptive rendition?
   - Failure hypothesis: Automatic quality reduction erases critical text or puzzle details.
   - Check or fix: Inspect the actual low-bitrate rendition using the viewer's task.
   - Severity: high. Modes: machine, visual, human-audience. Stages: delivery. Style filters: educational, puzzle. Passes: accessible_text, final_delivery.
8. **AVQ-029-008** Does constrained bandwidth cause stalls precisely during the solving or decision interval?
   - Failure hypothesis: Buffer interruptions alter the intended experience and available response time.
   - Check or fix: Test realistic constrained playback and provide a suitable download option if needed.
   - Severity: medium. Modes: machine, visual, human-audience. Stages: delivery. Style filters: any. Passes: accessible_text, final_delivery.
9. **AVQ-029-009** Are rotation and display-orientation flags interpreted consistently by target players?
   - Failure hypothesis: Different players rotate or letterbox the same pixels differently.
   - Check or fix: Compare the file on the supported player set.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any. Passes: accessible_text.
10. **AVQ-029-010** Does the selected thumbnail reveal a puzzle answer or narrative surprise before playback?
   - Failure hypothesis: Automatically chosen preview imagery spoils the experience.
   - Check or fix: Review the actual destination thumbnail and select an appropriate authorized replacement.
   - Severity: high. Modes: visual, human-audience. Stages: delivery. Style filters: puzzle, fiction. Passes: accessible_text.
11. **AVQ-029-011** Is the intended audio track selected by default rather than commentary, a stem, or another language?
   - Failure hypothesis: Track ordering or metadata causes the wrong listening experience.
   - Check or fix: Open the final file fresh in target players and listen to the default track.
   - Severity: high. Modes: machine, auditory. Stages: delivery. Style filters: any.
12. **AVQ-029-012** Does muted autoplay still make the opening intelligible enough for the viewer to choose whether to continue?
   - Failure hypothesis: The initial experience depends on audio the platform suppresses.
   - Check or fix: Test actual muted autoplay and make the opening promise visible.
   - Severity: medium. Modes: visual, human-audience. Stages: delivery. Style filters: any.
13. **AVQ-029-013** Are caption sidecars actually linked and available to the recipient rather than merely sitting beside the source file?
   - Failure hypothesis: Captions exist in storage but are absent from the delivery player.
   - Check or fix: Open the recipient-facing player and enable the supplied captions.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any.
14. **AVQ-029-014** Does switching language tracks select a matching caption track where the player supports that behavior?
   - Failure hypothesis: Independent track defaults produce mismatched spoken and written languages.
   - Check or fix: Test the available language combinations explicitly.
   - Severity: medium. Modes: machine, visual, auditory. Stages: delivery. Style filters: any.
15. **AVQ-029-015** Has destination transcoding finished before the video is described as ready for review?
   - Failure hypothesis: A placeholder or incomplete low-quality rendition is mistaken for final delivery.
   - Check or fix: Verify processing completion and inspect the resulting rendition.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any.
16. **AVQ-029-016** Does playback reach the intended ending rather than stop early at a bad duration or timestamp boundary?
   - Failure hypothesis: Container timing makes a valid tail inaccessible to the player.
   - Check or fix: Play through the end and compare visible duration with decoded content.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any.
17. **AVQ-029-017** Can a viewer seek to a critical explanation without waiting excessively or landing on corrupted frames?
   - Failure hypothesis: Sparse or malformed random-access points impair navigation.
   - Check or fix: Seek repeatedly around key sections on target players.
   - Severity: medium. Modes: machine, visual. Stages: delivery. Style filters: any.
18. **AVQ-029-018** Does loop playback include an unintended pause, black flash, or duplicate frame imposed by the destination player?
   - Failure hypothesis: Local seamlessness is broken by destination loop behavior.
   - Check or fix: Observe multiple actual destination loops and adjust delivery if possible.
   - Severity: medium. Modes: machine, visual. Stages: delivery. Style filters: any.
19. **AVQ-029-019** Do player controls or captions supplied by the destination cover evidence placed near the frame edge?
   - Failure hypothesis: Delivery UI obscures content that was safe in the clean export.
   - Check or fix: Inspect the real player with controls and captions visible.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any.
20. **AVQ-029-020** Does automatic platform cropping preserve the intended composition in every supported presentation slot?
   - Failure hypothesis: Feed, preview, or full-screen modes use different crops.
   - Check or fix: Test each actual slot and prepare separately reviewed variants where needed.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any.
21. **AVQ-029-021** Are the file's access settings limited to the audience the user authorized?
   - Failure hypothesis: Delivery convenience accidentally makes a private film publicly reachable.
   - Check or fix: Inspect sharing scope before sending and verify the intended recipient view.
   - Severity: critical. Modes: machine, human-audience. Stages: delivery. Style filters: any.
22. **AVQ-029-022** Can the intended recipient open the delivered attachment or link with their actual permissions?
   - Failure hypothesis: Owner access is mistaken for recipient access.
   - Check or fix: Verify recipient access without broadening permissions beyond authorization.
   - Severity: high. Modes: machine. Stages: delivery. Style filters: any.
23. **AVQ-029-023** Will the access link remain valid for the expected review period?
   - Failure hypothesis: An expiring transfer fails before reviewers can use it.
   - Check or fix: Check expiry against the agreed review window and choose a suitable authorized route.
   - Severity: high. Modes: machine. Stages: delivery. Style filters: any.
24. **AVQ-029-024** Does destination caching continue serving an older rendition after the approved file has been replaced?
   - Failure hypothesis: A cached media response defeats an otherwise correct version update.
   - Check or fix: Compare fresh-session playback and downloaded rendition identity with the approved replacement.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any.
25. **AVQ-029-025** Does the media metadata expose unintended location, personal names, internal paths, or production notes?
   - Failure hypothesis: Hidden metadata leaks information absent from the visible film.
   - Check or fix: Audit metadata and remove unnecessary private fields from the delivery copy.
   - Severity: high. Modes: machine. Stages: final-encode, delivery. Style filters: any.
26. **AVQ-029-026** Is a compatibility fallback the same approved revision as the primary file?
   - Failure hypothesis: A playable alternate silently delivers an older story or fact.
   - Check or fix: Compare version manifests and content landmarks across all variants.
   - Severity: high. Modes: machine, visual. Stages: delivery. Style filters: any.
27. **AVQ-029-027** Is the playable film clearly separated from source archives so the recipient does not have to unpack a project to watch it?
   - Failure hypothesis: Packaging makes a technically complete delivery unusable for its audience.
   - Check or fix: Provide a clearly identified playback file alongside any approved source package.
   - Severity: medium. Modes: machine, human-audience. Stages: delivery. Style filters: any.
28. **AVQ-029-028** Are the delivery instructions naming a genuinely available file rather than a private build path?
   - Failure hypothesis: The handoff points to storage the recipient cannot reach.
   - Check or fix: Follow every recipient-facing link or attachment path from the recipient context.
   - Severity: high. Modes: machine. Stages: delivery. Style filters: any.
29. **AVQ-029-029** Does an embedded player require third-party cookies or an account that the intended audience may not have?
   - Failure hypothesis: Authentication or browser privacy constraints block otherwise valid media.
   - Check or fix: Test the expected signed-out or restricted-browser context.
   - Severity: high. Modes: machine. Stages: delivery. Style filters: any.
30. **AVQ-029-030** Does the destination recompress audio in a way that introduces artifacts or changes speech intelligibility?
   - Failure hypothesis: Source audio review does not cover the platform's actual rendition.
   - Check or fix: Listen to the processed destination audio on representative devices.
   - Severity: high. Modes: auditory, human-audience. Stages: delivery. Style filters: any.
31. **AVQ-029-031** Are review comments attached to an immutable version so later replacement cannot change what was approved?
   - Failure hypothesis: A moving link makes prior feedback and signoff ambiguous.
   - Check or fix: Preserve version IDs or hashes in the review record.
   - Severity: high. Modes: machine. Stages: delivery. Style filters: any.
32. **AVQ-029-032** Can a recipient tell which file is the final intended version when several drafts or aspect ratios are present?
   - Failure hypothesis: Ambiguous naming leads to review or distribution of the wrong asset.
   - Check or fix: Use a clear manifest identifying status, purpose, and approved version.
   - Severity: medium. Modes: machine, human-audience. Stages: delivery. Style filters: any.
