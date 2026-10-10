# Video RE question bank: Camera and virtual camera motion

Lens `camera_motion` · 33 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-camera-motion` subagent and challenged by `video-re-challenger`.

Lifts real and virtual camera moves (Ken Burns zooms, pans, punch-ins, parallax, shake) with speeds, easing and alternation rules.

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
- `ms`: {"value": n, "unit": "ms"} optionally with "min"/"max"; signed when an offset (negative = earlier)
- `range`: {"value": typical, "min": a, "max": b, "unit": "..."}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `timestamps`: array of seconds from the start of the source
- `parameter`: one IR parameter object (name, type, description, default, min/max or choices, derived_from)
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[].camera.pan_x, pan_y, zoom (video_re_camera_motion)
- shots[].motion_energy (video_re_motion_energy)

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_ken_burns`, `video_re_detect_zoom_punch_in`, `video_re_detect_whip_pan`, `video_re_detect_camera_shake`, `video_re_detect_motion_blur`, `video_re_detect_parallax_depth_layers`, `video_re_detect_easing_profile`, `video_re_detect_speed_ramp_freeze`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F1 at the first and last frame of a shot to measure scale change; F8 for punch-ins and shake; F5 on a corner region.

## Pitfalls challengers check first

- Reading subject motion inside footage as camera motion
- Estimating zoom from text that animates separately
- Stating a speed without the shot duration it was measured over

## Parameters this lens usually proposes

- zoom_per_s (range)
- zoom_alternate (boolean)
- punch_in_scale
- parallax_ratio
- shake_px

## IR paths this lens writes

- `/generation_rules/-` (11)
- `/motion/camera_moves/-` (15)
- `/motion/easing` (1)
- `/motion/transitions/-` (1)
- `/parameters/-` (2)
- `/visual/layers/*/motion` (3)

## Questions (33)

### camera_motion-001 · `ratio` → `/motion/camera_moves/-`

**What share of shots have camera or virtual-camera motion (zoom, pan, tilt, rotation)?**

- Why it matters: Sets how often the renderer applies a move.
- How to answer: From evidence.shots[].camera (video_re_camera_motion: zoom is the natural-log scale change per second, pan_x/pan_y are frame widths/heights per second), count shots with |zoom| > 0.01 or |pan_x| or |pan_y| > 0.01; confirm on F1 at shot start and end for 5 shots.
- Evidence required: evidence.shots[].camera; frames: F1 at shot start and end
- Challenge: Check the camera estimator on a shot where the subject moves but the frame does not; subject motion must not count.

### camera_motion-002 · `object` → `/motion/camera_moves/-`

**Which move types occur and how often (push-in, pull-out, pan left, pan right, tilt up, tilt down, rotate, parallax, shake, static)?**

- Why it matters: Lists moves for the motion vocabulary with weights.
- How to answer: Classify each shot from camera.zoom sign and pan direction; verify ambiguous ones with F1 first/last frame.
- Evidence required: evidence.shots[].camera
- Challenge: A combined zoom and pan must be classified once with both components, not counted twice.

### camera_motion-003 · `range` → `/motion/camera_moves/-`

**How fast are zooms (scale change per second, median and range)?**

- Why it matters: Becomes the zoom_per_s parameter.
- How to answer: For zoom shots, scale change per second = exp(camera.zoom) - 1 (camera.zoom is already a log rate per second); cross-check by measuring a feature width on F1 at shot start and end: (w_end / w_start)^(1 / duration_s) - 1.
- Evidence required: evidence.shots[].camera.zoom; evidence.shots[].duration_s; frames: F1 start/end
- Challenge: Recompute one shot manually from pixel widths; disagreement above 30% questions the estimator.

### camera_motion-004 · `ratio` → `/generation_rules/-`

**Do zoom directions alternate between consecutive shots (in, out, in, out)?**

- Why it matters: Becomes the zoom_alternate rule.
- How to answer: Write the sign sequence of evidence.shots[].camera.zoom (positive = zoom in); count sign alternations / consecutive pairs.
- Evidence required: evidence.shots[].camera.zoom
- Challenge: Static shots break the sequence; say how they were treated.

