# Video RE question bank: Pacing and cut rhythm

Lens `pacing_cut_rhythm` · 35 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-pacing-cut-rhythm` subagent and challenged by `video-re-challenger`.

Measures shot lengths, cut rate, acceleration, holds and how cuts line up with speech and music, then states them as pacing rules.

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
- `distribution`: {"median": m, "p10": a, "p90": b, "n": count, "unit": "..."}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `parameter`: one IR parameter object (name, type, description, default, min/max or choices, derived_from)
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[] start_s/end_s/duration_s (video_re_detect_shots)
- shot_stats (video_re_shot_stats)
- audio.onsets_s, audio.tempo_bpm (video_re_onsets_beats)
- audio.cuts_on_beat_ratio (video_re_cut_beat_alignment)
- audio.speech_segments

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_transition_type`, `video_re_detect_flash_frames`, `video_re_detect_speed_ramp_freeze`, `video_re_detect_tempo_changes`, `video_re_detect_silence_gaps`, `video_re_detect_frame_rate_cadence`, `video_re_detect_hook_window_density`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F11 scene scores to find dissolves and false cuts; F1 frames either side of doubtful cuts.

## Pitfalls challengers check first

- Trusting a shot detector on dissolves, flashes or fast pans
- Mixing mean and median
- Calling cuts on-beat when tempo detection failed or the tolerance is wider than half a beat
- Ignoring the hook when describing overall pacing

## Parameters this lens usually proposes

- target_median_shot_s (range)
- hook_median_shot_s
- max_static_s
- cut_on_beat (boolean)

## IR paths this lens writes

- `/audio/cuts_on_beat_ratio` (1)
- `/audio/narration/speech_gap_ms` (1)
- `/generation_rules/-` (23)
- `/motion/camera_moves/-` (1)
- `/motion/transitions/-` (3)
- `/parameters/-` (1)
- `/render_binding/mapping/measurement_precision/cut_detection` (1)
- `/timeline/cut_rate_per_min` (1)
- `/timeline/median_shot_s` (2)
- `/timeline/retention_devices/-` (1)

## Questions (35)

### pacing_cut_rhythm-001 · `seconds` → `/timeline/median_shot_s`

**What is the median shot length over the whole video?**

- Why it matters: Fills timeline.median_shot_s, the main pacing parameter.
- How to answer: Read evidence.shot_stats.median_s (video_re_shot_stats); report evidence.shot_stats.count in the note.
- Evidence required: evidence.shot_stats.median_s; evidence.shot_stats.count
- Challenge: Recompute the median from evidence.shots[].duration_s; check F11 scene scores for missed dissolves which would lengthen shots.

### pacing_cut_rhythm-002 · `number` → `/timeline/cut_rate_per_min`

**What is the cut rate in cuts per minute?**

- Why it matters: Fills timeline.cut_rate_per_min.
- How to answer: Read evidence.shot_stats.cut_rate_per_min; equivalently (count - 1) / duration_s x 60.
- Evidence required: evidence.shot_stats.cut_rate_per_min; evidence.source.duration_s
- Challenge: Recompute from count and duration; a mismatch above 5% means one of the fields is stale.

### pacing_cut_rhythm-003 · `object` → `/generation_rules/-`

**What is the median shot length in the first 10 seconds versus the rest of the video?**

- Why it matters: Captures front-loaded pacing as a two-speed rule.
- How to answer: Split evidence.shots[] by start_s < 10; report both medians and their ratio.
- Evidence required: evidence.shots[].start_s; evidence.shots[].duration_s
- Challenge: With fewer than 4 shots in the first 10 s, the first median is weak; say so.

### pacing_cut_rhythm-004 · `distribution` → `/timeline/median_shot_s`

**What is the shot-length distribution (p10, median, p90) and its coefficient of variation?**

