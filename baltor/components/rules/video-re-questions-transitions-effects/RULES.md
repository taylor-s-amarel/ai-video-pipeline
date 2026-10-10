# Video RE question bank: Transitions and effects

Lens `transitions_effects` · 31 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-transitions-effects` subagent and challenged by `video-re-challenger`.

Lists every transition and overlay effect with type, duration and sync, and expresses the reusable ones as ffmpeg-reproducible recipes.

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
- `distribution`: {"median": m, "p10": a, "p90": b, "n": count, "unit": "..."}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `segments`: [{"start_s": a, "end_s": b, "label": "..."}]
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[] boundaries
- audio.onsets_s

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_transition_type`, `video_re_detect_fade_to_color`, `video_re_detect_flash_frames`, `video_re_detect_whip_pan`, `video_re_detect_glitch_effects`, `video_re_detect_light_leak_flare`, `video_re_detect_camera_shake`, `video_re_detect_film_damage_dust`, `video_re_detect_particles_overlay`, `video_re_detect_sfx_hits`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F8 frame steps across each boundary (0.25 s either side); F11 scene scores for dissolves; A1 with highpass for whooshes.

## Pitfalls challengers check first

- Calling a hard cut a transition because the next shot zooms
- Counting compression flicker as a flash
- Inventing an xfade name that ffmpeg does not have

## Parameters this lens usually proposes

- transition_kind (enum)
- transition_ms
- transition_sfx (boolean)
- overlay_effects (list)

## IR paths this lens writes

- `/audio/sfx/-` (1)
- `/generation_rules/-` (10)
- `/motion/camera_moves/-` (1)
- `/motion/transitions/-` (15)
- `/parameters/-` (1)
- `/visual/layers/-` (3)

## Questions (31)

### transitions_effects-001 · `object` → `/motion/transitions/-`

**Which transition types occur between shots (hard cut, dissolve, whip, zoom-through, slide, wipe, glitch, flash, dip to black, morph), with counts?**

- Why it matters: Fills motion.transitions with a weighted vocabulary.
- How to answer: For every shot boundary in evidence.shots[] (or a sample of 15), inspect F8 frame steps 0.25 s either side and F11 scene scores; classify each.
- Evidence required: evidence.shots[]; frames: F8 across boundaries; F11 scene scores
- Challenge: Re-inspect 3 boundaries labelled as something other than hard cuts; each needs at least 2 intermediate frames.

### transitions_effects-002 · `distribution` → `/motion/transitions/-`

**How long do non-cut transitions last (median ms, range)?**

- Why it matters: Fills transition_ms.
- How to answer: Count intermediate frames on F8 steps; ms = frames x 1000 / fps.
- Evidence required: frames: F8; evidence.source.fps
- Challenge: Report frames and fps for each measured transition.

### transitions_effects-003 · `object` → `/generation_rules/-`

**Do transitions at item boundaries differ from transitions inside items?**

- Why it matters: Becomes separate rules for between-item and within-item transitions.
- How to answer: Compare transition types (001) at beat boundaries versus other boundaries.
- Evidence required: transition classification; timeline beats
- Challenge: Report counts in both groups.

### transitions_effects-004 · `object` → `/motion/transitions/-`

**How many white or colour flash frames are used, and how long is each?**

- Why it matters: Adds flash transitions with duration.
- How to answer: F6 YAVG per frame: spikes of 1-3 frames; confirm on F8.
- Evidence required: F6 series; frames: F8
- Challenge: Bright content cuts are not flashes; the flash frame must be near-uniform.

### transitions_effects-005 · `boolean` → `/motion/transitions/-`

**Are zoom-through (scale-up into next shot) transitions used?**

- Why it matters: Adds zoom transitions.
- How to answer: F8 across boundaries: outgoing shot scales up rapidly over 2+ frames before the new shot.
- Evidence required: frames: F8
- Challenge: A Ken Burns zoom ending at a cut is not a zoom transition unless it accelerates.

### transitions_effects-006 · `timestamps` → `/motion/transitions/-`

**Are glitch, RGB split or digital distortion effects used, and where?**

- Why it matters: Adds glitch effects.
- How to answer: F8 for horizontal displacement bands or colour channel offsets.
- Evidence required: frames: F8
- Challenge: Decoder errors look like glitches; they would also appear in a fresh decode only if in the file. Re-extract to confirm.

### transitions_effects-007 · `boolean` → `/motion/transitions/-`