### camera_motion-005 · `enum` → `/motion/easing`

**What easing do moves use (linear, ease-in-out, ease-out, ease-in)?**

- Choices: `linear`, `ease-in-out`, `ease-out`, `ease-in`, `mixed`
- Why it matters: Fills motion.easing.
- How to answer: For 3 moving shots, measure a feature position or width on F8-style frames at 0%, 25%, 50%, 75%, 100% of the shot; compare increments (equal = linear).
- Evidence required: frames: 5 samples per shot in 3 shots
- Challenge: Short shots (under 1 s) cannot show easing reliably; exclude them.

### camera_motion-006 · `object` → `/motion/camera_moves/-`

**Are there punch-ins (instant scale jumps within a shot or on a cut to the same framing) and when do they occur?**

- Why it matters: Adds punch-in emphasis to the motion list with timing.
- How to answer: F10 SSIM across cuts with similar content, or frame steps (F8) showing a one-frame scale change; list timestamps and scale factor.
- Evidence required: frames: F8; frames: F10
- Challenge: Check that a punch-in is not a cut to a different crop of a new asset.

### camera_motion-007 · `object` → `/motion/camera_moves/-`

**Is there camera shake, and what are its amplitude (px) and rough frequency?**

- Why it matters: Adds a shake effect with parameters.
- How to answer: Track a fixed point across F8 frames (0.5 s); record max displacement and oscillations per second.
- Evidence required: frames: F8 over 0.5 s
- Challenge: Handheld footage shake belongs to the footage; say whether it was added in edit (it appears on stills or graphics).

### camera_motion-008 · `range` → `/motion/camera_moves/-`

**How fast are pans as a fraction of frame width per second?**

- Why it matters: Becomes the pan speed parameter.
- How to answer: Read evidence.shots[].camera.pan_x (already frame widths per second); cross-check one shot by tracking a feature on F1 at start and end: displacement_px / width / duration_s.
- Evidence required: evidence.shots[].camera.pan_x; evidence.source.width
- Challenge: Check the sign convention (positive pan_x = camera moves right, content travels left) and that the feature track agrees within 30%.

### camera_motion-009 · `ms` → `/generation_rules/-`

**Does the move start right at the cut or after a delay?**

- Why it matters: Sets a move start offset.
- How to answer: F8 over the first 0.5 s of 4 moving shots; find the first frame where the feature moves.
- Evidence required: frames: F8 at shot starts
- Challenge: Convert frames to ms with the true fps from A7.

### camera_motion-010 · `ratio` → `/generation_rules/-`

**Does motion continue across cuts (the next shot keeps the same direction and speed)?**

- Why it matters: Becomes a motion-matching rule.
- How to answer: Compare direction and speed of moves in adjacent shots.
- Evidence required: evidence.shots[].camera
- Challenge: Alternating zooms (004) and matched motion are opposite rules; the answers must be consistent.

### camera_motion-011 · `enum` → `/motion/camera_moves/-`

**Is motion filmed (real camera) or virtual (Ken Burns on stills), or both?**

- Choices: `filmed`, `virtual`, `both`
- Why it matters: Decides whether the renderer needs footage or can animate stills.
- How to answer: On moving shots, check for parallax between near and far objects (filmed) versus a uniform scale of a flat image (virtual), using F1 start and end.
- Evidence required: frames: F1 start/end
- Challenge: 2.5D parallax on stills mimics filmed motion; look for cut-out edges.

### camera_motion-012 · `number` → `/visual/layers/*/motion`

**Do different layers move at different speeds (parallax), and what is the speed ratio between foreground and background?**

- Why it matters: Fills parallax_ratio for 2.5D renders.
- How to answer: Track a background feature and a foreground feature across the same shot; ratio of displacements.
- Evidence required: frames: F1 start/end of parallax shots
- Challenge: Make sure the foreground is not moving on its own (animation) rather than with the camera.

### camera_motion-013 · `object` → `/motion/camera_moves/-`

**Are rotations used, and how many degrees over how long?**

