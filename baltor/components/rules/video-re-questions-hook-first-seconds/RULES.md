# Video RE question bank: Hook and first seconds

Lens `hook_first_seconds` · 36 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-hook-first-seconds` subagent and challenged by `video-re-challenger`.

Describes exactly what happens in the first frame and the first 3-5 seconds (title, voice, motion, sound) so the opening can be rebuilt with new content.

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
- `ms`: {"value": n, "unit": "ms"} optionally with "min"/"max"; signed when an offset (negative = earlier)
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `pattern`: a template with {slots} in place of content words, e.g. 'FACT {n}: {number} {unit}'
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[0..3]
- text_regions[] with t_s < 5
- audio.speech_segments[0]
- audio.onsets_s < 3
- shots[0].motion_energy

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_hook_window_density`, `video_re_detect_text_presence_timeline`, `video_re_detect_text_position_grid`, `video_re_detect_text_animation_type`, `video_re_detect_zoom_punch_in`, `video_re_classify_face_presence`, `video_re_detect_text_color_contrast`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F1 at 0.0, 0.5, 1.0, 2.0, 3.0 s; F8 over 0-0.5 s for the title entrance; A1 spectrogram over 0-3 s.

## Pitfalls challengers check first

- Reading frame 0 from a keyframe that is not at 0.0 s
- Treating a platform thumbnail as the first frame
- Confusing the hook line with the title text
- Quoting the hook instead of turning it into a slot pattern

## Parameters this lens usually proposes

- title_text (string slot)
- title_color (color)
- title_hold_s (duration_s)
- hook_pattern (enum)
- hero_visual (asset)

## IR paths this lens writes

- `/audio/music/entry` (1)
- `/audio/narration/first_word_s` (1)
- `/audio/narration/hook_loudness_delta_db` (1)
- `/audio/narration/hook_wpm` (1)
- `/audio/narration/lead_in_ms` (1)
- `/audio/sfx/-` (1)
- `/generation_rules/-` (2)
- `/motion/camera_moves/-` (1)
- `/motion/text_animations/-` (1)
- `/parameters/-` (1)
- `/script/hook_pattern` (4)
- `/timeline/beats/*/end_ratio` (1)
- `/timeline/retention_devices/-` (5)
- `/typography/captions/first_caption_s` (1)
- `/typography/labels/series_tag` (1)
- `/typography/title/area_ratio` (1)
- `/typography/title/color` (1)
- `/typography/title/contrast_ratio` (1)
- `/typography/title/cover_frame` (1)
- `/typography/title/first_frame_words` (1)
- `/typography/title/hold_s` (1)
- `/typography/title/layout` (1)
- `/typography/title/overlaps_subject` (1)
- `/typography/title/placement` (1)
- `/typography/title/relation_to_voice` (1)
- `/typography/title/size_ratio` (1)
- `/typography/title/thumbnail_legible` (1)
- `/visual/subject_framing` (1)

## Questions (36)

### hook_first_seconds-001 · `integer` → `/typography/title/first_frame_words`

**How many words of on-screen text are visible on the frame at exactly 0.0 s?**

- Why it matters: Sets the first-frame title word budget (title_max_words).
- How to answer: Extract F1 at T=0 (not a keyframe from evidence, which may be later); crop the text with F3 enlarged 2x; count words without copying them beyond a 6-word locating note.
- Evidence required: frames: F1 at 0.0 s; frames: F3 crop of text
- Challenge: Re-extract with -ss after -i (accurate seek) to rule out a seek to the wrong frame; count again.

### hook_first_seconds-002 · `object` → `/typography/title/placement`

**Where is the title's bounding box on the first frame (centre y as a fraction of height, centre x, width as a fraction of frame width)?**

- Why it matters: Fills the title placement used by every rendered variant.
- How to answer: Use evidence.text_regions[] entries with t_s nearest 0 (bbox and y_center_ratio); confirm on F1 at 0.0 s and measure the box by pixel coordinates on a crop.
- Evidence required: evidence.text_regions[] near t=0; frames: F1 at 0.0 s
- Challenge: Check that the region is the title and not a caption or watermark; compare the bbox with a manual measurement on the frame (tolerance 3% of height).

### hook_first_seconds-003 · `enum` → `/typography/title/overlaps_subject`

**Does the title overlap the main subject or photo, sit in empty space beside it, or sit on a separate band?**