- Why it matters: Sets the allowed spread around the target median in the compiler.
- How to answer: Compute from evidence.shots[].duration_s.
- Evidence required: evidence.shots[].duration_s
- Challenge: Recompute; exclude a first or last shot that is a leader or end card and report the difference.

### pacing_cut_rhythm-005 · `object` → `/generation_rules/-`

**Do shots get shorter or longer over the course of the video (slope of shot length against time)?**

- Why it matters: Becomes an acceleration rule or confirms constant pacing.
- How to answer: Fit duration_s against start_s with least squares; report slope in seconds of shot length per minute and the first-third versus last-third medians.
- Evidence required: evidence.shots[]
- Challenge: Check that a long end card is not driving the slope.

### pacing_cut_rhythm-006 · `ratio` → `/audio/cuts_on_beat_ratio`

**What share of cuts land on a detected musical beat?**

- Why it matters: Fills audio.cuts_on_beat_ratio.
- How to answer: Read evidence.audio.cuts_on_beat_ratio (video_re_cut_beat_alignment); report the tolerance it used and evidence.audio.tempo_bpm.
- Evidence required: evidence.audio.cuts_on_beat_ratio; evidence.audio.tempo_bpm
- Challenge: Compute the chance rate: tolerance window x 2 / beat period. A ratio near chance does not support 'cuts on beat'.

### pacing_cut_rhythm-007 · `ratio` → `/generation_rules/-`

**What share of cuts fall within 150 ms of the end of a speech segment (cutting on pauses)?**

- Why it matters: Becomes a rule to cut on speech pauses or not.
- How to answer: For each cut time (shots[].start_s, excluding 0), find the nearest speech segment end in audio.speech_segments; report the share within 150 ms.
- Evidence required: evidence.shots[]; evidence.audio.speech_segments
- Challenge: Compare with the share for randomly shifted cut times (shift all cuts by 0.7 s) to show the effect is not chance.

### pacing_cut_rhythm-008 · `ratio` → `/generation_rules/-`

**What share of cuts happen in the middle of a word (speech continues across the cut)?**

- Why it matters: Tells the editor whether picture changes are tied to words.
- How to answer: A cut is mid-speech if it falls inside a speech segment more than 100 ms from both ends; report the share.
- Evidence required: evidence.shots[]; evidence.audio.speech_segments
- Challenge: Speech segments merge short pauses; check two flagged cuts on an A1 spectrogram.

### pacing_cut_rhythm-009 · `object` → `/generation_rules/-`

**Where is the longest shot, how long is it, and what happens during it (reveal, text-heavy explanation, end card)?**

- Why it matters: Shows where the format deliberately holds.
- How to answer: Max of shots[].duration_s; inspect F2 bursts across it.
- Evidence required: evidence.shots[]; frames: F2 across the longest shot
- Challenge: Check with F11 that the longest shot is not two shots joined by a missed dissolve.

### pacing_cut_rhythm-010 · `object` → `/motion/transitions/-`

**Are there flash shots shorter than 0.25 s, how many, and what are they used for?**

- Why it matters: Adds flash accents to the effect list if deliberate.
- How to answer: Filter shots[] by duration_s < 0.25; inspect each with F8.
- Evidence required: evidence.shots[]; frames: F8 at each flash
- Challenge: Encoder artefacts and detector double-triggers produce fake short shots; each must be seen on F8.

### pacing_cut_rhythm-011 · `object` → `/generation_rules/-`

**Do shot lengths alternate (long-short-long) or follow another repeating rhythm?**

- Why it matters: Becomes a rhythm pattern in the generation rules.
- How to answer: Compute the lag-1 autocorrelation of shot durations; negative values suggest alternation. Also write the first 12 durations rounded to 0.1 s.
- Evidence required: evidence.shots[].duration_s
- Challenge: Autocorrelation on fewer than 15 shots is noisy; report n and keep confidence low.

### pacing_cut_rhythm-012 · `object` → `/generation_rules/-`

