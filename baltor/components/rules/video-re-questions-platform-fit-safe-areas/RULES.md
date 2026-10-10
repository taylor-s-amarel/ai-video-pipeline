# Video RE question bank: Platform fit and safe areas

Lens `platform_fit_safe_areas` · 30 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-platform-fit-safe-areas` subagent and challenged by `video-re-challenger`.

Checks aspect, resolution, frame rate, encoding, loudness, safe-area use and sound-off readability, and records them as render settings and constraints.

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
- `ratio`: {"value": r} with 0 <= r <= 1
- `seconds`: {"value": s, "unit": "s"} optionally with "min"/"max"
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `text`: one technique description, at most 300 characters, no copied content
- `list`: array of short strings (technique names or kinds)
- `segments`: [{"start_s": a, "end_s": b, "label": "..."}]
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- source.* (video_re_probe_metadata)
- safe_area.violations (video_re_safe_area_probe)
- text_regions[]
- audio.integrated_lufs

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_safe_margin_usage`, `video_re_detect_letterbox_pillarbox`, `video_re_detect_frame_rate_cadence`, `video_re_detect_interlacing`, `video_re_detect_color_range_space`, `video_re_detect_compression_blockiness`, `video_re_detect_true_resolution`, `video_re_detect_static_overlay_regions`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

A7 stream facts; F1 frames with a safe-area overlay drawn by drawbox; F12 black frames; F6 YAVG series for flashes.

## Pitfalls challengers check first

- Stating platform limits from memory; check current platform documentation and cite it, or say 'not checked'
- Treating a safe-area template from one app as universal
- Ignoring that the source may be a re-encode

## Parameters this lens usually proposes

- target_platforms (list)
- aspect (enum)
- fps (number)
- safe_box (object)
- target_lufs (number)

## IR paths this lens writes

- `/generation_rules/-` (9)
- `/parameters/-` (1)
- `/render_binding/mapping/audio_layout` (1)
- `/render_binding/mapping/av_duration_delta_s` (1)
- `/render_binding/mapping/color_tags` (1)
- `/render_binding/mapping/duration_constraints` (1)
- `/render_binding/mapping/gop_s` (1)
- `/render_binding/mapping/loudness_target_delta_lu` (1)
- `/render_binding/mapping/reframe_16x9` (1)
- `/render_binding/mapping/reframe_ok` (1)
- `/render_binding/mapping/source_is_reencode` (1)
- `/render_binding/mapping/text_margins_px` (1)
- `/render_binding/mapping/variable_frame_rate` (1)
- `/render_binding/mapping/video_format` (1)
- `/source/fps` (1)
- `/source/platform` (1)
- `/source/resolution` (1)
- `/typography/captions/burned_in` (1)
- `/typography/captions/cap_height_px_at_1080w` (1)
- `/typography/captions/sound_off_coverage` (1)
- `/typography/labels/handle_slot` (1)
- `/visual/safe_area_respected` (1)

## Questions (30)

### platform_fit_safe_areas-001 · `object` → `/source/resolution`

**What are the resolution and display aspect ratio?**

- Why it matters: Fills source.resolution and visual.aspect.
- How to answer: evidence.source.width and height (video_re_probe_metadata); check A7 for sample_aspect_ratio and rotation side data.
- Evidence required: evidence.source.width; evidence.source.height; A7
- Challenge: A rotation tag can swap width and height; confirm on an F1 frame.

### platform_fit_safe_areas-002 · `number` → `/source/fps`

**What is the average frame rate in frames per second?**

- Why it matters: Fills source.fps and the render frame rate.
- How to answer: evidence.source.fps (avg_frame_rate); compare with r_frame_rate in A7 and report both in the note.
- Evidence required: evidence.source.fps; A7
- Challenge: Different r_frame_rate and avg_frame_rate indicate variable frame rate; say so.

### platform_fit_safe_areas-003 · `object` → `/render_binding/mapping/duration_constraints`

**Which duration band does the video fit, and which platform limits should be checked against current platform documentation?**

- Why it matters: Records duration constraints without stating platform limits from memory.
- How to answer: Report source.duration_s; list platforms the user targets and mark each limit 'check current docs' unless a citation is supplied in the run.
- Evidence required: evidence.source.duration_s
- Challenge: Any platform limit stated without a dated source is rejected.

### platform_fit_safe_areas-004 · `boolean` → `/visual/safe_area_respected`

**Which safe-area violations did the probe report, and are they real?**

- Why it matters: Fills visual.safe_area_respected.
- How to answer: Read evidence.safe_area.violations (video_re_safe_area_probe); inspect F1 frames at 3 violation times with a drawbox overlay of the template.
- Evidence required: evidence.safe_area.violations; frames: F1 with drawbox
- Challenge: Name the template the probe used; violations from watermark regions are not format violations.