- Choices: `over-subject`, `over-photo-not-subject`, `empty-space`, `separate-band`, `no-title`
- Why it matters: Captures whether the format layers the title over the photo (a recurring house preference) or reserves space.
- How to answer: On F1 at 0.0 s and 1.0 s, compare the title bbox with the subject region; a subject is the largest face, person or object in focus.
- Evidence required: frames: F1 at 0.0 and 1.0 s; evidence.text_regions[] near t=0
- Challenge: Ask whether the 'subject' is actually a background element; if two readings are possible, lower confidence and name both.

### hook_first_seconds-004 · `seconds` → `/audio/narration/first_word_s`

**How many seconds after the start is the first spoken word?**

- Why it matters: Sets the voice lead-in in the hook timing rule.
- How to answer: Read the first evidence.audio.speech_segments[0].start_s; confirm the onset on an A1 spectrogram of 0-2 s (voiced harmonics).
- Evidence required: evidence.audio.speech_segments[0]; A1 over 0-2 s
- Challenge: Music with vocals can be detected as speech; check the spectrogram for a narration voice rather than sung notes.

### hook_first_seconds-005 · `seconds` → `/timeline/retention_devices/-`

**When is the first cut, in seconds?**

- Why it matters: Tells the generator how long the opening shot holds before the first visual change.
- How to answer: Take evidence.shots[0].end_s; verify with F11 scene scores over 0-5 s that no earlier dissolve or cut was missed.
- Evidence required: evidence.shots[0].end_s; F11 scene scores 0-5 s
- Challenge: If the opening shot is a fast zoom, detectors may report a false cut; inspect F1 either side.

### hook_first_seconds-006 · `enum` → `/script/hook_pattern`

**What type of hook is used: question, bold claim, specific number, contradiction or myth, direct 'you' address, visual shock, mid-action cold open, unfinished sentence, or a promise of a list?**

- Choices: `question`, `bold-claim`, `specific-number`, `contradiction`, `direct-address`, `visual-shock`, `cold-open`, `unfinished-sentence`, `list-promise`, `other`
- Why it matters: Fills hook_pattern so new videos can be written with the same opening move.
- How to answer: Read the first caption cards (evidence.captions with start_s < 5, analysis only) and the title crop; classify by the dominant move. Do not copy the line.
- Evidence required: evidence.captions[] start_s < 5 (analysis only); frames: F3 title crop
- Challenge: If two types apply (number inside a question), require the note to name the secondary type and justify the primary.

### hook_first_seconds-007 · `pattern` → `/script/hook_pattern`

**What is the hook's slot pattern with content words replaced (for example '{number} {things} that {surprising verb}')?**

- Why it matters: Turns the opening line into a reusable template.
- How to answer: From the first sentence (captions, analysis only) keep function words and structure, replace every noun, number, name and verb with a typed slot. Keep at most the structure, never the content.
- Evidence required: evidence.captions[] first sentence (analysis only)
- Challenge: Check that no content word from the source survives in the pattern; any copied distinctive phrase is a rejection.

### hook_first_seconds-008 · `enum` → `/typography/title/relation_to_voice`

**Is the spoken hook the same as the on-screen title, a paraphrase of it, or different information?**

- Choices: `same-words`, `paraphrase`, `different-information`, `no-spoken-hook`, `no-title`
- Why it matters: Decides whether title and first line are generated together or separately.
- How to answer: Compare the title crop (F3 at 0.5 s) with the first caption/transcribed sentence; judge overlap of key content words without writing them down.
- Evidence required: frames: F3 title crop; evidence.captions[] first sentence (analysis only)
- Challenge: Transcription errors can make a same-words title look like a paraphrase; check the audio timing alignment too.

### hook_first_seconds-009 · `integer` → `/timeline/retention_devices/-`

**How many distinct visual changes (cuts, text appearances, zoom jumps, colour flashes) happen in the first 3 seconds?**

- Why it matters: Sets the opening event density for the hook rule.
- How to answer: Count cuts (evidence.shots with start_s < 3), new text regions (text_regions t_s < 3) and visible jumps on F2 burst sheets for 0-1, 1-2, 2-3 s.
- Evidence required: evidence.shots[]; evidence.text_regions[]; frames: F2 at 0, 1, 2 s
- Challenge: Make sure a single animated title is not counted once per frame; each element counts once per appearance.

