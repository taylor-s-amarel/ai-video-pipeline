# Video RE question bank: Background system

Lens `background_system` · 32 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-background-system` subagent and challenged by `video-re-challenger`.

Describes what sits behind the subject, how much and how it moves, how it changes per beat and how it could be generated procedurally.

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
- `range`: {"value": typical, "min": a, "max": b, "unit": "..."}
- `boolean`: true or false
- `enum`: exactly one of the question's choices (a string)
- `palette`: ["#RRGGBB", ...] ordered by area, at most 8
- `list`: array of short strings (technique names or kinds)
- `segments`: [{"start_s": a, "end_s": b, "label": "..."}]
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- shots[].motion_energy.border (video_re_motion_energy)
- shots[].palette (video_re_palette_per_shot)

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_background_motion_type`, `video_re_detect_loop_seam`, `video_re_detect_parallax_depth_layers`, `video_re_detect_particles_overlay`, `video_re_detect_light_leak_flare`, `video_re_detect_palette_consistency`, `video_re_detect_split_screen_layout`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

F5 on the border bands (top 15%, bottom 15%, side 10%) for motion; F1 frames per beat; F6 for luminance.

## Pitfalls challengers check first

- Measuring background motion in a region covered by text or the subject
- Calling a slow zoom on a photo a moving background
- Ignoring compression noise when the motion level is near zero

## Parameters this lens usually proposes

- background_kind (enum)
- background_asset (asset)
- background_motion_level (range)
- background_per_beat (boolean)

## IR paths this lens writes

- `/generation_rules/-` (10)
- `/motion/background_motion_level` (1)
- `/motion/transitions/-` (1)
- `/parameters/-` (3)
- `/visual/grade` (1)
- `/visual/layers` (1)
- `/visual/layers/*/frame_coverage` (1)
- `/visual/layers/*/motion` (7)
- `/visual/layers/*/source_slot` (1)
- `/visual/layers/-` (5)
- `/visual/palette` (1)

## Questions (32)

### background_system-001 · `enum` → `/visual/layers/-`

**What is the background made of (looping video, still image, gradient, procedural pattern, blurred copy of the foreground, solid colour)?**

- Choices: `video-loop`, `still`, `gradient`, `procedural-pattern`, `blurred-foreground-copy`, `solid`, `mixed`
- Why it matters: Fills the bottom layer kind.
- How to answer: Inspect border regions on F1 frames across beats and F2 bursts; a blurred copy mirrors foreground colours and shapes.
- Evidence required: frames: F1 per beat; frames: F2 bursts
- Challenge: Compare background regions with the foreground at the same time (F10 on downscaled crops) before calling it a blurred copy.

### background_system-002 · `boolean` → `/generation_rules/-`

**Does the background move during every shot?**

- Why it matters: Checks the moving-background rule.
- How to answer: F5 on the top 15% and bottom 15% bands (regions without text); a shot passes when the mean difference exceeds 0.6 (0-255 scale) for every 2 s window. Also read evidence.shots[].motion_energy.border.
- Evidence required: F5 on border bands; evidence.shots[].motion_energy.border
- Challenge: Make sure the measured band contains no text, subject or camera zoom; a zoom on a photo moves the band too.

### background_system-003 · `number` → `/motion/background_motion_level`

**What is the background motion level (mean absolute frame difference in background regions, median over shots)?**

- Why it matters: Fills background_motion_level as a measurable number.
- How to answer: Median over shots of evidence.shots[].motion_energy.border (video_re_motion_energy: mean absolute grey-level difference between consecutive frames, 0-255, at 160 px analysis width, outside the central 60% x 60% box). Cross-check 3 shots with F5 on text-free bands.
- Evidence required: F5; evidence.shots[].motion_energy.border
- Challenge: The border region includes captions and titles that animate; compare with F5 on a text-free band and report both.

### background_system-004 · `enum` → `/parameters/-`

**Does the background change per beat, per shot, or stay the same for the whole video?**