- Why it matters: Adds a rotation range to the move vocabulary.
- How to answer: Measure the angle of a straight edge on F1 at shot start and end.
- Evidence required: frames: F1 start/end
- Challenge: Report measured degrees; 'slight rotation' alone is rejected.

### camera_motion-014 · `ratio` → `/generation_rules/-`

**Are move starts or speed changes aligned with music onsets?**

- Why it matters: Becomes a sync rule for motion keyframes.
- How to answer: Compare move start times (009) or punch-in times (006) with evidence.audio.onsets_s; share within 80 ms.
- Evidence required: move times; evidence.audio.onsets_s
- Challenge: Compare with the chance rate given onset density.

### camera_motion-015 · `number` → `/parameters/-`

**What is the maximum zoom factor reached on any shot?**

- Why it matters: Bounds zoom so assets are not over-enlarged.
- How to answer: Max over shots of exp(|camera.zoom| x duration_s), the total scale change across the shot.
- Evidence required: evidence.shots[].camera.zoom
- Challenge: Check the extreme shot by eye; estimators overshoot on blurry frames.

### camera_motion-016 · `enum` → `/generation_rules/-`

**Where are zooms centred (subject face, frame centre, text, a detail being explained)?**

- Choices: `subject`, `frame-centre`, `text`, `detail`, `varies`
- Why it matters: Becomes the zoom focus rule.
- How to answer: Find the fixed point of the zoom by comparing feature positions between start and end frames.
- Evidence required: frames: F1 start/end
- Challenge: Check at least 4 shots before naming a rule.

### camera_motion-017 · `boolean` → `/motion/camera_moves/-`

**Is motion blur visible during fast moves?**

- Why it matters: Tells the renderer to add motion blur on fast virtual moves.
- How to answer: F8 frames during the fastest move; look for directional smearing compared with a static frame.
- Evidence required: frames: F8 during fast moves
- Challenge: Compression blocks on fast motion are not motion blur; check edge direction.

### camera_motion-018 · `timestamps` → `/motion/camera_moves/-`

**Are there speed ramps or slow-motion segments?**

- Why it matters: Adds time remapping to the motion vocabulary.
- How to answer: Compare motion speed of the same subject across frames; look for sudden slow-down (F5 difference drops while motion continues).
- Evidence required: F5; frames: F8
- Challenge: A slow virtual zoom is not slow motion; ramps change the speed of filmed action.

### camera_motion-019 · `boolean` → `/generation_rules/-`

**Does camera motion pause or slow while dense text is on screen?**

- Why it matters: Becomes a readability rule for moves.
- How to answer: Compare camera speed in shots with text area_ratio above 0.1 against shots with less text.
- Evidence required: evidence.shots[].camera; evidence.text_regions[]
- Challenge: Report the two group medians and their sizes.

### camera_motion-020 · `number` → `/generation_rules/-`

**Is the hook shot's move stronger (faster or larger) than body moves?**

- Why it matters: Becomes a hook-intensity multiplier.
- How to answer: Ratio of hook zoom_per_s to body median zoom_per_s.
- Evidence required: evidence.shots[].camera; hook beat
- Challenge: One hook shot is a single sample; confidence must reflect that.

### camera_motion-021 · `boolean` → `/motion/camera_moves/-`

**Are there 3D camera moves through layered 2.5D scenes (dolly through cut-out planes)?**

- Why it matters: Adds a 2.5D dolly option.
- How to answer: Look for layers scaling at different rates during one move (F1 start/end).
- Evidence required: frames: F1 start/end
- Challenge: Different-rate scaling can also be separate animations; require consistent depth ordering.

### camera_motion-022 · `object` → `/motion/transitions/-`

**Are whip pans used as transitions, and how long are they?**

- Why it matters: Adds whip transitions with a duration.
- How to answer: F8 across cuts with heavy directional blur; count frames of blur.
- Evidence required: frames: F8 across cuts
- Challenge: Must show directional blur on at least 2 frames.

### camera_motion-023 · `boolean` → `/motion/camera_moves/-`

**Is there a simulated handheld drift (slow low-amplitude wander) on stills or graphics?**