### hook_first_seconds-010 · `boolean` → `/timeline/retention_devices/-`

**Is there visible motion from the very first frame, or does the video open on a still?**

- Why it matters: Becomes a rule that the opening frame must already move (or may hold).
- How to answer: Use F5 (full frame) for the first 1 s and report mean frame difference; inspect F2 at 0 s.
- Evidence required: F5 over 0-1 s; evidence.shots[0].motion_energy; frames: F2 at 0 s
- Challenge: A mean difference below about 0.5 can be compression noise; verify by eye on the burst.

### hook_first_seconds-011 · `ms` → `/audio/narration/lead_in_ms`

**How long is the silence (or near-silence) before any audio starts?**

- Why it matters: Sets audio lead-in; a silent first second changes autoplay behaviour.
- How to answer: Run A4 over the first 2 s and A3 momentary loudness; report ms until loudness rises above -40 LUFS.
- Evidence required: A4 silences; A3 momentary loudness
- Challenge: A3 momentary loudness uses a 400 ms window, so values are smeared; confirm with A6 RMS.

### hook_first_seconds-012 · `boolean` → `/audio/sfx/-`

**Is there a sound effect (hit, whoosh, riser, pop) within the first second?**

- Why it matters: Adds an opening sfx slot to the audio recipe.
- How to answer: A1 spectrogram 0-1.5 s with and without highpass=f=3000; look for broadband transients or sweeps not aligned with speech; cross-check evidence.audio.onsets_s < 1.
- Evidence required: A1 0-1.5 s; evidence.audio.onsets_s
- Challenge: A plosive at the first word or a music downbeat is not a sound effect; the transient must stand apart from both.

### hook_first_seconds-013 · `enum` → `/audio/music/entry`

**Does music start at 0 s, under the hook voice, or only after the hook ends?**

- Choices: `from-start`, `under-hook`, `after-hook`, `no-music`
- Why it matters: Fills audio.music.entry for the mix recipe.
- How to answer: Compare A5 side-channel loudness (stereo) and A1 spectrogram over 0-5 s for sustained tonal or rhythmic content.
- Evidence required: A5 side loudness 0-5 s; A1 0-5 s
- Challenge: Side-channel loudness is meaningless on mono audio (check A7 channels); then rely on the spectrogram and lower confidence.

### hook_first_seconds-014 · `seconds` → `/typography/title/hold_s`

**How long does the title stay on screen, and how does it leave (cut away, fade, shrink to corner, stays all video)?**

- Why it matters: Fills title hold_s and exit behaviour.
- How to answer: Track the title region in evidence.text_regions[] from first to last t_s; inspect F8 frames around the disappearance.
- Evidence required: evidence.text_regions[]; frames: F8 at title exit
- Challenge: Check whether the 'title' that persists is actually a series tag or watermark.

### hook_first_seconds-015 · `enum` → `/motion/text_animations/-`

**How does the title enter in its first 500 ms (pop with overshoot, scale-up, slide, type-on, fade, already present)?**

- Choices: `pop-overshoot`, `scale-up`, `slide`, `type-on`, `fade`, `already-present`, `other`
- Why it matters: Adds the title entrance to motion.text_animations.
- How to answer: F8 frame steps over 0-0.5 s; measure the title box height per frame on the stepped images.
- Evidence required: frames: F8 over 0-0.5 s
- Challenge: If the title is present on frame 0 at full size, the answer must be already-present, whatever happens later.

### hook_first_seconds-016 · `object` → `/typography/title/color`

**What colour is the title text, and what is behind it (none, solid plate, frosted blur panel, stroke, drop shadow)?**

- Why it matters: Fills title colour and backing, both common parameters.
- How to answer: F9 average colour on a crop inside a letter stroke (choose a thick stroke, 3x3 px), and F3 crop of the backing; compare the backing region in two frames with different backgrounds to tell blur from a solid plate.
- Evidence required: frames: F9 text colour; frames: F3 backing crop
- Challenge: Anti-aliased edges and compression shift colour; resample in two other letters and report the spread.

### hook_first_seconds-017 · `ratio` → `/typography/title/size_ratio`

**How tall is the title text block relative to the frame height?**

- Why it matters: Fills title size_ratio for rendering at any resolution.
- How to answer: bbox height from evidence.text_regions[] near t=0 divided by source.height; for multi-line titles also report lines and per-line height from an F3 crop.
- Evidence required: evidence.text_regions[]; evidence.source.height; frames: F3
- Challenge: A bbox that includes the backing panel overstates text size; measure letters directly on the crop.

