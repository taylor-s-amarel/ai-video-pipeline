# Video RE question bank: Characters and animation style

Lens `characters_animation_style` · 32 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-characters-animation-style` subagent and challenged by `video-re-challenger`.

Classifies the visual style family and, when characters or drawn elements appear, lifts their construction, frame rate, poses, lip sync and secondary motion.

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
- `ms`: {"value": n, "unit": "ms"} optionally with "min"/"max"; signed when an offset (negative = earlier)
- `distribution`: {"median": m, "p10": a, "p90": b, "n": count, "unit": "..."}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `list`: array of short strings (technique names or kinds)
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[].keyframe
- shots[].motion_energy

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_classify_animation_style`, `video_re_classify_flat_vs_photographic`, `video_re_detect_frame_rate_cadence`, `video_re_detect_parallax_depth_layers`, `video_re_detect_paper_halftone_texture`, `video_re_detect_easing_profile`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F8 frame steps to count unique drawings per second; F3 crops for line weight and fill; F2 bursts for cycles.

## Pitfalls challengers check first

- Calling footage 'animation' because it is stylised
- Measuring frame holds over a section where the camera also moves
- Naming the tool used to make it as fact; it is inferred

## Parameters this lens usually proposes

- style_family (enum)
- character_rig (asset)
- animation_fps (enum)
- line_weight_px
- lip_sync (enum)

## IR paths this lens writes

- `/generation_rules/-` (4)
- `/motion/easing` (1)
- `/parameters/-` (1)
- `/render_binding/mapping/animation_fps` (1)
- `/render_binding/mapping/blink_per_min` (1)
- `/render_binding/mapping/character_entrance` (1)
- `/render_binding/mapping/contact_shadow` (1)
- `/render_binding/mapping/expressions` (1)
- `/render_binding/mapping/fill_style` (1)
- `/render_binding/mapping/hold_ms` (1)
- `/render_binding/mapping/impact_pause_ms` (1)
- `/render_binding/mapping/line_style` (1)
- `/render_binding/mapping/lip_sync` (1)
- `/render_binding/mapping/motion_cues` (1)
- `/render_binding/mapping/physics` (1)
- `/render_binding/mapping/pose_count` (1)
- `/render_binding/mapping/projection` (1)
- `/render_binding/mapping/proportions` (1)
- `/render_binding/mapping/renderer_hint` (1)
- `/render_binding/mapping/secondary_motion` (1)
- `/render_binding/mapping/squash_stretch` (1)
- `/render_binding/mapping/walk_cycle_frames` (1)
- `/timeline/beats/*/content_slot` (1)
- `/typography/labels/diegetic` (1)
- `/visual/layers` (1)
- `/visual/layers/-` (2)
- `/visual/style_family` (2)

## Questions (32)

### characters_animation_style-001 · `enum` → `/visual/style_family`

**Which visual style family fits best (live-action, photo montage, 2D flat vector, stick figure, cut-out, layered 2.5D, low-poly 3D, textured 3D, pixel art, voxel, whiteboard or sketch, kinetic type, screen capture)?**

- Choices: `live-action`, `photo-montage`, `flat-vector-2d`, `stick-figure`, `cut-out`, `layered-2-5d`, `low-poly-3d`, `textured-3d`, `pixel-art`, `voxel`, `whiteboard-sketch`, `kinetic-type`, `screen-capture`, `mixed`
- Why it matters: Fills visual.style_family, which picks the renderer.
- How to answer: Classify from the F4 contact sheet and 5 F1 frames; give the share of runtime per family if mixed.
- Evidence required: frames: F4; frames: F1 samples
- Challenge: A stylised filter over footage is still live-action; check for photographic texture on F3 crops.

### characters_animation_style-002 · `integer` → `/visual/layers/-`

**Are there characters (people, animals, mascots, objects with faces), and how many distinct ones?**

- Why it matters: Decides whether the format needs character rigs.
- How to answer: Count distinct characters on the contact sheet; describe each by construction only (no identities).
- Evidence required: frames: F4
- Challenge: Do not count real people in photos as characters; they belong to shot_list_framing.

### characters_animation_style-003 · `enum` → `/visual/layers/-`