**What is the median shot length per beat role (hook, items, outro)?**

- Why it matters: Lets the compiler pace each beat role differently.
- How to answer: Assign each shot to a beat using the structure lens boundaries; compute medians per role.
- Evidence required: evidence.shots[]; timeline beats
- Challenge: Shots straddling a boundary must be assigned by majority overlap; check the rule was applied.

### pacing_cut_rhythm-013 · `number` → `/timeline/retention_devices/-`

**How many visual events per second occur when counting cuts plus text appearances plus distinct zoom or colour jumps?**

- Why it matters: Captures total visual change rate, which cut rate alone misses.
- How to answer: Merge event times: shots[].start_s, distinct text_regions t_s where a new region appears, and jumps seen on F2 bursts at 5 sampled points; divide by duration.
- Evidence required: evidence.shots[]; evidence.text_regions[]; frames: F2 samples
- Challenge: Make sure the same event is not counted twice when a cut and a caption change coincide.

### pacing_cut_rhythm-014 · `seconds` → `/generation_rules/-`

**What is the longest stretch without any visual change (no cut, no new text, no visible motion change)?**

- Why it matters: Becomes a max_static_s constraint.
- How to answer: From the merged event list (013) find the largest gap; confirm with F5 full-frame difference that motion is low during it.
- Evidence required: merged event times; F5 over the gap
- Challenge: A continuous camera move is a change; check F5 values during the gap.

### pacing_cut_rhythm-015 · `ratio` → `/generation_rules/-`

**What share of caption changes coincide with a cut (within 100 ms)?**

- Why it matters: Decides whether captions and cuts are scheduled together.
- How to answer: Compare captions[].start_s with shots[].start_s.
- Evidence required: evidence.captions[]; evidence.shots[]
- Challenge: If captions come from transcription, they are not on-screen timings; use text_regions instead or lower confidence.

### pacing_cut_rhythm-016 · `enum` → `/generation_rules/-`

**Are cuts made on action (movement continues across the cut) or on stillness?**

- Choices: `on-action`, `on-stillness`, `mixed`, `not-applicable-stills`
- Why it matters: Becomes an editing rule for motion footage.
- How to answer: Use F5 full-frame difference values in the 3 frames before each of 6 sampled cuts; high values mean on-action.
- Evidence required: F5 around sampled cuts; frames: F8 at sampled cuts
- Challenge: Virtual zooms on stills always show motion; use not-applicable-stills for photo montages.

### pacing_cut_rhythm-017 · `integer` → `/motion/transitions/-`

**How many jump cuts are there (cut between two shots with the same framing and subject)?**

- Why it matters: Adds jump cuts as a technique for presenter-led formats.
- How to answer: F10 SSIM between the last frame of each shot and the first frame of the next; values above 0.8 with a cut indicate a jump cut.
- Evidence required: frames: F10 across cuts; evidence.shots[]
- Challenge: A punch-in zoom changes framing and lowers SSIM; check flagged and unflagged pairs by eye.

### pacing_cut_rhythm-018 · `number` → `/generation_rules/-`

**On average, how many spoken phrases does one shot cover (shots per phrase)?**

- Why it matters: Becomes a rule tying shot count to script phrases.
- How to answer: Count speech segments (or caption cards) and shots; ratio = shots / phrases.
- Evidence required: evidence.shots[]; evidence.audio.speech_segments; evidence.captions[]
- Challenge: Say which unit was used for phrases; the two give different ratios.

### pacing_cut_rhythm-019 · `number` → `/generation_rules/-`

**What is the median shot length measured in musical beats at the detected tempo?**

- Why it matters: Gives a tempo-relative pacing rule that transfers to new music.
- How to answer: median_s x tempo_bpm / 60.
- Evidence required: evidence.shot_stats.median_s; evidence.audio.tempo_bpm
- Challenge: If tempo_bpm is null or the music has no clear pulse (check A1), answer 'not determinable'.