### hook_first_seconds-018 · `boolean` → `/script/hook_pattern`

**Does the opening show the end result or payoff first (a visual promise) before explaining it?**

- Why it matters: Becomes a 'show the payoff first' rule for the hook.
- How to answer: Compare the first shot keyframe with later keyframes using F10 SSIM; a match above 0.7 with a shot in the final third indicates a flash-forward.
- Evidence required: evidence.shots[].keyframe; frames: F10 comparisons
- Challenge: A shared background or template layout gives high SSIM without being the same shot; inspect the pair by eye.

### hook_first_seconds-019 · `boolean` → `/typography/title/thumbnail_legible`

**Does the first frame stay legible as a thumbnail (title readable when the frame is scaled to 20% width)?**

- Why it matters: Records whether the first frame doubles as the thumbnail.
- How to answer: Scale F1 at 0.0 s to 216 px wide (ffmpeg -vf scale=216:-2) and inspect whether the title words are distinguishable.
- Evidence required: frames: F1 at 0.0 s scaled to 216 px
- Challenge: Legibility is a judgement; require the note to state the scaled text height in pixels.

### hook_first_seconds-020 · `number` → `/typography/title/contrast_ratio`

**What is the approximate contrast ratio between the title colour and the colour directly behind it?**

- Why it matters: Sets a minimum contrast constraint for generated titles.
- How to answer: Take text colour and backing colour from F9 samples; compute WCAG relative luminance contrast (L1 + 0.05) / (L2 + 0.05).
- Evidence required: frames: F9 text and backing samples
- Challenge: Recompute from the reported RGB values; with a blurred photo behind the text, sample three background points and report the worst.

### hook_first_seconds-021 · `ratio` → `/visual/subject_framing`

**Is a face visible in the first frame, and what fraction of the frame height does it occupy?**

- Why it matters: Becomes a hook framing rule (face-first or object-first).
- How to answer: Inspect F1 at 0.0 s; measure the face box height in pixels divided by frame height. Do not identify the person.
- Evidence required: frames: F1 at 0.0 s
- Challenge: Answers that name or describe the identity of a person are rejected; only size and position are allowed.

### hook_first_seconds-022 · `number` → `/generation_rules/-`

**Is the first shot shorter or longer than the video's median shot (ratio first shot / median)?**

- Why it matters: Tells the generator whether the hook is front-loaded with faster cuts or a longer hold.
- How to answer: evidence.shots[0].duration_s divided by evidence.shot_stats.median_s.
- Evidence required: evidence.shots[0].duration_s; evidence.shot_stats.median_s
- Challenge: Recompute the division; check that shot 0 is not a 1-frame black leader.

### hook_first_seconds-023 · `object` → `/audio/narration/hook_wpm`

**What is the speech rate in the first 5 seconds compared with the whole video (words per minute in both)?**

- Why it matters: Captures whether the hook is delivered faster or slower than the body.
- How to answer: Count caption words with start_s < 5 (analysis only) divided by speech time inside 0-5 s (speech_segments); compare with evidence.audio.speech_wpm.
- Evidence required: evidence.captions[]; evidence.audio.speech_segments; evidence.audio.speech_wpm
- Challenge: With fewer than 8 words in the window, the rate is unstable; confidence must stay below 0.5.

### hook_first_seconds-024 · `number` → `/audio/narration/hook_loudness_delta_db`

**How much louder or quieter are the first 3 seconds than the integrated loudness of the whole video (dB)?**

- Why it matters: Sets a hook loudness offset in the mix recipe.
- How to answer: Mean of A3 momentary loudness over 0-3 s minus evidence.audio.integrated_lufs.
- Evidence required: A3 momentary loudness; evidence.audio.integrated_lufs
- Challenge: Averaging LUFS values arithmetically is approximate; note it, and check the sign against A6 RMS.

### hook_first_seconds-025 · `object` → `/timeline/retention_devices/-`

**What information is withheld by the hook (a curiosity gap), and at what timestamp is it resolved?**

- Why it matters: Becomes an open-loop retention device with a resolution time.
- How to answer: Describe the withheld element as a slot (for example 'the identity of {item 1}'), then find where captions or labels resolve it. Give both timestamps.
- Evidence required: evidence.captions[] (analysis only); evidence.text_regions[]
- Challenge: If the 'gap' is just the topic of the video, it is not an open loop; reject or downgrade.