**How are characters constructed (stick lines, flat shapes, rigged cut-out parts, frame-by-frame drawings, 3D models)?**

- Choices: `stick-lines`, `flat-shapes`, `rigged-cut-out`, `frame-by-frame`, `3d-model`, `none`
- Why it matters: Selects a character rig type.
- How to answer: F3 crops at joints: hinged parts that rotate rigidly indicate cut-out rigs; redrawn shapes per frame indicate frame-by-frame.
- Evidence required: frames: F3 at joints; frames: F8
- Challenge: Check two different poses of the same character.

### characters_animation_style-004 · `enum` → `/render_binding/mapping/animation_fps`

**At what rate do drawings or poses change (on ones, twos, threes, or held poses) relative to the video frame rate?**

- Choices: `ones`, `twos`, `threes`, `held-poses`, `mixed`
- Why it matters: Fills animation_fps.
- How to answer: F8 steps over 0.5 s of character motion; count frames where the character changes; compare with fps.
- Evidence required: frames: F8; evidence.source.fps
- Challenge: Camera moves change every frame regardless; measure on a section with a still camera.

### characters_animation_style-005 · `object` → `/render_binding/mapping/line_style`

**What line style is used (stroke weight in px, outline colour, clean or sketchy)?**

- Why it matters: Fills line style parameters.
- How to answer: F3 enlarged crops; measure stroke width at full resolution.
- Evidence required: frames: F3
- Challenge: Report px measurements.

### characters_animation_style-006 · `enum` → `/render_binding/mapping/fill_style`

**How are shapes filled (flat colour, gradient, texture, cel-shaded with shadow bands)?**

- Choices: `flat`, `gradient`, `textured`, `cel-shaded`, `unfilled`
- Why it matters: Fills fill style.
- How to answer: F3 crops of filled areas.
- Evidence required: frames: F3
- Challenge: Compression banding on gradients is not cel shading.

### characters_animation_style-007 · `number` → `/render_binding/mapping/proportions`

**What are character proportions (head height to body height ratio)?**

- Why it matters: Fills a rig proportion parameter.
- How to answer: Measure on F3 crops of a standing pose.
- Evidence required: frames: F3
- Challenge: Use a neutral standing pose; foreshortening skews it.

### characters_animation_style-008 · `object` → `/render_binding/mapping/expressions`

**How many facial expression states are used, and how are they drawn (none, dots and lines, full faces)?**

- Why it matters: Sets the expression set size for a rig.
- How to answer: Collect distinct face states on F3 crops across the video.
- Evidence required: frames: F3
- Challenge: List timestamps per state.

### characters_animation_style-009 · `enum` → `/render_binding/mapping/lip_sync`

**Is there lip sync, and of what kind (none, open/close flap, viseme shapes)?**

- Choices: `none`, `flap`, `visemes`
- Why it matters: Decides whether a lip-sync tool (for example Rhubarb Lip Sync) is needed.
- How to answer: F8 on a speaking character; count distinct mouth shapes and compare with speech timing.
- Evidence required: frames: F8; evidence.audio.speech_segments
- Challenge: Mouth movement without speech alignment is not lip sync.

### characters_animation_style-010 · `number` → `/render_binding/mapping/blink_per_min`

**Do characters blink, and how often?**

- Why it matters: Adds a blink rate to idle animation.
- How to answer: Count blinks over 10 s of on-screen character time using F2 bursts.
- Evidence required: frames: F2
- Challenge: Report the observation window.

### characters_animation_style-011 · `integer` → `/render_binding/mapping/walk_cycle_frames`

**Are walk or run cycles used, and how many frames is one cycle?**

- Why it matters: Fills locomotion cycle length.
- How to answer: F8 over 1 s of walking; find the frame where the pose repeats.
- Evidence required: frames: F8
- Challenge: A sliding character with no leg motion has no cycle.

### characters_animation_style-012 · `boolean` → `/render_binding/mapping/secondary_motion`

**Is there secondary motion (follow-through on hair, clothing, tails, props)?**

- Why it matters: Adds secondary motion to the rig spec.
- How to answer: F8 after a character stops: parts that keep moving.
- Evidence required: frames: F8
- Challenge: Name the part and timestamp.