**Are light-leak or burn transitions used?**

- Why it matters: Adds light-leak transitions.
- How to answer: F8 across boundaries with warm bright washes covering the cut.
- Evidence required: frames: F8
- Challenge: Must cover the cut point, not appear mid-shot.

### transitions_effects-008 · `ratio` → `/audio/sfx/-`

**What share of transitions have a whoosh or swish sound aligned with them (within 100 ms)?**

- Why it matters: Couples transitions with sfx.
- How to answer: A1 spectrograms with highpass=f=3000 around 6 transitions; look for rising or falling noise sweeps.
- Evidence required: A1 highpassed around transitions
- Challenge: Report the sample; music hi-hats are not whooshes.

### transitions_effects-009 · `ratio` → `/generation_rules/-`

**What share of transitions fall on a music onset (within 80 ms)?**

- Why it matters: Becomes a transition sync rule.
- How to answer: Compare transition midpoints with evidence.audio.onsets_s.
- Evidence required: transition times; evidence.audio.onsets_s
- Challenge: Compare with chance for the onset density.

### transitions_effects-010 · `object` → `/generation_rules/-`

**Do slides and wipes move in a consistent direction?**

- Why it matters: Becomes a direction rule.
- How to answer: Record the direction of each slide or wipe from F8.
- Evidence required: frames: F8
- Challenge: Report counts per direction.

### transitions_effects-011 · `list` → `/motion/transitions/-`

**Are shape or mask wipes used (circle, diagonal, brush, shape of an object)?**

- Why it matters: Adds mask wipes.
- How to answer: F8 across boundaries; describe the mask shape.
- Evidence required: frames: F8
- Challenge: Name the ffmpeg xfade transition that matches, if one exists (for example circleopen, wipeleft, diagtl).

### transitions_effects-012 · `boolean` → `/motion/transitions/-`

**Are speed ramps used around transitions (shot accelerates into the cut)?**

- Why it matters: Adds speed-ramp transitions.
- How to answer: Compare motion speed in the last 0.3 s of a shot against earlier on F8.
- Evidence required: frames: F8
- Challenge: Report the speed change.

### transitions_effects-013 · `list` → `/visual/layers/-`

**Are there persistent overlay effects throughout (dust, scratches, scan lines, frame border)?**

- Why it matters: Adds always-on overlay effects.
- How to answer: F2 bursts at 5 times across the video.
- Evidence required: frames: F2
- Challenge: Must appear at all 5 sampled times to be persistent.

### transitions_effects-014 · `object` → `/motion/camera_moves/-`

**Is screen shake used on impacts or reveals, and how strong?**

- Why it matters: Adds shake on impact.
- How to answer: Track a fixed element over F8 at reveal moments.
- Evidence required: frames: F8
- Challenge: Report px amplitude and duration.

### transitions_effects-015 · `timestamps` → `/motion/transitions/-`

**Are freeze frames combined with an effect (desaturate, outline, label) to call out a moment?**

- Why it matters: Adds a freeze-callout effect.
- How to answer: F5 near-zero difference plus a visual change on F1.
- Evidence required: F5; frames: F1
- Challenge: Stills with no motion are not freezes.

### transitions_effects-016 · `timestamps` → `/visual/layers/-`

**Are particle bursts or confetti used on reveals?**

- Why it matters: Adds particle accents.
- How to answer: F2 bursts at reveal times.
- Evidence required: frames: F2
- Challenge: Ambient particles present all the time are not bursts.

### transitions_effects-017 · `boolean` → `/motion/transitions/-`

**Are blur transitions (defocus out, refocus in) used?**

- Why it matters: Adds blur transitions.
- How to answer: F8 across boundaries; sharpness drops then recovers.
- Evidence required: frames: F8
- Challenge: Compare edge sharpness on the frames (F3).

### transitions_effects-018 · `ratio` → `/generation_rules/-`

**What share of all shot changes use any transition effect at all?**

- Why it matters: Sets the transition frequency parameter.
- How to answer: From 001: non-cut transitions / all boundaries.
- Evidence required: transition classification
- Challenge: Report the denominator.

### transitions_effects-019 · `object` → `/generation_rules/-`

**Are effects denser in the hook than in the body?**

- Why it matters: Becomes a hook effect-density rule.
- How to answer: Effects per 10 s in the hook versus body.
- Evidence required: effect timestamps
- Challenge: Report both rates.

