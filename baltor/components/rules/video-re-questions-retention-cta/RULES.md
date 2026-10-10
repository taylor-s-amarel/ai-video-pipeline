# Video RE question bank: Retention devices and calls to action

Lens `retention_cta` · 30 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-retention-cta` subagent and challenged by `video-re-challenger`.

Finds the devices that keep viewers watching (open loops, countdowns, re-hooks, pattern interrupts) and the call to action, with placement as ratios of runtime.

## Rules for every answer

1. Boundary: The swarm lifts technique and structure only. Never store, transcribe or reuse the source's footage, frames, music, voice or script text. Keyframes and spectrograms are temporary analysis files in a scratch directory and are never copied into the format IR or a variant. On-screen text may be quoted only as a locating note in evidence.note, at most 6 words, and narration is never quoted. Patterns replace content words with slots, e.g. 'FACT {n}' or '{number} {unit} {noun}'. Analysing a public video for technique is fine; republishing its content is not.
2. Do not identify, name or describe people (identity, age, gender, ethnicity, accent origin); describe size, position, pitch register and delivery only.
3. Never name the source's music track, artist, creator, channel or series in an answer.
4. Cite evidence for every answer: method, confidence, the timestamps you used, the tool or recipe for measured values, and a note with the numbers behind the answer (at most 400 characters).
5. Shape the answer by its answer type and write it to the question's ir_path exactly as given.
6. Say 'not determinable' instead of guessing. A missing measurement is null with an errors[] entry in evidence.json, never zero.
7. State observations, not taste: 'engaging' or 'cinematic' is not an answer; the measurement behind it is. Effects on viewers (retention, virality) are not observable from one video.
8. A claim about every item, shot or caption needs at least 3 checked instances (or all of them when there are fewer).

## Methods and confidence

- **measured**: A measurement tool produced the value (an evidence.json field or an ffmpeg/ffprobe filter output). Name the tool and the field.
- **observed**: You looked at extracted frames, crops, scopes, spectrograms or waveforms and saw it. Give the timestamps you looked at.
- **inferred**: Reasoned from measured or observed facts, e.g. 'synthetic voice' from flat pitch on a spectrogram. State the reasoning in the note.
- **assumed**: No direct evidence; a default or convention. Use only for gaps the format needs filled, and keep confidence at 0.3 or lower.

Confidence bands:
- 0.85-0.95: measured, the tool ran cleanly and the value is unambiguous (for example shot_stats.median_s).
- 0.65-0.85: measured but sensitive to tool settings, or observed consistently on 3 or more instances.
- 0.45-0.65: observed on 1-2 instances, or inferred from measured values with one reasoning step.
- 0.25-0.45: inferred with several steps or from weak cues.
- 0.0-0.3: assumed, or not determinable (answer the string 'not determinable').
- These bands are the swarm's calibration convention, not a statistical guarantee; challengers move answers between bands.

Not determinable: When the evidence cannot answer a question, return the answer string "not determinable" with method "assumed", confidence 0 and a note that names the missing evidence (for example 'audio.tempo_bpm is null: librosa unavailable'). Never guess to fill a slot.

## IR pointer conventions

- ir_path is a JSON Pointer (RFC 6901) into the Video format IR (contract schema video_re_format_ir).
- A final '/-' means 'append this answer to the array' (the RFC 6901 end-of-array token), e.g. /motion/transitions/- or /generation_rules/-.
- A '*' segment means 'each array element the answer is about'; the answer must say which elements (for example beats with role 'item'). The lifter resolves '*' to concrete indexes.
- Paths under free-form objects (typography.title, typography.captions, typography.labels, audio.narration, audio.music, render_binding.mapping) use the snake_case key named in the question.

## Answer types used here

- `number`: {"value": n, "unit": "..."} optionally with "min" and "max"; becomes an IR observed_number
- `integer`: {"value": n}
- `ratio`: {"value": r} with 0 <= r <= 1
- `seconds`: {"value": s, "unit": "s"} optionally with "min"/"max"
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `segments`: [{"start_s": a, "end_s": b, "label": "..."}]
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- captions[] timing
- text_regions[]
- shots[]
- audio.onsets_s

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_cta_endcard`, `video_re_detect_loopability`, `video_re_detect_progress_bar`, `video_re_detect_hook_window_density`, `video_re_detect_label_patterns`, `video_re_detect_intro_outro_bumpers`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F4 contact sheet; F1 at each claimed device; the last 5 s frame by frame (F8) for the CTA.