### characters_animation_style-013 · `object` → `/render_binding/mapping/squash_stretch`

**Is squash and stretch used on characters or props?**

- Why it matters: Adds deformation to the animation style.
- How to answer: F8 on impacts and jumps; measure height/width changes.
- Evidence required: frames: F8
- Challenge: Report measured ratio change.

### characters_animation_style-014 · `enum` → `/render_binding/mapping/character_entrance`

**How do characters enter the scene (pop in, walk in, draw on, fade, already present)?**

- Choices: `pop-in`, `walk-in`, `draw-on`, `fade`, `already-present`
- Why it matters: Fills character entrance.
- How to answer: F8 at first appearances.
- Evidence required: frames: F8
- Challenge: Check 2 entrances.

### characters_animation_style-015 · `boolean` → `/generation_rules/-`

**Do props and environments share the characters' style (line weight, fill, palette)?**

- Why it matters: Becomes a consistency rule for asset generation.
- How to answer: Compare F3 crops of props with characters.
- Evidence required: frames: F3
- Challenge: List one mismatch if found.

### characters_animation_style-016 · `enum` → `/render_binding/mapping/projection`

**From which viewpoint is the scene shown (side view, top-down, isometric, front, three-quarter)?**

- Choices: `side`, `top-down`, `isometric`, `front`, `three-quarter`, `mixed`
- Why it matters: Fills the projection for 2D or 3D renderers.
- How to answer: Inspect floor lines and object faces on F1 frames.
- Evidence required: frames: F1
- Challenge: Isometric shows parallel receding lines at about 30 degrees; measure one.

### characters_animation_style-017 · `boolean` → `/render_binding/mapping/physics`

**Do falling or bouncing objects follow plausible gravity (accelerating falls, decaying bounces)?**

- Why it matters: Decides whether a physics engine (for example Pymunk) is needed.
- How to answer: Track an object's height over F8 frames; check for increasing per-frame displacement while falling.
- Evidence required: frames: F8
- Challenge: Report the displacement series.

### characters_animation_style-018 · `integer` → `/render_binding/mapping/pose_count`

**How many distinct poses does each character use?**

- Why it matters: Sizes a pose library.
- How to answer: Group F3 crops of a character by pose.
- Evidence required: frames: F3
- Challenge: Mirrored poses count once; say how mirrors were treated.

### characters_animation_style-019 · `enum` → `/visual/style_family`

**Does the background art match the character style or contrast with it (for example photo backgrounds behind drawn characters)?**

- Choices: `matching`, `contrasting-photo`, `contrasting-other`
- Why it matters: Fills background/character style relation.
- How to answer: Compare F3 crops.
- Evidence required: frames: F3
- Challenge: Check two scenes.

### characters_animation_style-020 · `boolean` → `/render_binding/mapping/contact_shadow`

**Do characters cast contact shadows on the ground?**

- Why it matters: Adds contact shadows to the scene recipe.
- How to answer: F3 crops at feet.
- Evidence required: frames: F3
- Challenge: Give a timestamp.

### characters_animation_style-021 · `enum` → `/motion/easing`

**Is the motion snappy (fast moves with holds) or floaty (continuous slow easing)?**

- Choices: `snappy`, `floaty`, `mixed`
- Why it matters: Sets the animation easing style.
- How to answer: From F8 series, compare move duration with hold duration.
- Evidence required: frames: F8
- Challenge: Report move and hold durations.

### characters_animation_style-022 · `distribution` → `/render_binding/mapping/hold_ms`

**How long are holds between key poses (ms)?**

- Why it matters: Fills pose-to-pose hold timing.
- How to answer: F8 series: count frames where the pose does not change between moves.
- Evidence required: frames: F8
- Challenge: Report n and fps.

### characters_animation_style-023 · `list` → `/render_binding/mapping/motion_cues`

**Are motion lines, smears or impact frames used?**

- Why it matters: Adds stylised motion cues.
- How to answer: F8 on fast actions.
- Evidence required: frames: F8
- Challenge: Timestamp each cue.