### pacing_cut_rhythm-020 · `distribution` → `/audio/narration/speech_gap_ms`

**What are the median and maximum gaps between speech segments?**

- Why it matters: Sets narration pause lengths in the TTS plan.
- How to answer: Compute gaps between consecutive audio.speech_segments.
- Evidence required: evidence.audio.speech_segments
- Challenge: Check two long gaps with A4 silencedetect; music-filled gaps may be missed by VAD.

### pacing_cut_rhythm-021 · `boolean` → `/generation_rules/-`

**Does pacing slow down before the payoff (longer shots or pauses in the last 25% before the reveal)?**

- Why it matters: Becomes a pre-payoff hold rule.
- How to answer: Compare median shot length in the 10 s before the payoff beat with the item median.
- Evidence required: evidence.shots[]; timeline beats
- Challenge: Require a change of at least 25% to call it a slow-down.

### pacing_cut_rhythm-022 · `ratio` → `/motion/transitions/-`

**What share of shot changes use a transition (dissolve, wipe, zoom) rather than a hard cut?**

- Why it matters: Sets the hard-cut default and transition frequency.
- How to answer: Use F11 scene scores: hard cuts are single-frame spikes; transitions spread over several frames. Sample at least 10 boundaries with F8.
- Evidence required: F11 scene scores; frames: F8 at sampled boundaries
- Challenge: Report the sample size; extrapolating from 3 boundaries is over-generalisation.

### pacing_cut_rhythm-023 · `boolean` → `/generation_rules/-`

**Is the first shot of each item longer than the item's other shots (a pacing reset at item start)?**

- Why it matters: Becomes a rule for item-opening shots.
- How to answer: Compare first-shot duration with the median of other shots per item.
- Evidence required: evidence.shots[]; item beat boundaries
- Challenge: Count how many items follow the pattern; under two thirds means false.

### pacing_cut_rhythm-024 · `rule` → `/generation_rules/-`

**Write the shot-count rule for a beat in terms of parameters (for example shots = ceil(beat_s / target_median_shot_s)).**

- Why it matters: Gives the compiler a procedural shot plan.
- How to answer: Fit the observed shots per beat against beat duration; propose the rule and report its error on each beat.
- Evidence required: evidence.shots[]; timeline beats
- Challenge: Recompute shots for each observed beat from the rule; errors of more than one shot on more than a third of beats reject it.

### pacing_cut_rhythm-025 · `parameter` → `/parameters/-`

**What range should target_median_shot_s have, justified by the spread observed in this video?**

- Why it matters: Turns one observation into a parameter with an evidence-based range.
- How to answer: Default = observed median; min/max = p25 and p75 of item shot lengths; derived_from = pacing_cut_rhythm-001 and -004.
- Evidence required: evidence.shots[].duration_s
- Challenge: Any range wider than the observed p10-p90 must be marked assumed.

### pacing_cut_rhythm-026 · `ms` → `/generation_rules/-`

**Does the picture change before the new sentence starts, and by how many milliseconds (cut lead)?**

- Why it matters: Sets the cut-to-voice offset in the editing rule.
- How to answer: For cuts within 400 ms of a speech segment start, compute start_speech - cut_time; report median (positive = picture leads).
- Evidence required: evidence.shots[]; evidence.audio.speech_segments
- Challenge: Speech segment onsets can lag the true onset; check two on A1.

### pacing_cut_rhythm-027 · `object` → `/generation_rules/-`

**What is the micro-timing inside an item start (for example cut at +0 ms, label at +150 ms, number at +400 ms, voice at +300 ms)?**

- Why it matters: Gives frame-accurate offsets for the per-item template.
- How to answer: F8 frame steps over the first 0.5 s of three items; convert frame indices to ms with source.fps; report the median offset per event.
- Evidence required: frames: F8 at three item starts; evidence.source.fps
- Challenge: Check the fps used for conversion matches A7 stream r_frame_rate.