## Pitfalls challengers check first

- Claiming a device works (retention effect) when only its presence is observable
- Calling every cut a pattern interrupt
- Missing a spoken-only CTA

## Parameters this lens usually proposes

- cta_kind (enum)
- cta_at_ratio
- rehook_at_ratio
- open_loop (boolean)

## IR paths this lens writes

- `/generation_rules/-` (8)
- `/parameters/-` (2)
- `/script/hook_pattern` (1)
- `/timeline/beats` (4)
- `/timeline/beats/*/start_ratio` (1)
- `/timeline/retention_devices/-` (13)
- `/typography/labels/cta_style` (1)

## Questions (30)

### retention_cta-001 · `object` → `/timeline/retention_devices/-`

**Which retention devices are present (open loop, countdown or ordinal progress, re-hook, pattern interrupt, teaser, cliffhanger, payoff promise), each with timestamps?**

- Why it matters: Fills timeline.retention_devices.
- How to answer: Combine label sequences (text_regions), caption phrasing (analysis only), visual interrupts (F4) and audio hits; list each device with timestamps.
- Evidence required: evidence.text_regions[]; evidence.captions[] (analysis only); frames: F4
- Challenge: Presence is observable, effect is not: reject any claim that a device 'increases retention'.

### retention_cta-002 · `segments` → `/timeline/retention_devices/-`

**How many open loops are opened, and when is each closed?**

- Why it matters: Becomes open-loop rules with open and close ratios.
- How to answer: Find statements that withhold information and the later resolution; give both times as ratios.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Each loop must have a resolution time or be marked unresolved.

### retention_cta-003 · `boolean` → `/timeline/retention_devices/-`

**Does the viewer see progress through the list (ordinal labels, countdown numbers, 'N of M')?**

- Why it matters: Becomes a progress-cue parameter.
- How to answer: Label crops (F3) per item.
- Evidence required: frames: F3 labels
- Challenge: Progress bars count too; say which form.

### retention_cta-004 · `ratio` → `/timeline/retention_devices/-`

**Is there a mid-video re-hook (a new promise or teaser in the middle), and at what ratio?**

- Why it matters: Places a re-hook beat.
- How to answer: Look between 35% and 65% of runtime for a teaser of what is coming.
- Evidence required: evidence.captions[] (analysis only); frames: F1
- Challenge: A plain transition to the next item is not a re-hook.

### retention_cta-005 · `enum` → `/timeline/beats`

**Is there a call to action, and what kind (follow, comment, share, save, watch part 2, link)?**

- Choices: `follow`, `comment`, `share`, `save`, `part-2`, `link`, `multiple`, `none`
- Why it matters: Fills the CTA slot.
- How to answer: Check the last 15% of captions and text crops.
- Evidence required: evidence.captions[] (analysis only); frames: F3
- Challenge: Spoken-only CTAs are easy to miss; check the audio transcript too.

### retention_cta-006 · `ratio` → `/timeline/beats/*/start_ratio`

**At what fraction of the runtime does the CTA start (seconds before the end in the note)?**

- Why it matters: Places the CTA beat.
- How to answer: First CTA cue time / duration; duration - time.
- Evidence required: CTA cue time; evidence.source.duration_s
- Challenge: Report both values.

### retention_cta-007 · `enum` → `/timeline/beats`

**Is the CTA spoken, shown on screen, or both?**

- Choices: `spoken`, `on-screen`, `both`, `none`
- Why it matters: Fills CTA modality.
- How to answer: Compare captions and text crops at the CTA time.
- Evidence required: evidence.captions[] (analysis only); frames: F3
- Challenge: Check both channels.

### retention_cta-008 · `seconds` → `/timeline/beats`

**How long does the CTA last?**