### platform_fit_safe_areas-005 · `ratio` → `/generation_rules/-`

**Is any text placed in the bottom 20% of the frame?**

- Why it matters: Becomes a placement constraint (many vertical apps draw captions and controls there).
- How to answer: evidence.text_regions[] with bbox bottom beyond 0.8 x height.
- Evidence required: evidence.text_regions[].bbox
- Challenge: Treat the 20% figure as a working template, not a platform specification.

### platform_fit_safe_areas-006 · `ratio` → `/generation_rules/-`

**Is any text placed in the right-hand 15% of the frame?**

- Why it matters: Becomes a placement constraint for side action buttons.
- How to answer: evidence.text_regions[] with bbox right edge beyond 0.85 x width.
- Evidence required: evidence.text_regions[].bbox
- Challenge: Same caveat as 005.

### platform_fit_safe_areas-007 · `boolean` → `/generation_rules/-`

**Is the top 10% kept free of important content?**

- Why it matters: Becomes a top margin constraint.
- How to answer: text_regions and subject positions in the top band.
- Evidence required: evidence.text_regions[]; frames: F1
- Challenge: Report what occupies the band if anything.

### platform_fit_safe_areas-008 · `object` → `/render_binding/mapping/reframe_ok`

**Would the important content survive a centre crop to 4:5 and to 1:1?**

- Why it matters: Decides whether variants can be re-framed for other placements.
- How to answer: Overlay 4:5 and 1:1 centre boxes on 5 F1 frames (drawbox); check title, captions and subject.
- Evidence required: frames: F1 with drawbox
- Challenge: Report per frame.

### platform_fit_safe_areas-009 · `boolean` → `/generation_rules/-`

**Are there letterbox or pillarbox bars?**

- Why it matters: Flags a framing error to avoid.
- How to answer: ffmpeg cropdetect over 10 s: ffmpeg -i SRC -vf cropdetect -t 10 -f null - 2>&1 | tail -3.
- Evidence required: cropdetect output
- Challenge: Dark content can trigger cropdetect; check on F1.

### platform_fit_safe_areas-010 · `object` → `/render_binding/mapping/video_format`

**What are the video codec, profile, pixel format and bitrate?**

- Why it matters: Fills render video settings.
- How to answer: A7 stream and format fields.
- Evidence required: A7
- Challenge: Copy exactly from ffprobe.

### platform_fit_safe_areas-011 · `number` → `/render_binding/mapping/loudness_target_delta_lu`

**How does integrated loudness compare with common streaming normalisation targets (difference in LU from a target the run specifies)?**

- Why it matters: Sets the loudness target for the render.
- How to answer: evidence.audio.integrated_lufs minus the target given in the run parameters; if none, report the value only.
- Evidence required: evidence.audio.integrated_lufs
- Challenge: Do not assert a platform's target from memory; cite or omit.

### platform_fit_safe_areas-012 · `object` → `/source/platform`

**Are platform UI elements, usernames or watermarks burned into the frames?**

- Why it matters: Flags re-uploads and fills source.platform as an observation; such marks never enter variants.
- How to answer: F3 crops of corners and edges at 3 times.
- Evidence required: frames: F3 corners
- Challenge: Do not name individuals; record the kind of mark and its position.

### platform_fit_safe_areas-013 · `boolean` → `/typography/captions/burned_in`

**Are captions burned in so the video can be followed with sound off?**

- Why it matters: Fills burned_in for sound-off viewing.
- How to answer: F1 frames during speech.
- Evidence required: frames: F1; evidence.audio.speech_segments
- Challenge: Check 5 speech moments.

### platform_fit_safe_areas-014 · `ratio` → `/typography/captions/sound_off_coverage`

**What share of speech time has matching on-screen text (sound-off coverage)?**

- Why it matters: Measures sound-off readability.
- How to answer: Speech segments overlapped by caption-area text regions / speech time.
- Evidence required: evidence.audio.speech_segments; evidence.text_regions[]
- Challenge: Text regions are sampled; state the sampling interval.

### platform_fit_safe_areas-015 · `boolean` → `/generation_rules/-`

**Are there interlacing or combing artefacts?**

- Why it matters: Flags a source quality issue.
- How to answer: ffmpeg idet filter over 500 frames: ffmpeg -i SRC -vf idet -frames:v 500 -an -f null - 2>&1 | grep 'Multi frame'.
- Evidence required: idet output
- Challenge: Report the counts.

### platform_fit_safe_areas-016 · `object` → `/render_binding/mapping/color_tags`

**What colour primaries, transfer and range are tagged?**