- Choices: `per-shot`, `per-beat`, `constant`, `mixed`
- Why it matters: Becomes the background_per_beat parameter.
- How to answer: F10 SSIM between background crops at the start of each beat.
- Evidence required: frames: F10 on background crops
- Challenge: A looping video gives different frames over time; compare the same loop phase or judge by content.

### background_system-005 · `palette` → `/visual/palette`

**What are the background's dominant colours?**

- Why it matters: Adds background colours to the palette.
- How to answer: F9 average colour of background crops in 5 shots, or evidence.shots[].palette when the background dominates the frame.
- Evidence required: frames: F9; evidence.shots[].palette
- Challenge: Palettes from whole frames include the photo; use background-only crops.

### background_system-006 · `number` → `/generation_rules/-`

**How much darker or lighter is the background than the foreground subject (luma difference)?**

- Why it matters: Becomes a separation rule.
- How to answer: F6 YAVG on a background crop versus a subject crop in 5 shots.
- Evidence required: F6 on crops
- Challenge: Report all 5 pairs; one bright shot can dominate a mean.

### background_system-007 · `enum` → `/visual/layers/*/motion`

**How blurred is the background (sharp, soft, heavy blur)?**

- Choices: `sharp`, `soft`, `heavy`
- Why it matters: Sets background blur strength.
- How to answer: F3 enlarged crops of the background; heavy blur shows no edges finer than about 2% of frame width.
- Evidence required: frames: F3
- Challenge: Compare with a known sharp edge in the same frame.

### background_system-008 · `object` → `/visual/layers/-`

**Is there a repeating grid, dot or line pattern, and what is its spacing in px?**

- Why it matters: Adds a grid layer with spacing.
- How to answer: F3 crop of the background; measure distance between repeated lines.
- Evidence required: frames: F3
- Challenge: Report spacing and line width; check that it is not a compression artefact.

### background_system-009 · `seconds` → `/visual/layers/*/motion`

**Does the background loop, and what is the loop period in seconds?**

- Why it matters: Sets the loop length for a background asset.
- How to answer: F10 SSIM between a background crop at time t and later times; the first time with SSIM above 0.95 (excluding t+0) gives the period.
- Evidence required: frames: F10 over time
- Challenge: Foreground elements change the crop; use a band with background only.

### background_system-010 · `enum` → `/visual/layers/*/motion`

**Which way does the background move (drift up, down, sideways, radial, rotating, turbulent)?**

- Choices: `up`, `down`, `sideways`, `radial`, `rotating`, `turbulent`, `none`
- Why it matters: Fills the background motion direction.
- How to answer: Track a background feature over F2 bursts.
- Evidence required: frames: F2
- Challenge: Track at least two features; say if they disagree.

### background_system-011 · `integer` → `/visual/layers`

**How many sub-layers make up the background (for example gradient plus texture plus particles plus light)?**

- Why it matters: Sets background layer depth.
- How to answer: Separate elements by different motion or blend behaviour on F2 bursts.
- Evidence required: frames: F2
- Challenge: Require one observable cue per sub-layer.

### background_system-012 · `boolean` → `/generation_rules/-`

**Does the background react to the audio (pulses or flashes on beats or onsets)?**

- Why it matters: Adds an audio-reactive rule.
- How to answer: Correlate F5 background-band differences or F6 YAVG per frame with evidence.audio.onsets_s; check peaks within 80 ms of onsets.
- Evidence required: F5 or F6 series; evidence.audio.onsets_s
- Challenge: Compare against random time shifts; reaction must beat chance clearly.

### background_system-013 · `number` → `/visual/layers/*/motion`

**Does the background hue shift over time, and how fast (degrees per second)?**

- Why it matters: Adds a hue-cycle parameter.
- How to answer: F6 HUEMED on background-only crops sampled every 2 s.
- Evidence required: F6 HUEMED series
- Challenge: Shot changes cause jumps; measure within long shots.

### background_system-014 · `number` → `/generation_rules/-`