- Why it matters: Fills CTA beat length.
- How to answer: From first to last CTA cue.
- Evidence required: CTA cues
- Challenge: Recompute.

### retention_cta-009 · `boolean` → `/timeline/retention_devices/-`

**Does the video ask a specific question to prompt comments?**

- Why it matters: Adds a comment-prompt slot.
- How to answer: Questions in the last 20% of captions or text.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Rhetorical questions answered in the video do not count.

### retention_cta-010 · `boolean` → `/parameters/-`

**Is the video framed as part of a series (part numbers, 'next episode' tease)?**

- Why it matters: Adds series fields to the format.
- How to answer: Text crops and captions at the start and end.
- Evidence required: frames: F3; evidence.captions[] (analysis only)
- Challenge: The series name must not be carried into the format.

### retention_cta-011 · `boolean` → `/timeline/retention_devices/-`

**Does the last line or frame lead back into the first (seamless loop for rewatching)?**

- Why it matters: Becomes a loop-ending option.
- How to answer: F10 between the last and first frames; compare the last caption's structure with the hook's (analysis only).
- Evidence required: frames: F10; evidence.captions[] (analysis only)
- Challenge: Visual similarity alone (same template) is not a loop; the sentence must continue too.

### retention_cta-012 · `boolean` → `/timeline/retention_devices/-`

**Are visual progress indicators used (progress bar, dots, timeline)?**

- Why it matters: Records presence; some house styles forbid them, so the IR must say.
- How to answer: F1 frames at 25%, 50%, 75% of runtime.
- Evidence required: frames: F1
- Challenge: Check all three frames.

### retention_cta-013 · `integer` → `/timeline/retention_devices/-`

**How many reasons to keep watching are stated in the hook (for example 'number 1 will surprise you', 'stay for the last one')?**

- Why it matters: Sets the count of hook promises.
- How to answer: Count promise statements in the first 10% (captions, analysis only).
- Evidence required: evidence.captions[] (analysis only)
- Challenge: The topic statement itself is not a promise.

### retention_cta-014 · `boolean` → `/timeline/retention_devices/-`

**Is the best item explicitly teased as saved for last?**

- Why it matters: Becomes a 'best last' ordering rule with a tease.
- How to answer: Captions in the first half referencing the final item.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Give the timestamp of the tease.

### retention_cta-015 · `timestamps` → `/timeline/retention_devices/-`

**Are there interaction prompts mid-video (pause to guess, comment your answer, look closely)?**

- Why it matters: Adds interaction prompts.
- How to answer: Captions and text crops in the middle 60%.
- Evidence required: evidence.captions[] (analysis only); frames: F3
- Challenge: List each prompt.

### retention_cta-016 · `seconds` → `/generation_rules/-`

**How many seconds pass between the payoff and the end of the video?**

- Why it matters: Sets a post-payoff limit.
- How to answer: duration - payoff beat end (from structure).
- Evidence required: timeline beats; evidence.source.duration_s
- Challenge: Cross-check with the structure lens.

### retention_cta-017 · `enum` → `/typography/labels/cta_style`

**How is the CTA drawn on screen (text only, button shape, arrow pointing at UI, animated icon)?**

- Choices: `text-only`, `button`, `arrow-to-ui`, `animated-icon`, `none`
- Why it matters: Fills CTA graphic style.
- How to answer: F3 at the CTA.
- Evidence required: frames: F3
- Challenge: Platform-native UI is not part of the video.

### retention_cta-018 · `seconds` → `/generation_rules/-`

**What is the median time between new-information moments (new fact, new number, new visual)?**

- Why it matters: Becomes a 'new information every N seconds' rule.
- How to answer: Merge times of new labels, new key numbers and new assets; median gap.
- Evidence required: evidence.text_regions[]; evidence.shots[]
- Challenge: New captions repeating the same idea are not new information.

### retention_cta-019 · `object` → `/timeline/retention_devices/-`

**Which pattern interrupts occur (sudden zoom, sound hit, colour flash, layout change, silence), with timestamps?**