### pacing_cut_rhythm-028 · `list` → `/generation_rules/-`

**What does the cut density look like across the video in 10-second windows?**

- Why it matters: Shows pacing shape (flat, peaks at items, burst in hook) for the compiler.
- How to answer: Count shot starts per 10 s window; list counts in order.
- Evidence required: evidence.shots[].start_s
- Challenge: The last window is usually partial; normalise it or mark it.

### pacing_cut_rhythm-029 · `timestamps` → `/motion/camera_moves/-`

**Are there freeze frames or speed ramps, and where?**

- Why it matters: Adds time-manipulation effects to the motion list.
- How to answer: F5 full-frame difference near zero for more than 0.5 s inside moving footage indicates a freeze; frame steps (F8) show ramps.
- Evidence required: F5; frames: F8
- Challenge: Stills with no Ken Burns also show zero difference; a freeze must follow moving footage in the same shot.

### pacing_cut_rhythm-030 · `ratio` → `/render_binding/mapping/measurement_precision/cut_detection`

**Of 10 randomly sampled detected cuts, what share are real shot changes (shot-detector precision on this video)?**

- Why it matters: Calibrates trust in shot_stats for this video.
- How to answer: Pick 10 cuts at random from evidence.shots[]; inspect F8 at each and count real shot changes (not flashes, fast pans or text pops). Report the share and list the sampled cut times in the note; the challenger lowers pacing answers built on shot counts when it is below 0.9.
- Evidence required: evidence.shots[]; frames: F8 at 10 cuts
- Challenge: Report which cuts were sampled so the check can be repeated.

### pacing_cut_rhythm-031 · `number` → `/generation_rules/-`

**What is the ratio of text-change rate to cut rate?**

- Why it matters: Tells the compiler how many caption or label changes to schedule per shot.
- How to answer: Number of distinct on-screen text changes (from text_regions) per minute divided by cut_rate_per_min.
- Evidence required: evidence.text_regions[]; evidence.shot_stats.cut_rate_per_min
- Challenge: text_regions are sampled; a change between samples may be missed. State the sampling interval.

### pacing_cut_rhythm-032 · `object` → `/generation_rules/-`

**Does pacing differ between narrated stretches and stretches with no narration?**

- Why it matters: Becomes a rule for music-only segments.
- How to answer: Median shot length for shots mostly inside speech segments versus mostly outside.
- Evidence required: evidence.shots[]; evidence.audio.speech_segments
- Challenge: If narration covers more than 90% of the runtime, the second group is too small; say so.

### pacing_cut_rhythm-033 · `seconds` → `/generation_rules/-`

**How long is the final shot?**

- Why it matters: Sets the end hold.
- How to answer: Last element of evidence.shots[] duration_s.
- Evidence required: evidence.shots[-1].duration_s
- Challenge: Check against the dead-tail answer in the structure lens.

### pacing_cut_rhythm-034 · `ratio` → `/generation_rules/-`

**Is the median cut interval close to an integer multiple of the music beat period?**

- Why it matters: Becomes a rule to quantise shot lengths to beats.
- How to answer: Compute cut intervals modulo the beat period (60 / tempo_bpm); report the share within 15% of a beat of a multiple.
- Evidence required: evidence.shots[]; evidence.audio.tempo_bpm
- Challenge: Report the chance rate for the same tolerance (0.3 for 15% either side); a share near it is not evidence.

### pacing_cut_rhythm-035 · `distribution` → `/generation_rules/-`

**What is the minimum time any text card stays on screen per word shown on it (ms per word)?**