### hook_first_seconds-026 · `boolean` → `/script/hook_pattern`

**Does the hook state a specific number or quantity, on screen or in the voice?**

- Why it matters: Becomes a constraint for the hook template (must contain a number).
- How to answer: Check the title crop and first two caption cards for digits or number words; record only that a number exists and its type (count, year, measurement).
- Evidence required: frames: F3 title crop; evidence.captions[] (analysis only)
- Challenge: Ordinals in a label (FACT 1) do not count as a hook number.

### hook_first_seconds-027 · `seconds` → `/timeline/beats/*/end_ratio`

**How many seconds long is the hook segment before the body begins?**

- Why it matters: Fills the hook beat length.
- How to answer: Use the first non-hook beat start from structure_beats-001 or, independently, the first label appearance or first topic change; report both if they differ.
- Evidence required: timeline beats; evidence.text_regions[]
- Challenge: Compare with the structure lens; a difference above 0.5 s must be explained in the note.

### hook_first_seconds-028 · `boolean` → `/typography/labels/series_tag`

**Is a series name, recurring tag or brand mark shown in the hook?**

- Why it matters: Adds a series_tag slot that a new format must fill with its own name.
- How to answer: Look for a small persistent text or logo region in evidence.text_regions[] near frame edges during 0-3 s; crop it with F3.
- Evidence required: evidence.text_regions[]; frames: F3 corners
- Challenge: Platform watermarks and usernames are not series tags; classify them for the rights lens instead.

### hook_first_seconds-029 · `boolean` → `/typography/title/cover_frame`

**Is the first frame visually distinct from the rest (different grade, a frame border, a flash, a still title card)?**

- Why it matters: Decides whether frame 0 is a designed cover frame.
- How to answer: Compare F6 statistics (YAVG, SATAVG) of frame 0 against the video median; inspect F1 at 0.0 and 1.0 s.
- Evidence required: F6 stats; frames: F1 at 0.0 and 1.0 s
- Challenge: A fade-in from black makes frame 0 distinct by accident; check frames 0-5 with F8.

### hook_first_seconds-030 · `number` → `/motion/camera_moves/-`

**Is there a zoom or punch-in on the subject during the first second, and by how much does the scale change?**

- Why it matters: Adds the opening camera move to motion.camera_moves.
- How to answer: Measure the width of a fixed feature on F1 at 0.0 s and at 1.0 s (same shot); ratio = later width / earlier width. Cross-check evidence.shots[0].camera.zoom.
- Evidence required: frames: F1 at 0.0 and 1.0 s; evidence.shots[0].camera.zoom
- Challenge: Make sure a cut did not occur between the two frames (check shots[0].end_s).

### hook_first_seconds-031 · `list` → `/parameters/-`

**Which hook elements are fixed format and which must become parameters (title text, title colour, hero image, hook line pattern, sound hit)?**

- Why it matters: Feeds the parameteriser with the hook's slots.
- How to answer: Combine answers 001-030: anything that carries content (words, image) is a parameter; style that a series would keep (placement, entrance, colour) is fixed or a parameter with a default.
- Evidence required: hook lens answers
- Challenge: Each proposed parameter must point to the question that observed it (derived_from).

### hook_first_seconds-032 · `rule` → `/generation_rules/-`

**Write the hook timing rule (title appear and hold, voice start, first cut, first item start) in terms of parameters.**

- Why it matters: Gives the compiler a reproducible opening.
- How to answer: Use measured times from 004, 005, 014 and 027, scaled where sensible (for example 'title at 0.0 s, holds title_hold_s; voice at 0.3 s; first cut at 0.8-1.2 s; first item at 0.1 x duration').
- Evidence required: hook lens answers
- Challenge: Re-derive the source's opening times from the rule; any mismatch over 0.3 s must be fixed or explained.

### hook_first_seconds-033 · `object` → `/typography/captions/first_caption_s`

**When does the first caption appear, and is it on screen at the same time as the title?**

- Why it matters: Decides whether captions wait for the title or overlap it.
- How to answer: First evidence.captions[] start_s (or first text region in the caption area) compared with the title hold window.
- Evidence required: evidence.captions[0]; evidence.text_regions[]
- Challenge: If captions come from transcription (not burned in), on-screen overlap cannot be measured from them; check frames.