- Why it matters: Lists interrupt devices for the generator.
- How to answer: Combine transitions, effects and audio drops; list with type.
- Evidence required: frames: F8; A3
- Challenge: Ordinary cuts are not interrupts; each must break the established pattern.

### retention_cta-020 · `timestamps` → `/timeline/retention_devices/-`

**Is there a mid-video cliffhanger (an unresolved moment right before a section change)?**

- Why it matters: Adds a cliffhanger device.
- How to answer: Captions near section ends with an unresolved question or reveal held across the boundary.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: The resolution must come after the boundary.

### retention_cta-021 · `number` → `/timeline/retention_devices/-`

**How often is the viewer addressed directly on screen (text containing 'you' or an imperative)?**

- Why it matters: Sets on-screen address frequency.
- How to answer: Count text crops with direct address / minute.
- Evidence required: frames: F3; evidence.captions[] (analysis only)
- Challenge: Report the count and duration.

### retention_cta-022 · `seconds` → `/script/hook_pattern`

**Is the benefit to the viewer stated early (what they will learn or get), and when?**

- Why it matters: Adds a benefit statement slot.
- How to answer: Captions in the first 15% with a benefit statement.
- Evidence required: evidence.captions[] (analysis only)
- Challenge: Give the timestamp; topic mention is not a benefit.

### retention_cta-023 · `timestamps` → `/generation_rules/-`

**Are social proof cues used (counts of people, expert references, results achieved)?**

- Why it matters: Adds proof slots that require sourced numbers in variants.
- How to answer: Captions and text crops with numbers about people or authority.
- Evidence required: evidence.captions[] (analysis only); frames: F3
- Challenge: Every proof cue becomes a claim that needs a source in a variant.

### retention_cta-024 · `rule` → `/generation_rules/-`

**Write the retention placement rule (re-hook ratio, CTA ratio, interrupt interval) in terms of parameters.**

- Why it matters: Gives the compiler procedural retention placement.
- How to answer: Combine 004, 006 and 019, for example 're-hook at 0.45-0.55; CTA starts at duration - cta_s; interrupt every 8-12 s'.
- Evidence required: retention answers
- Challenge: Re-derive the source's device times from the rule.

### retention_cta-025 · `list` → `/parameters/-`

**Which retention parameters should a new video set (cta_kind, cta_text slot, rehook_at_ratio, open_loop)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect 004, 005, 006 and 002.
- Evidence required: retention answers
- Challenge: Each parameter needs derived_from.

### retention_cta-026 · `enum` → `/generation_rules/-`

**Does the CTA come before the payoff (interrupting content) or after it?**

- Choices: `before-payoff`, `after-payoff`, `no-cta`
- Why it matters: Becomes a CTA order rule.
- How to answer: Compare CTA time with the payoff beat.
- Evidence required: CTA time; timeline beats
- Challenge: Cross-check with structure_beats-016.

### retention_cta-027 · `timestamps` → `/generation_rules/-`

**Which frames would work as thumbnails (clear subject, readable text, high contrast)?**

- Why it matters: Adds a thumbnail selection rule for the rendered variant.
- How to answer: Pick 3 frames from F4 that meet the criteria; give timestamps and the measured text size and contrast.
- Evidence required: frames: F4; frames: F1
- Challenge: Thumbnails are never exported from the source; the rule applies to the variant.

### retention_cta-028 · `segments` → `/generation_rules/-`

**Which stretches have no new visual or verbal information for more than 4 seconds?**

- Why it matters: Becomes a negative rule (avoid dead stretches) with measured examples.
- How to answer: Gaps in the merged event list (new text, new asset, new sentence) longer than 4 s.
- Evidence required: merged event times
- Challenge: Report the event sources merged.

### retention_cta-029 · `boolean` → `/generation_rules/-`

**Does the number of items delivered match the number promised in the hook?**

- Why it matters: A consistency rule for generated scripts.
- How to answer: Compare the hook's promised count (title or captions) with n_items.
- Evidence required: frames: F3 title; n_items
- Challenge: If no count was promised, answer not determinable.

### retention_cta-030 · `seconds` → `/timeline/beats`

**Is there an end card with additional prompts (next video, subscribe graphic), and how long?**