- Why it matters: Fills render colour tags.
- How to answer: A7: color_space, color_transfer, color_primaries, color_range.
- Evidence required: A7
- Challenge: Untagged streams must be reported as untagged, not as bt709.

### platform_fit_safe_areas-017 · `object` → `/render_binding/mapping/audio_layout`

**What are the audio channel layout and sample rate?**

- Why it matters: Fills render audio settings.
- How to answer: A7 audio stream.
- Evidence required: A7
- Challenge: Copy exactly.

### platform_fit_safe_areas-018 · `boolean` → `/render_binding/mapping/variable_frame_rate`

**Is the frame rate variable?**

- Why it matters: Variable frame rate affects frame-accurate measurements and renders.
- How to answer: Compare A7 r_frame_rate and avg_frame_rate; inspect pts deltas with ffprobe -show_frames on 100 frames.
- Evidence required: A7; ffprobe frames
- Challenge: Report min and max frame durations.

### platform_fit_safe_areas-019 · `object` → `/render_binding/mapping/text_margins_px`

**What are the minimum text margins in px at the source resolution?**

- Why it matters: Fills a safe box for the render template.
- How to answer: Min distance from text bboxes to each edge.
- Evidence required: evidence.text_regions[].bbox
- Challenge: Exclude watermarks.

### platform_fit_safe_areas-020 · `text` → `/render_binding/mapping/reframe_16x9`

**What changes would a 16:9 version need (re-layout, pillarbox, side panels)?**

- Why it matters: Adds a reframing plan for other aspects.
- How to answer: Inspect layout on F1 frames; propose a layout that keeps title, captions and subject; method inferred.
- Evidence required: frames: F1
- Challenge: Must not require source footage.

### platform_fit_safe_areas-021 · `boolean` → `/typography/labels/handle_slot`

**Are handles, hashtags or account names overlaid as part of the design?**