### hook_first_seconds-034 · `timestamps` → `/timeline/retention_devices/-`

**Is the opening a flash-forward excerpt from later in the video (a cold-open teaser)?**

- Why it matters: Adds a teaser beat option to the format.
- How to answer: F10 SSIM of each shot in the first 3 s against all later keyframes; list matches over 0.75 with their timestamps.
- Evidence required: evidence.shots[].keyframe; frames: F10
- Challenge: Matches inside the same template background are false positives; the subject must match too.

### hook_first_seconds-035 · `ratio` → `/typography/title/area_ratio`

**What fraction of the frame area is covered by text during the first 3 seconds (peak)?**

- Why it matters: Sets a text-density limit for generated hooks.
- How to answer: Max of sum(area_ratio) over evidence.text_regions[] grouped by t_s < 3.
- Evidence required: evidence.text_regions[].area_ratio
- Challenge: Check whether backing panels were counted as text by the detector; compare with a manual crop.

### hook_first_seconds-036 · `enum` → `/typography/title/layout`

**Does the hook frame use the upper third, centre or lower third for its main text, and is the photo kept full size underneath?**

- Choices: `upper-third-photo-full`, `centre-photo-full`, `lower-third-photo-full`, `photo-shrunk-for-text`, `no-photo`
- Why it matters: Captures the title-over-photo layout that is cheap to get wrong in variants.
- How to answer: From title y_center_ratio (002) and the photo layer width on F1 at 0.0 s compared with its width at 3 s.
- Evidence required: evidence.text_regions[]; frames: F1 at 0.0 and 3.0 s
- Challenge: Check the photo width in pixels at both times; 'photo-full' requires the same width within 5%.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F5** Per-frame motion in a region (mean absolute frame difference, 0-255): ffmpeg -v error -i "$SRC" -vf "crop=iw:ih*0.15:0:0,tblend=all_mode=difference,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=$WORK/diff.txt" -an -f null -  (drop the crop for the full frame)
- **F6** Per-frame colour statistics (YMIN, YAVG, YMAX, SATAVG, HUEMED, UAVG, VAVG): ffmpeg -v error -ss T -t D -i "$SRC" -vf "signalstats,metadata=mode=print:file=$WORK/stats.txt" -an -f null -
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F9** Average colour of a region: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y,scale=1:1:flags=area,format=rgb24" -f rawvideo - | od -An -tu1
- **F10** Similarity of two frames (SSIM, 1.0 = identical): ffmpeg -i a.jpg -i b.jpg -lavfi "[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*"
- **F11** Per-frame scene-change score (finds dissolves and missed cuts): ffmpeg -v error -i "$SRC" -vf "select='gte(scene,0)',metadata=mode=print:key=lavfi.scene_score:file=$WORK/scene.txt" -an -f null -
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"
- **A3** Momentary loudness every 100 ms (LUFS): ffmpeg -v error -i "$SRC" -af "ebur128=metadata=1,ametadata=mode=print:key=lavfi.r128.M:file=$WORK/lufs_m.txt" -f null -
- **A4** Silences: ffmpeg -i "$SRC" -af "silencedetect=noise=-35dB:d=0.25" -f null - 2>&1 | grep silence_
- **A5** Side (L-R) channel loudness, which removes centre-panned voice and leaves most stereo music: replace the A3 filter with "pan=mono|c0=0.5*c0-0.5*c1,ebur128=metadata=1,ametadata=mode=print:key=lavfi.r128.M:file=$WORK/side_m.txt"; mid channel uses 0.5*c0+0.5*c1. Only meaningful for stereo sources.
- **A6** RMS level per 100 ms at 48 kHz: ffmpeg -v error -i "$SRC" -af "aresample=48000,asetnsamples=n=4800,astats=metadata=1:reset=1,ametadata=mode=print:key=lavfi.astats.Overall.RMS_level:file=$WORK/rms.txt" -f null -
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "hook_first_seconds-001", "ir_path": "/typography/title/first_frame_words", "answer_type": "integer"}, {"id": "hook_first_seconds-002", "ir_path": "/typography/title/placement", "answer_type": "object"}, {"id": "hook_first_seconds-003", "ir_path": "/typography/title/overlaps_subject", "answer_type": "enum", "choices": ["over-subject", "over-photo-not-subject", "empty-space", "separate-band", "no-title"]}, {"id": "hook_first_seconds-004", "ir_path": "/audio/narration/first_word_s", "answer_type": "seconds"}, {"id": "hook_first_seconds-005", "ir_path": "/timeline/retention_devices/-", "answer_type": "seconds"}, {"id": "hook_first_seconds-006", "ir_path": "/script/hook_pattern", "answer_type": "enum", "choices": ["question", "bold-claim", "specific-number", "contradiction", "direct-address", "visual-shock", "cold-open", "unfinished-sentence", "list-promise", "other"]}, {"id": "hook_first_seconds-007", "ir_path": "/script/hook_pattern", "answer_type": "pattern"}, {"id": "hook_first_seconds-008", "ir_path": "/typography/title/relation_to_voice", "answer_type": "enum", "choices": ["same-words", "paraphrase", "different-information", "no-spoken-hook", "no-title"]}, {"id": "hook_first_seconds-009", "ir_path": "/timeline/retention_devices/-", "answer_type": "integer"}, {"id": "hook_first_seconds-010", "ir_path": "/timeline/retention_devices/-", "answer_type": "boolean"}, {"id": "hook_first_seconds-011", "ir_path": "/audio/narration/lead_in_ms", "answer_type": "ms"}, {"id": "hook_first_seconds-012", "ir_path": "/audio/sfx/-", "answer_type": "boolean"}, {"id": "hook_first_seconds-013", "ir_path": "/audio/music/entry", "answer_type": "enum", "choices": ["from-start", "under-hook", "after-hook", "no-music"]}, {"id": "hook_first_seconds-014", "ir_path": "/typography/title/hold_s", "answer_type": "seconds"}, {"id": "hook_first_seconds-015", "ir_path": "/motion/text_animations/-", "answer_type": "enum", "choices": ["pop-overshoot", "scale-up", "slide", "type-on", "fade", "already-present", "other"]}, {"id": "hook_first_seconds-016", "ir_path": "/typography/title/color", "answer_type": "object"}, {"id": "hook_first_seconds-017", "ir_path": "/typography/title/size_ratio", "answer_type": "ratio"}, {"id": "hook_first_seconds-018", "ir_path": "/script/hook_pattern", "answer_type": "boolean"}, {"id": "hook_first_seconds-019", "ir_path": "/typography/title/thumbnail_legible", "answer_type": "boolean"}, {"id": "hook_first_seconds-020", "ir_path": "/typography/title/contrast_ratio", "answer_type": "number"}, {"id": "hook_first_seconds-021", "ir_path": "/visual/subject_framing", "answer_type": "ratio"}, {"id": "hook_first_seconds-022", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "hook_first_seconds-023", "ir_path": "/audio/narration/hook_wpm", "answer_type": "object"}, {"id": "hook_first_seconds-024", "ir_path": "/audio/narration/hook_loudness_delta_db", "answer_type": "number"}, {"id": "hook_first_seconds-025", "ir_path": "/timeline/retention_devices/-", "answer_type": "object"}, {"id": "hook_first_seconds-026", "ir_path": "/script/hook_pattern", "answer_type": "boolean"}, {"id": "hook_first_seconds-027", "ir_path": "/timeline/beats/*/end_ratio", "answer_type": "seconds"}, {"id": "hook_first_seconds-028", "ir_path": "/typography/labels/series_tag", "answer_type": "boolean"}, {"id": "hook_first_seconds-029", "ir_path": "/typography/title/cover_frame", "answer_type": "boolean"}, {"id": "hook_first_seconds-030", "ir_path": "/motion/camera_moves/-", "answer_type": "number"}, {"id": "hook_first_seconds-031", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "hook_first_seconds-032", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "hook_first_seconds-033", "ir_path": "/typography/captions/first_caption_s", "answer_type": "object"}, {"id": "hook_first_seconds-034", "ir_path": "/timeline/retention_devices/-", "answer_type": "timestamps"}, {"id": "hook_first_seconds-035", "ir_path": "/typography/title/area_ratio", "answer_type": "ratio"}, {"id": "hook_first_seconds-036", "ir_path": "/typography/title/layout", "answer_type": "enum", "choices": ["upper-third-photo-full", "centre-photo-full", "lower-third-photo-full", "photo-shrunk-for-text", "no-photo"]}]
```