**Is the background less saturated than the foreground, and by how much (SATAVG ratio)?**

- Why it matters: Becomes a saturation separation rule.
- How to answer: F6 SATAVG on background versus subject crops.
- Evidence required: F6 on crops
- Challenge: Report all measured pairs.

### background_system-015 · `enum` → `/parameters/-`

**Is the background thematically tied to the topic (for example water for an ocean topic) or generic?**

- Choices: `topic-themed`, `generic`, `mixed`
- Why it matters: Becomes the background_theme parameter (asset search hint or generic default).
- How to answer: Compare background content with the item subjects on F1 frames.
- Evidence required: frames: F1
- Challenge: Method must be observed; one themed shot does not make the system themed.

### background_system-016 · `ratio` → `/visual/layers/*/frame_coverage`

**What share of the frame shows background (not covered by the main visual or text)?**

- Why it matters: Tells the generator how visible the background is.
- How to answer: 1 - main visual coverage - text area, measured on F1 frames in 5 shots.
- Evidence required: frames: F1; evidence.text_regions[].area_ratio
- Challenge: Semi-transparent foreground layers still let background show; say how they were counted.

### background_system-017 · `boolean` → `/visual/layers/-`

**Is the background derived from the foreground image (a zoomed, blurred copy)?**

- Why it matters: Selects a cheap, always-matching background method.
- How to answer: Compare colours and large shapes of the background with the foreground image at the same time.
- Evidence required: frames: F1; frames: F9
- Challenge: When the foreground changes, a derived background must change at the same frame.

### background_system-018 · `object` → `/visual/layers/-`

**Are there light sweeps or rays crossing the background, and how often?**

- Why it matters: Adds a light-sweep sub-layer with period.
- How to answer: F2 bursts and F6 YAVG series on background bands; periodic bright passes indicate sweeps.
- Evidence required: frames: F2; F6 series
- Challenge: Give the period from at least two passes.

### background_system-019 · `range` → `/visual/layers/*/motion`

**How fast does background content drift, in px per second at full resolution?**

- Why it matters: Sets the background speed parameter.
- How to answer: Track a feature across F1 frames 1 s apart.
- Evidence required: frames: F1 1 s apart
- Challenge: Track two features; report both.

### background_system-020 · `number` → `/visual/layers/*/motion`

**Does the background brightness pulse or flicker, and with what amplitude?**

- Why it matters: Adds a pulse parameter or confirms a steady background.
- How to answer: F6 YAVG per frame on a background band; report peak-to-peak range within shots.
- Evidence required: F6 series
- Challenge: Exclude frames at cuts.

### background_system-021 · `ratio` → `/generation_rules/-`

**Do background changes line up with item beat boundaries?**

- Why it matters: Becomes a sync rule between structure and background.
- How to answer: Background change times (from 004) compared with beat starts; share within 0.3 s.
- Evidence required: background change times; timeline beats
- Challenge: If the background never changes, answer not applicable in the note and ratio 0 with low confidence.

### background_system-022 · `rule` → `/generation_rules/-`

**What procedural recipe would reproduce the background (for example gradient plus noise plus drifting particles), expressed as ffmpeg filters or a renderer recipe?**

- Why it matters: Lets new videos generate the background without sourcing footage.
- How to answer: From 001, 008, 010, 013 and 019, write a recipe using real ffmpeg sources and filters (for example gradients, noise, geq, hue, scroll) or the project's renderer, with measured parameters.
- Evidence required: background answers
- Challenge: Every filter named must exist in ffmpeg (check with ffmpeg -filters); render 2 s and compare motion level with 003.

### background_system-023 · `list` → `/parameters/-`

**What background parameters should a new video set (kind, asset or recipe, speed, colours, per-beat change)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect 001, 003, 004, 005 and 019 into typed parameters with ranges from the observed spread.
- Evidence required: background answers
- Challenge: Each parameter must cite derived_from.

### background_system-024 · `boolean` → `/generation_rules/-`