- Why it matters: Adds a handle slot (filled with the new channel's own handle) or rules it out.
- How to answer: F3 crops; describe placement and style only.
- Evidence required: frames: F3
- Challenge: Never copy the handle.

### platform_fit_safe_areas-022 · `segments` → `/generation_rules/-`

**Are there black frames at the start, the end, or anywhere else?**

- Why it matters: Flags autoplay and thumbnail problems.
- How to answer: F12 blackdetect.
- Evidence required: F12
- Challenge: Report all segments.

### platform_fit_safe_areas-023 · `number` → `/generation_rules/-`

**How many large luminance flashes per second occur at most (three per second is the WCAG 2.3.1 general flash threshold)?**

- Why it matters: An accessibility check; renders should stay under the threshold.
- How to answer: F6 YAVG per frame; count opposing changes above about 10% of full range within any 1 s window. This is a screening estimate, not a certified photosensitivity test.
- Evidence required: F6 series
- Challenge: Small-area flashes count differently under WCAG; mark the result as a screening estimate.

### platform_fit_safe_areas-024 · `number` → `/typography/captions/cap_height_px_at_1080w`

**How tall is caption text in pixels at 1080 px width (scaled from the source)?**

- Why it matters: Gives a concrete size for phone legibility.
- How to answer: Cap height (typography lens) scaled to a 1080-wide frame.
- Evidence required: cap height; evidence.source.width
- Challenge: Recompute the scaling.

### platform_fit_safe_areas-025 · `list` → `/parameters/-`

**Which platform parameters should a new video set (target platforms, aspect, fps, safe box, target loudness)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect 001, 002, 004, 011 and 019.
- Evidence required: platform answers
- Challenge: Each parameter needs derived_from.

### platform_fit_safe_areas-026 · `rule` → `/generation_rules/-`

**Write the safe-box rule for text and key subjects as fractions of width and height.**

- Why it matters: Gives the compiler a placement constraint.
- How to answer: From 005-007 and 019, for example 'text inside x 0.06-0.85, y 0.10-0.80'.
- Evidence required: platform answers
- Challenge: Check the source's own text against the rule and report violations.

### platform_fit_safe_areas-027 · `enum` → `/render_binding/mapping/source_is_reencode`

**Is the file a re-encode of an earlier upload (double compression signs, burned UI, odd bitrate)?**

- Choices: `likely-original-export`, `likely-re-encode`, `not-determinable`
- Why it matters: Calibrates trust in colour, sharpness and audio measurements.
- How to answer: A7 encoder tags, F3 crops for blocking, burned-in UI from 012; method inferred.
- Evidence required: A7; frames: F3
- Challenge: Encoder tags can be stripped; low confidence unless two cues agree.

### platform_fit_safe_areas-028 · `seconds` → `/render_binding/mapping/gop_s`

**What keyframe (GOP) interval does the file use?**

- Why it matters: Informs render settings and seek accuracy of measurements.
- How to answer: ffprobe -select_streams v -skip_frame nokey -show_entries frame=pts_time -of csv SRC | head -20; median interval.
- Evidence required: ffprobe keyframes
- Challenge: Report the first 10 keyframe times.

### platform_fit_safe_areas-029 · `seconds` → `/render_binding/mapping/av_duration_delta_s`

**Is the audio present for the whole duration, or shorter or longer than the video?**

- Why it matters: Flags sync and duration problems.
- How to answer: Compare audio and video stream durations in A7.
- Evidence required: A7
- Challenge: Report both durations.

### platform_fit_safe_areas-030 · `boolean` → `/generation_rules/-`

**Does the first frame contain the title and subject so a paused autoplay frame still communicates the topic?**

- Why it matters: Becomes a first-frame content rule.
- How to answer: F1 at 0.0 s.
- Evidence required: frames: F1 at 0.0 s
- Challenge: Cross-check with hook_first_seconds-001 and -019.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F6** Per-frame colour statistics (YMIN, YAVG, YMAX, SATAVG, HUEMED, UAVG, VAVG): ffmpeg -v error -ss T -t D -i "$SRC" -vf "signalstats,metadata=mode=print:file=$WORK/stats.txt" -an -f null -
- **F12** Black frames: ffmpeg -i "$SRC" -vf "blackdetect=d=0.05:pix_th=0.10" -an -f null - 2>&1 | grep black_
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "platform_fit_safe_areas-001", "ir_path": "/source/resolution", "answer_type": "object"}, {"id": "platform_fit_safe_areas-002", "ir_path": "/source/fps", "answer_type": "number"}, {"id": "platform_fit_safe_areas-003", "ir_path": "/render_binding/mapping/duration_constraints", "answer_type": "object"}, {"id": "platform_fit_safe_areas-004", "ir_path": "/visual/safe_area_respected", "answer_type": "boolean"}, {"id": "platform_fit_safe_areas-005", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "platform_fit_safe_areas-006", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "platform_fit_safe_areas-007", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "platform_fit_safe_areas-008", "ir_path": "/render_binding/mapping/reframe_ok", "answer_type": "object"}, {"id": "platform_fit_safe_areas-009", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "platform_fit_safe_areas-010", "ir_path": "/render_binding/mapping/video_format", "answer_type": "object"}, {"id": "platform_fit_safe_areas-011", "ir_path": "/render_binding/mapping/loudness_target_delta_lu", "answer_type": "number"}, {"id": "platform_fit_safe_areas-012", "ir_path": "/source/platform", "answer_type": "object"}, {"id": "platform_fit_safe_areas-013", "ir_path": "/typography/captions/burned_in", "answer_type": "boolean"}, {"id": "platform_fit_safe_areas-014", "ir_path": "/typography/captions/sound_off_coverage", "answer_type": "ratio"}, {"id": "platform_fit_safe_areas-015", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "platform_fit_safe_areas-016", "ir_path": "/render_binding/mapping/color_tags", "answer_type": "object"}, {"id": "platform_fit_safe_areas-017", "ir_path": "/render_binding/mapping/audio_layout", "answer_type": "object"}, {"id": "platform_fit_safe_areas-018", "ir_path": "/render_binding/mapping/variable_frame_rate", "answer_type": "boolean"}, {"id": "platform_fit_safe_areas-019", "ir_path": "/render_binding/mapping/text_margins_px", "answer_type": "object"}, {"id": "platform_fit_safe_areas-020", "ir_path": "/render_binding/mapping/reframe_16x9", "answer_type": "text"}, {"id": "platform_fit_safe_areas-021", "ir_path": "/typography/labels/handle_slot", "answer_type": "boolean"}, {"id": "platform_fit_safe_areas-022", "ir_path": "/generation_rules/-", "answer_type": "segments"}, {"id": "platform_fit_safe_areas-023", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "platform_fit_safe_areas-024", "ir_path": "/typography/captions/cap_height_px_at_1080w", "answer_type": "number"}, {"id": "platform_fit_safe_areas-025", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "platform_fit_safe_areas-026", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "platform_fit_safe_areas-027", "ir_path": "/render_binding/mapping/source_is_reencode", "answer_type": "enum", "choices": ["likely-original-export", "likely-re-encode", "not-determinable"]}, {"id": "platform_fit_safe_areas-028", "ir_path": "/render_binding/mapping/gop_s", "answer_type": "seconds"}, {"id": "platform_fit_safe_areas-029", "ir_path": "/render_binding/mapping/av_duration_delta_s", "answer_type": "seconds"}, {"id": "platform_fit_safe_areas-030", "ir_path": "/generation_rules/-", "answer_type": "boolean"}]
```