- Why it matters: Sets a readability floor for text holds.
- How to answer: For caption or label cards, divide on-screen duration (text_regions first to last t_s, or captions[] end_s - start_s) by word count; report min and median.
- Evidence required: evidence.text_regions[]; evidence.captions[]
- Challenge: Word-by-word highlighted captions keep the card while words change; use card duration, not word duration.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F5** Per-frame motion in a region (mean absolute frame difference, 0-255): ffmpeg -v error -i "$SRC" -vf "crop=iw:ih*0.15:0:0,tblend=all_mode=difference,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=$WORK/diff.txt" -an -f null -  (drop the crop for the full frame)
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F10** Similarity of two frames (SSIM, 1.0 = identical): ffmpeg -i a.jpg -i b.jpg -lavfi "[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*"
- **F11** Per-frame scene-change score (finds dissolves and missed cuts): ffmpeg -v error -i "$SRC" -vf "select='gte(scene,0)',metadata=mode=print:key=lavfi.scene_score:file=$WORK/scene.txt" -an -f null -
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"
- **A4** Silences: ffmpeg -i "$SRC" -af "silencedetect=noise=-35dB:d=0.25" -f null - 2>&1 | grep silence_
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "pacing_cut_rhythm-001", "ir_path": "/timeline/median_shot_s", "answer_type": "seconds"}, {"id": "pacing_cut_rhythm-002", "ir_path": "/timeline/cut_rate_per_min", "answer_type": "number"}, {"id": "pacing_cut_rhythm-003", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "pacing_cut_rhythm-004", "ir_path": "/timeline/median_shot_s", "answer_type": "distribution"}, {"id": "pacing_cut_rhythm-005", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "pacing_cut_rhythm-006", "ir_path": "/audio/cuts_on_beat_ratio", "answer_type": "ratio"}, {"id": "pacing_cut_rhythm-007", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "pacing_cut_rhythm-008", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "pacing_cut_rhythm-009", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "pacing_cut_rhythm-010", "ir_path": "/motion/transitions/-", "answer_type": "object"}, {"id": "pacing_cut_rhythm-011", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "pacing_cut_rhythm-012", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "pacing_cut_rhythm-013", "ir_path": "/timeline/retention_devices/-", "answer_type": "number"}, {"id": "pacing_cut_rhythm-014", "ir_path": "/generation_rules/-", "answer_type": "seconds"}, {"id": "pacing_cut_rhythm-015", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "pacing_cut_rhythm-016", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["on-action", "on-stillness", "mixed", "not-applicable-stills"]}, {"id": "pacing_cut_rhythm-017", "ir_path": "/motion/transitions/-", "answer_type": "integer"}, {"id": "pacing_cut_rhythm-018", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "pacing_cut_rhythm-019", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "pacing_cut_rhythm-020", "ir_path": "/audio/narration/speech_gap_ms", "answer_type": "distribution"}, {"id": "pacing_cut_rhythm-021", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "pacing_cut_rhythm-022", "ir_path": "/motion/transitions/-", "answer_type": "ratio"}, {"id": "pacing_cut_rhythm-023", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "pacing_cut_rhythm-024", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "pacing_cut_rhythm-025", "ir_path": "/parameters/-", "answer_type": "parameter"}, {"id": "pacing_cut_rhythm-026", "ir_path": "/generation_rules/-", "answer_type": "ms"}, {"id": "pacing_cut_rhythm-027", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "pacing_cut_rhythm-028", "ir_path": "/generation_rules/-", "answer_type": "list"}, {"id": "pacing_cut_rhythm-029", "ir_path": "/motion/camera_moves/-", "answer_type": "timestamps"}, {"id": "pacing_cut_rhythm-030", "ir_path": "/render_binding/mapping/measurement_precision/cut_detection", "answer_type": "ratio"}, {"id": "pacing_cut_rhythm-031", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "pacing_cut_rhythm-032", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "pacing_cut_rhythm-033", "ir_path": "/generation_rules/-", "answer_type": "seconds"}, {"id": "pacing_cut_rhythm-034", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "pacing_cut_rhythm-035", "ir_path": "/generation_rules/-", "answer_type": "distribution"}]
```