**Is the background kept calm behind text (less detail or motion where captions and titles sit)?**

- Why it matters: Becomes a legibility rule for background placement.
- How to answer: Compare edge density and F5 motion in the caption band against other bands.
- Evidence required: F5 by band; frames: F3 caption band
- Challenge: A frosted panel already calms the area; say whether the background itself is calmer.

### background_system-025 · `ratio` → `/generation_rules/-`

**How busy is the background directly behind the captions (edge density or local contrast)?**

- Why it matters: Gives a measurable busyness limit for caption areas.
- How to answer: On F3 crops of the caption band without text, run an edge filter (ffmpeg -vf edgedetect) and report the share of edge pixels.
- Evidence required: frames: F3 with edgedetect
- Challenge: Report crop coordinates so the measurement can be repeated.

### background_system-026 · `list` → `/visual/layers/-`

**Are there depth cues inside the background (bokeh circles, haze, perspective lines)?**

- Why it matters: Adds depth elements to the background recipe.
- How to answer: Inspect F3 background crops.
- Evidence required: frames: F3
- Challenge: Name the timestamp for each cue.

### background_system-027 · `boolean` → `/generation_rules/-`

**Is the background in the hook different from the body background?**

- Why it matters: Becomes a hook-specific background option.
- How to answer: F10 SSIM and F9 colour comparison between hook and first item background crops.
- Evidence required: frames: F10; frames: F9
- Challenge: Compare against variation between two body items; the hook difference must exceed it.

### background_system-028 · `enum` → `/visual/layers/*/source_slot`

**Is the background footage vertical-native or cropped from horizontal footage?**

- Choices: `vertical-native`, `cropped-horizontal`, `generated`, `not-footage`
- Why it matters: Tells the asset step which footage orientation to source.
- How to answer: Look for cropped subjects at the sides, upscaling softness (F3), and composition centred for 16:9.
- Evidence required: frames: F3
- Challenge: Mark as inferred unless an edge cut-off is visible.

### background_system-029 · `enum` → `/visual/layers/*/motion`

**What is the temporal character of background motion: slow drift (under one cycle per 5 s), moderate, or busy (several changes per second)?**

- Choices: `slow-drift`, `moderate`, `busy`
- Why it matters: Gives a qualitative speed class tied to a number.
- How to answer: Use 003 and 019; classify with the stated boundaries and report the numbers.
- Evidence required: background motion numbers
- Challenge: The class must be consistent with the measured values.

### background_system-030 · `object` → `/generation_rules/-`

**Does the background motion level stay steady or spike at transitions?**

- Why it matters: Becomes a rule for transition energy versus steady motion.
- How to answer: Plot F5 border-band means over time (list values per second); compare values within 0.5 s of cuts to the rest.
- Evidence required: F5 series; evidence.shots[]
- Challenge: Cuts themselves create a one-frame spike in F5; exclude the cut frame.

### background_system-031 · `range` → `/visual/grade`

**What is the background's luminance range across shots (YAVG min and max)?**

- Why it matters: Bounds background brightness in the grade.
- How to answer: F6 YAVG on background bands per shot; report min, median and max.
- Evidence required: F6 per shot
- Challenge: Report which shots were measured.

### background_system-032 · `segments` → `/motion/transitions/-`

**Does the background ever drop to plain black or white (dips), and for how long?**