- Why it matters: Fills the end card beat.
- How to answer: F8 over the last 3 s.
- Evidence required: frames: F8
- Challenge: Cross-check with structure_beats-010.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F4** Whole-video contact sheet, 1 frame per second: ffmpeg -v error -i "$SRC" -vf "fps=1,scale=180:-2,tile=8x8" -frames:v 1 "$WORK/sheet.jpg" (or use the keyframes and contact sheet from video_re_keyframes_contact_sheet)
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F10** Similarity of two frames (SSIM, 1.0 = identical): ffmpeg -i a.jpg -i b.jpg -lavfi "[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*"
- **A3** Momentary loudness every 100 ms (LUFS): ffmpeg -v error -i "$SRC" -af "ebur128=metadata=1,ametadata=mode=print:key=lavfi.r128.M:file=$WORK/lufs_m.txt" -f null -

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "retention_cta-001", "ir_path": "/timeline/retention_devices/-", "answer_type": "object"}, {"id": "retention_cta-002", "ir_path": "/timeline/retention_devices/-", "answer_type": "segments"}, {"id": "retention_cta-003", "ir_path": "/timeline/retention_devices/-", "answer_type": "boolean"}, {"id": "retention_cta-004", "ir_path": "/timeline/retention_devices/-", "answer_type": "ratio"}, {"id": "retention_cta-005", "ir_path": "/timeline/beats", "answer_type": "enum", "choices": ["follow", "comment", "share", "save", "part-2", "link", "multiple", "none"]}, {"id": "retention_cta-006", "ir_path": "/timeline/beats/*/start_ratio", "answer_type": "ratio"}, {"id": "retention_cta-007", "ir_path": "/timeline/beats", "answer_type": "enum", "choices": ["spoken", "on-screen", "both", "none"]}, {"id": "retention_cta-008", "ir_path": "/timeline/beats", "answer_type": "seconds"}, {"id": "retention_cta-009", "ir_path": "/timeline/retention_devices/-", "answer_type": "boolean"}, {"id": "retention_cta-010", "ir_path": "/parameters/-", "answer_type": "boolean"}, {"id": "retention_cta-011", "ir_path": "/timeline/retention_devices/-", "answer_type": "boolean"}, {"id": "retention_cta-012", "ir_path": "/timeline/retention_devices/-", "answer_type": "boolean"}, {"id": "retention_cta-013", "ir_path": "/timeline/retention_devices/-", "answer_type": "integer"}, {"id": "retention_cta-014", "ir_path": "/timeline/retention_devices/-", "answer_type": "boolean"}, {"id": "retention_cta-015", "ir_path": "/timeline/retention_devices/-", "answer_type": "timestamps"}, {"id": "retention_cta-016", "ir_path": "/generation_rules/-", "answer_type": "seconds"}, {"id": "retention_cta-017", "ir_path": "/typography/labels/cta_style", "answer_type": "enum", "choices": ["text-only", "button", "arrow-to-ui", "animated-icon", "none"]}, {"id": "retention_cta-018", "ir_path": "/generation_rules/-", "answer_type": "seconds"}, {"id": "retention_cta-019", "ir_path": "/timeline/retention_devices/-", "answer_type": "object"}, {"id": "retention_cta-020", "ir_path": "/timeline/retention_devices/-", "answer_type": "timestamps"}, {"id": "retention_cta-021", "ir_path": "/timeline/retention_devices/-", "answer_type": "number"}, {"id": "retention_cta-022", "ir_path": "/script/hook_pattern", "answer_type": "seconds"}, {"id": "retention_cta-023", "ir_path": "/generation_rules/-", "answer_type": "timestamps"}, {"id": "retention_cta-024", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "retention_cta-025", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "retention_cta-026", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["before-payoff", "after-payoff", "no-cta"]}, {"id": "retention_cta-027", "ir_path": "/generation_rules/-", "answer_type": "timestamps"}, {"id": "retention_cta-028", "ir_path": "/generation_rules/-", "answer_type": "segments"}, {"id": "retention_cta-029", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "retention_cta-030", "ir_path": "/timeline/beats", "answer_type": "seconds"}]
```