### characters_animation_style-024 · `boolean` → `/generation_rules/-`

**Is each character colour-coded (one dominant colour per character)?**

- Why it matters: Becomes a character palette rule.
- How to answer: F9 on each character's main area.
- Evidence required: F9
- Challenge: Report colours per character.

### characters_animation_style-025 · `object` → `/visual/layers`

**For 2.5D scenes, how many depth planes are there and how do their parallax speeds compare?**

- Why it matters: Fills depth plane count and parallax ratios.
- How to answer: Track features on each plane between two frames of a move.
- Evidence required: frames: F1 pairs
- Challenge: Planes moving by animation (not camera) must be excluded.

### characters_animation_style-026 · `list` → `/render_binding/mapping/renderer_hint`

**Which open-source tools could reproduce this style (for example Motion Canvas, Manim, Blender, Godot, Synfig, OpenToonz, Pymunk for physics)?**

- Why it matters: Gives the render binding a renderer hint; always inferred.
- How to answer: Map style features (vector vs 3D, rigging, physics) to tools known to support them; mark method inferred and do not claim the source used them.
- Evidence required: style answers
- Challenge: Any statement that the source was made with a named tool is rejected unless the video shows it.

### characters_animation_style-027 · `list` → `/parameters/-`

**Which character and style parameters should a new video set (style family, rig asset, palette, line weight, fps)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect 001, 003, 004, 005 and 024.
- Evidence required: style answers
- Challenge: Each parameter needs derived_from.

### characters_animation_style-028 · `ms` → `/generation_rules/-`

**Do character actions follow the narration (a gesture or action when the key word is spoken)?**

- Why it matters: Becomes a narration-to-action sync rule.
- How to answer: Compare action start times (F8) with word onsets (A1) for 4 actions.
- Evidence required: frames: F8; A1
- Challenge: Report offsets for each action.

### characters_animation_style-029 · `boolean` → `/typography/labels/diegetic`

**Is text integrated into the scene (signs, labels attached to objects, speech bubbles)?**

- Why it matters: Adds diegetic text to the style.
- How to answer: Inspect F1 frames for text attached to objects.
- Evidence required: frames: F1
- Challenge: Captions placed near objects are not diegetic unless attached and moving with them.

### characters_animation_style-030 · `boolean` → `/generation_rules/-`

**Does a character's appearance stay consistent between shots (same proportions, colours, features)?**

- Why it matters: Tells the pipeline it needs a fixed character sheet or reusable rig.
- How to answer: F10 and F3 comparisons of the same character in different shots.
- Evidence required: frames: F3; frames: F10
- Challenge: List the shots compared and any differences found.

### characters_animation_style-031 · `integer` → `/timeline/beats/*/content_slot`

**How many scenes (distinct environments) does each item use?**

- Why it matters: Sizes scene assets per item.
- How to answer: Group shots per item by environment.
- Evidence required: frames: F4; item beat boundaries
- Challenge: Report the median and range.

### characters_animation_style-032 · `distribution` → `/render_binding/mapping/impact_pause_ms`

**Before a comedic or dramatic impact, how long is the pause (ms) between set-up and impact?**