- Why it matters: Adds a subtle drift effect.
- How to answer: Track a feature on F1 frames every 0.5 s across a graphic shot; non-linear wander of a few px suggests drift.
- Evidence required: frames: F1 every 0.5 s
- Challenge: Linear motion is a pan, not drift.

### camera_motion-024 · `object` → `/generation_rules/-`

**Is there a dominant pan direction (left to right versus right to left) and does it carry meaning (timeline, progress)?**

- Why it matters: Becomes a direction rule.
- How to answer: Count pan directions from camera.pan_x signs.
- Evidence required: evidence.shots[].camera.pan_x
- Challenge: Report counts; meaning is inferred and must say so.

### camera_motion-025 · `boolean` → `/visual/layers/*/motion`

**Does the background layer move independently of the foreground (separate virtual cameras)?**

- Why it matters: Fills per-layer motion fields.
- How to answer: Compare border-region motion (evidence.shots[].motion_energy.border, F5 on edges) with foreground scale change.
- Evidence required: evidence.shots[].motion_energy; F5
- Challenge: A moving background video naturally moves independently; say whether it is a camera move or footage motion.

### camera_motion-026 · `object` → `/generation_rules/-`

**What share of runtime is static (no camera or virtual camera motion), and where do static shots fall?**

- Why it matters: Sets where the generator may hold still.
- How to answer: Sum durations of shots classified static in 002 / duration; list their beat roles.
- Evidence required: evidence.shots[]; move classification
- Challenge: Check one static shot with F5 to confirm no slow zoom was missed.

### camera_motion-027 · `rule` → `/generation_rules/-`

**Write the Ken Burns rule per shot (start scale, end scale, direction policy, focus point) in terms of parameters.**

- Why it matters: Gives the compiler a procedural move plan.
- How to answer: Combine 003, 004, 016 and 015, for example 'scale 1.00 to 1.00 + zoom_per_s x shot_s, alternate in/out, centred on subject, max zoom_max'.
- Evidence required: camera lens answers
- Challenge: Apply the rule to 3 observed shots; the predicted end scale must be within 0.03 of the measured one.

### camera_motion-028 · `parameter` → `/parameters/-`

**What range should zoom_per_s take, justified by the observed spread?**

- Why it matters: Turns observed speeds into a parameter with an evidence-based range.
- How to answer: Default = observed median; min/max = observed p25/p75; derived_from camera_motion-003.
- Evidence required: zoom speeds
- Challenge: A range wider than observed must be marked assumed.

### camera_motion-029 · `number` → `/motion/camera_moves/-`

**What is the median absolute zoom change per second across all shots from the camera estimator?**

- Why it matters: A single motion-intensity number for fidelity scoring.
- How to answer: Median of |evidence.shots[].camera.zoom| over shots with a non-null estimate (log scale change per second).
- Evidence required: evidence.shots[].camera.zoom; evidence.shots[].duration_s
- Challenge: Recompute from evidence.

### camera_motion-030 · `boolean` → `/generation_rules/-`

**Does any move push the subject or text out of the safe area?**

- Why it matters: Becomes a constraint on move size near frame edges.
- How to answer: Check end frames of moving shots against the safe box used by the platform lens.
- Evidence required: frames: F1 at shot ends; evidence.safe_area.violations
- Challenge: Cross-check with safe_area.violations timestamps.

### camera_motion-031 · `enum` → `/motion/camera_moves/-`

**Do moves follow a subject (tracking) or a fixed path regardless of content?**

- Choices: `tracking`, `fixed-path`, `mixed`
- Why it matters: Decides whether the renderer needs subject detection for moves.
- How to answer: Check whether the subject stays at the same frame position during moves in filmed shots.
- Evidence required: frames: F1 start/middle/end
- Challenge: Virtual moves on stills are fixed-path by definition unless the focus point changes.

### camera_motion-032 · `boolean` → `/motion/camera_moves/-`

**Is there a final pull-back or reveal move in the last shots?**

- Why it matters: Adds an ending move to the outro.
- How to answer: Inspect camera.zoom on the last 2 shots and F1 start/end frames.
- Evidence required: evidence.shots[-2:].camera; frames: F1
- Challenge: Make sure the move is not the same alternating pattern as all other shots.