### transitions_effects-020 · `enum` → `/motion/transitions/-`

**What happens at the very end (outro transition: fade, slide to end card, cut)?**

- Choices: `fade-out`, `slide-to-end-card`, `hard-cut`, `zoom-out`, `other`
- Why it matters: Fills the ending transition.
- How to answer: F8 over the last 1.5 s.
- Evidence required: frames: F8
- Challenge: Cross-check with structure_beats-031.

### transitions_effects-021 · `rule` → `/generation_rules/-`

**Which ffmpeg xfade transition and duration reproduce the main transition (for example fade 0.25 s, slideleft 0.3 s, circleopen 0.4 s)?**

- Why it matters: Gives the compiler a concrete, reproducible recipe.
- How to answer: Pick from xfade's built-in list (check ffmpeg -h filter=xfade) the closest match to 001; render a 2 s test with testsrc2 and compare frame steps.
- Evidence required: transition classification; test render
- Challenge: The named transition must exist in the installed ffmpeg; run the test render.

### transitions_effects-022 · `list` → `/parameters/-`

**Which transition parameters should a new video set (kinds and weights, duration, sfx coupling)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect 001, 002 and 008.
- Evidence required: transition answers
- Challenge: Each parameter needs derived_from.

### transitions_effects-023 · `number` → `/generation_rules/-`

**How many effect events (transitions, flashes, shakes, bursts) happen per minute?**

- Why it matters: Bounds effect density.
- How to answer: Count all effect timestamps / duration x 60.
- Evidence required: effect timestamps
- Challenge: Do not double-count an effect listed under two names.

### transitions_effects-024 · `ratio` → `/generation_rules/-`

**Do transitions cover jump cuts or continuity breaks (for example a flash placed on a jump cut)?**

- Why it matters: Adds a rule for when to use cover transitions.
- How to answer: Check whether transitions coincide with jump cuts found by pacing_cut_rhythm-017.
- Evidence required: jump cut times; transition times
- Challenge: If there are no jump cuts, answer not determinable.

### transitions_effects-025 · `timestamps` → `/motion/transitions/-`

**Are match or morph transitions used (shape in outgoing shot becomes shape in incoming shot)?**

- Why it matters: Adds match transitions.
- How to answer: F8 across boundaries; look for aligned shapes that persist through the cut.
- Evidence required: frames: F8
- Challenge: Coincidental alignment must be ruled out; check the shapes are deliberately positioned.

### transitions_effects-026 · `enum` → `/motion/transitions/-`

**Do flash colours come from the palette (accent colour) or are they white?**

- Choices: `white`, `accent`, `other`
- Why it matters: Fills flash colour.
- How to answer: F9 on flash frames.
- Evidence required: F9
- Challenge: If there are no flashes, answer not determinable.

### transitions_effects-027 · `boolean` → `/motion/transitions/-`

**Is a camera-flash or shutter effect used when photos appear?**

- Why it matters: Adds a photo reveal effect.
- How to answer: F8 at photo appearances; A1 for a click.
- Evidence required: frames: F8; A1
- Challenge: Requires both a brightness spike and a photo appearance.

### transitions_effects-028 · `timestamps` → `/visual/layers/-`

**Are lens distortion or fisheye effects used?**

- Why it matters: Adds a distortion effect.
- How to answer: F3 crops: straight lines bend near edges during effect moments.
- Evidence required: frames: F3
- Challenge: Wide-angle footage bends lines naturally; check graphics.

### transitions_effects-029 · `integer` → `/generation_rules/-`

**Are transitions frame-clean (no stray single frames from the wrong shot at boundaries)?**

- Why it matters: A quality rule for the rebuild (avoid stray frames).
- How to answer: F8 at 10 boundaries; count stray frames.
- Evidence required: frames: F8
- Challenge: Report the boundaries checked.

### transitions_effects-030 · `boolean` → `/generation_rules/-`

**Do any effects pass over text and reduce its legibility?**

- Why it matters: Becomes a legibility rule (effects stay below text or avoid text moments).
- How to answer: F8 at effect moments where text is on screen.
- Evidence required: frames: F8; evidence.text_regions[]
- Challenge: Name the moments.

### transitions_effects-031 · `segments` → `/motion/transitions/-`

**Are there dips to black or white between sections, and how long are they?**