- Why it matters: Adds dips as transition devices or rules them out.
- How to answer: F12 blackdetect for black; F6 YMIN above 235 across a frame for white.
- Evidence required: F12; F6
- Challenge: Fade-ins at the start and end are separate from mid-video dips.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
- **F5** Per-frame motion in a region (mean absolute frame difference, 0-255): ffmpeg -v error -i "$SRC" -vf "crop=iw:ih*0.15:0:0,tblend=all_mode=difference,signalstats,metadata=mode=print:key=lavfi.signalstats.YAVG:file=$WORK/diff.txt" -an -f null -  (drop the crop for the full frame)
- **F6** Per-frame colour statistics (YMIN, YAVG, YMAX, SATAVG, HUEMED, UAVG, VAVG): ffmpeg -v error -ss T -t D -i "$SRC" -vf "signalstats,metadata=mode=print:file=$WORK/stats.txt" -an -f null -
- **F9** Average colour of a region: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y,scale=1:1:flags=area,format=rgb24" -f rawvideo - | od -An -tu1
- **F10** Similarity of two frames (SSIM, 1.0 = identical): ffmpeg -i a.jpg -i b.jpg -lavfi "[0:v]scale=320:-2[a];[1:v]scale=320:-2[b];[a][b]ssim" -f null - 2>&1 | grep -o "All:[0-9.]*"
- **F12** Black frames: ffmpeg -i "$SRC" -vf "blackdetect=d=0.05:pix_th=0.10" -an -f null - 2>&1 | grep black_

## Machine-readable bank

Read by the challenger's pre-pass script. The full bank with every field is `questions.json` in this package.

<!-- machine-readable bank -->
```json
[{"id": "background_system-001", "ir_path": "/visual/layers/-", "answer_type": "enum", "choices": ["video-loop", "still", "gradient", "procedural-pattern", "blurred-foreground-copy", "solid", "mixed"]}, {"id": "background_system-002", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "background_system-003", "ir_path": "/motion/background_motion_level", "answer_type": "number"}, {"id": "background_system-004", "ir_path": "/parameters/-", "answer_type": "enum", "choices": ["per-shot", "per-beat", "constant", "mixed"]}, {"id": "background_system-005", "ir_path": "/visual/palette", "answer_type": "palette"}, {"id": "background_system-006", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "background_system-007", "ir_path": "/visual/layers/*/motion", "answer_type": "enum", "choices": ["sharp", "soft", "heavy"]}, {"id": "background_system-008", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "background_system-009", "ir_path": "/visual/layers/*/motion", "answer_type": "seconds"}, {"id": "background_system-010", "ir_path": "/visual/layers/*/motion", "answer_type": "enum", "choices": ["up", "down", "sideways", "radial", "rotating", "turbulent", "none"]}, {"id": "background_system-011", "ir_path": "/visual/layers", "answer_type": "integer"}, {"id": "background_system-012", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "background_system-013", "ir_path": "/visual/layers/*/motion", "answer_type": "number"}, {"id": "background_system-014", "ir_path": "/generation_rules/-", "answer_type": "number"}, {"id": "background_system-015", "ir_path": "/parameters/-", "answer_type": "enum", "choices": ["topic-themed", "generic", "mixed"]}, {"id": "background_system-016", "ir_path": "/visual/layers/*/frame_coverage", "answer_type": "ratio"}, {"id": "background_system-017", "ir_path": "/visual/layers/-", "answer_type": "boolean"}, {"id": "background_system-018", "ir_path": "/visual/layers/-", "answer_type": "object"}, {"id": "background_system-019", "ir_path": "/visual/layers/*/motion", "answer_type": "range"}, {"id": "background_system-020", "ir_path": "/visual/layers/*/motion", "answer_type": "number"}, {"id": "background_system-021", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "background_system-022", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "background_system-023", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "background_system-024", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "background_system-025", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "background_system-026", "ir_path": "/visual/layers/-", "answer_type": "list"}, {"id": "background_system-027", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "background_system-028", "ir_path": "/visual/layers/*/source_slot", "answer_type": "enum", "choices": ["vertical-native", "cropped-horizontal", "generated", "not-footage"]}, {"id": "background_system-029", "ir_path": "/visual/layers/*/motion", "answer_type": "enum", "choices": ["slow-drift", "moderate", "busy"]}, {"id": "background_system-030", "ir_path": "/generation_rules/-", "answer_type": "object"}, {"id": "background_system-031", "ir_path": "/visual/grade", "answer_type": "range"}, {"id": "background_system-032", "ir_path": "/motion/transitions/-", "answer_type": "segments"}]
```