### camera_motion-033 · `enum` → `/visual/layers/*/motion`

**Are moves applied to the whole frame or only to inset media inside a fixed layout?**

- Choices: `whole-frame`, `inset-only`, `both`
- Why it matters: Tells the renderer which layer receives the move.
- How to answer: Check whether text, borders and backgrounds stay fixed while the photo moves (F1 start/end).
- Evidence required: frames: F1 start/end
- Challenge: Look at the frame edges and text positions in both frames.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F5** Per-frame motion in a region (mean absolute frame difference, 0-255): ffmpeg -v error -i "$SRC" -vf "crop=iw:ih*0.15:0:0,tblend=all_mode=difference,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=$WORK/diff.txt" -an -f null -  (drop the crop for the full frame)
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F10** Similarity of two frames (SSIM, 1.0 = identical): ffmpeg -i a.jpg -i b.jpg -lavfi "[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*"
- **A7** Stream facts: ffprobe -v error -show_streams -show_format -of json "$SRC"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "camera_motion-001", "ir_path": "/motion/camera_moves/-", "answer_type": "ratio"}, {"id": "camera_motion-002", "ir_path": "/motion/camera_moves/-", "answer_type": "object"}, {"id": "camera_motion-003", "ir_path": "/motion/camera_moves/-", "answer_type": "range"}, {"id": "camera_motion-004", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "camera_motion-005", "ir_path": "/motion/easing", "answer_type": "enum", "choices": ["linear", "ease-in-out", "ease-out", "ease-in", "mixed"]}, {"id": "camera_motion-006", "ir_path": "/motion/camera_moves/-", "answer_type": "object"}, {"id": "camera_motion-007", "ir_path": "/motion/camera_moves/-", "answer_type": "object"}, {"id": "camera_motion-008", "ir_path": "/motion/camera_moves/-", "answer_type": "range"}, {"id": "camera_motion-009", "ir_path": "/generation_rules/-", "answer_type": "ms"}, {"id": "camera_motion-010", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "camera_motion-011", "ir_path": "/motion/camera_moves/-", "answer_type": "enum", "choices": ["filmed", "virtual", "both"]}, {"id": "camera_motion-012", "ir_path": "/visual/layers/*/motion", "answer_type": "number"}, {"id": "camera_motion-013", "ir_path": "/motion/camera_moves/-", "answer_type": "object"}, {"id": "camera_motion-014", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "camera_motion-015", "ir_path": "/parameters/-", "answer_type": "number"}, {"id": "camera_motion-016", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["subject", "frame-centre", "text", "detail", "varies"]}, {"id": "camera_motion-017", "ir_path": "/motion/camera_moves/-", "answer_type": "boolean"}, {"id": "camera_motion-018", "ir_path": "/motion/camera_moves/-", "answer_type": "timestamps"}, {"id": "camera_motion-019", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "camera_motion-020", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "camera_motion-021", "ir_path": "/motion/camera_moves/-", "answer_type": "boolean"}, {"id": "camera_motion-022", "ir_path": "/motion/transitions/-", "answer_type": "object"}, {"id": "camera_motion-023", "ir_path": "/motion/camera_moves/-", "answer_type": "boolean"}, {"id": "camera_motion-024", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "camera_motion-025", "ir_path": "/visual/layers/*/motion", "answer_type": "boolean"}, {"id": "camera_motion-026", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "camera_motion-027", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "camera_motion-028", "ir_path": "/parameters/-", "answer_type": "parameter"}, {"id": "camera_motion-029", "ir_path": "/motion/camera_moves/-", "answer_type": "number"}, {"id": "camera_motion-030", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "camera_motion-031", "ir_path": "/motion/camera_moves/-", "answer_type": "enum", "choices": ["tracking", "fixed-path", "mixed"]}, {"id": "camera_motion-032", "ir_path": "/motion/camera_moves/-", "answer_type": "boolean"}, {"id": "camera_motion-033", "ir_path": "/visual/layers/*/motion", "answer_type": "enum", "choices": ["whole-frame", "inset-only", "both"]}]
```