- Why it matters: Fills a comic timing parameter.
- How to answer: F8 and A1 around 3 impacts; time from the last set-up motion to impact.
- Evidence required: frames: F8; A1
- Challenge: If the video has no impacts, answer not determinable.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F4** Whole-video contact sheet, 1 frame per second: ffmpeg -v error -i "$SRC" -vf "fps=1,scale=180:-2,tile=8x8" -frames:v 1 "$WORK/sheet.jpg" (or use the keyframes and contact sheet from video_re_keyframes_contact_sheet)
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F9** Average colour of a region: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y,scale=1:1:flags=area,format=rgb24" -f rawvideo - | od -An -tu1
- **F10** Similarity of two frames (SSIM, 1.0 = identical): ffmpeg -i a.jpg -i b.jpg -lavfi "[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*"
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "characters_animation_style-001", "ir_path": "/visual/style_family", "answer_type": "enum", "choices": ["live-action", "photo-montage", "flat-vector-2d", "stick-figure", "cut-out", "layered-2-5d", "low-poly-3d", "textured-3d", "pixel-art", "voxel", "whiteboard-sketch", "kinetic-type", "screen-capture", "mixed"]}, {"id": "characters_animation_style-002", "ir_path": "/visual/layers/-", "answer_type": "integer"}, {"id": "characters_animation_style-003", "ir_path": "/visual/layers/-", "answer_type": "enum", "choices": ["stick-lines", "flat-shapes", "rigged-cut-out", "frame-by-frame", "3d-model", "none"]}, {"id": "characters_animation_style-004", "ir_path": "/render_binding/mapping/animation_fps", "answer_type": "enum", "choices": ["ones", "twos", "threes", "held-poses", "mixed"]}, {"id": "characters_animation_style-005", "ir_path": "/render_binding/mapping/line_style", "answer_type": "object"}, {"id": "characters_animation_style-006", "ir_path": "/render_binding/mapping/fill_style", "answer_type": "enum", "choices": ["flat", "gradient", "textured", "cel-shaded", "unfilled"]}, {"id": "characters_animation_style-007", "ir_path": "/render_binding/mapping/proportions", "answer_type": "number"}, {"id": "characters_animation_style-008", "ir_path": "/render_binding/mapping/expressions", "answer_type": "object"}, {"id": "characters_animation_style-009", "ir_path": "/render_binding/mapping/lip_sync", "answer_type": "enum", "choices": ["none", "flap", "visemes"]}, {"id": "characters_animation_style-010", "ir_path": "/render_binding/mapping/blink_per_min", "answer_type": "number"}, {"id": "characters_animation_style-011", "ir_path": "/render_binding/mapping/walk_cycle_frames", "answer_type": "integer"}, {"id": "characters_animation_style-012", "ir_path": "/render_binding/mapping/secondary_motion", "answer_type": "boolean"}, {"id": "characters_animation_style-013", "ir_path": "/render_binding/mapping/squash_stretch", "answer_type": "object"}, {"id": "characters_animation_style-014", "ir_path": "/render_binding/mapping/character_entrance", "answer_type": "enum", "choices": ["pop-in", "walk-in", "draw-on", "fade", "already-present"]}, {"id": "characters_animation_style-015", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "characters_animation_style-016", "ir_path": "/render_binding/mapping/projection", "answer_type": "enum", "choices": ["side", "top-down", "isometric", "front", "three-quarter", "mixed"]}, {"id": "characters_animation_style-017", "ir_path": "/render_binding/mapping/physics", "answer_type": "boolean"}, {"id": "characters_animation_style-018", "ir_path": "/render_binding/mapping/pose_count", "answer_type": "integer"}, {"id": "characters_animation_style-019", "ir_path": "/visual/style_family", "answer_type": "enum", "choices": ["matching", "contrasting-photo", "contrasting-other"]}, {"id": "characters_animation_style-020", "ir_path": "/render_binding/mapping/contact_shadow", "answer_type": "boolean"}, {"id": "characters_animation_style-021", "ir_path": "/motion/easing", "answer_type": "enum", "choices": ["snappy", "floaty", "mixed"]}, {"id": "characters_animation_style-022", "ir_path": "/render_binding/mapping/hold_ms", "answer_type": "distribution"}, {"id": "characters_animation_style-023", "ir_path": "/render_binding/mapping/motion_cues", "answer_type": "list"}, {"id": "characters_animation_style-024", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "characters_animation_style-025", "ir_path": "/visual/layers", "answer_type": "object"}, {"id": "characters_animation_style-026", "ir_path": "/render_binding/mapping/renderer_hint", "answer_type": "list"}, {"id": "characters_animation_style-027", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "characters_animation_style-028", "ir_path": "/generation_rules/-", "answer_type": "ms"}, {"id": "characters_animation_style-029", "ir_path": "/typography/labels/diegetic", "answer_type": "boolean"}, {"id": "characters_animation_style-030", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "characters_animation_style-031", "ir_path": "/timeline/beats/*/content_slot", "answer_type": "integer"}, {"id": "characters_animation_style-032", "ir_path": "/render_binding/mapping/impact_pause_ms", "answer_type": "distribution"}]
```