- Why it matters: Adds dip transitions with duration.
- How to answer: F12 blackdetect; F6 YMIN high for white dips.
- Evidence required: F12; F6
- Challenge: Exclude the first and last second.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F5** Per-frame motion in a region (mean absolute frame difference, 0-255): ffmpeg -v error -i "$SRC" -vf "crop=iw:ih*0.15:0:0,tblend=all_mode=difference,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=$WORK/diff.txt" -an -f null -  (drop the crop for the full frame)
- **F6** Per-frame colour statistics (YMIN, YAVG, YMAX, SATAVG, HUEMED, UAVG, VAVG): ffmpeg -v error -ss T -t D -i "$SRC" -vf "signalstats,metadata=mode=print:file=$WORK/stats.txt" -an -f null -
- **F8** Every frame in a short window (animation timing; frame k is at T + k/fps): ffmpeg -v error -ss T -t 0.5 -i "$SRC" -vf "scale=540:-2" "$WORK/step_T_%03d.png"
- **F9** Average colour of a region: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y,scale=1:1:flags=area,format=rgb24" -f rawvideo - | od -An -tu1
- **F11** Per-frame scene-change score (finds dissolves and missed cuts): ffmpeg -v error -i "$SRC" -vf "select='gte(scene,0)',metadata=mode=print:key=lavfi.scene_score:file=$WORK/scene.txt" -an -f null -
- **F12** Black frames: ffmpeg -i "$SRC" -vf "blackdetect=d=0.05:pix_th=0.10" -an -f null - 2>&1 | grep black_
- **A1** Spectrogram image (add highpass=f=3000, before showspectrumpic to isolate clicks and whooshes): ffmpeg -v error -ss T -t D -i "$SRC" -lavfi "showspectrumpic=s=1200x600:legend=1" "$WORK/spec_T.png"

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "transitions_effects-001", "ir_path": "/motion/transitions/-", "answer_type": "object"}, {"id": "transitions_effects-002", "ir_path": "/motion/transitions/-", "answer_type": "distribution"}, {"id": "transitions_effects-003", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "transitions_effects-004", "ir_path": "/motion/transitions/-", "answer_type": "object"}, {"id": "transitions_effects-005", "ir_path": "/motion/transitions/-", "answer_type": "boolean"}, {"id": "transitions_effects-006", "ir_path": "/motion/transitions/-", "answer_type": "timestamps"}, {"id": "transitions_effects-007", "ir_path": "/motion/transitions/-", "answer_type": "boolean"}, {"id": "transitions_effects-008", "ir_path": "/audio/sfx/-", "answer_type": "ratio"}, {"id": "transitions_effects-009", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "transitions_effects-010", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "transitions_effects-011", "ir_path": "/motion/transitions/-", "answer_type": "list"}, {"id": "transitions_effects-012", "ir_path": "/motion/transitions/-", "answer_type": "boolean"}, {"id": "transitions_effects-013", "ir_path": "/visual/layers/-", "answer_type": "list"}, {"id": "transitions_effects-014", "ir_path": "/motion/camera_moves/-", "answer_type": "object"}, {"id": "transitions_effects-015", "ir_path": "/motion/transitions/-", "answer_type": "timestamps"}, {"id": "transitions_effects-016", "ir_path": "/visual/layers/-", "answer_type": "timestamps"}, {"id": "transitions_effects-017", "ir_path": "/motion/transitions/-", "answer_type": "boolean"}, {"id": "transitions_effects-018", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "transitions_effects-019", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "transitions_effects-020", "ir_path": "/motion/transitions/-", "answer_type": "enum", "choices": ["fade-out", "slide-to-end-card", "hard-cut", "zoom-out", "other"]}, {"id": "transitions_effects-021", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "transitions_effects-022", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "transitions_effects-023", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "transitions_effects-024", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "transitions_effects-025", "ir_path": "/motion/transitions/-", "answer_type": "timestamps"}, {"id": "transitions_effects-026", "ir_path": "/motion/transitions/-", "answer_type": "enum", "choices": ["white", "accent", "other"]}, {"id": "transitions_effects-027", "ir_path": "/motion/transitions/-", "answer_type": "boolean"}, {"id": "transitions_effects-028", "ir_path": "/visual/layers/-", "answer_type": "timestamps"}, {"id": "transitions_effects-029", "ir_path": "/generation_rules/-", "answer_type": "integer"}, {"id": "transitions_effects-030", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "transitions_effects-031", "ir_path": "/motion/transitions/-", "answer_type": "segments"}]
```
