# Video RE question bank: Narration and voice

Lens `narration_voice` · 31 questions · answers follow the `video_re_analyst_answer` contract and fill the `video_re_format_ir` contract (Video format IR, spec `baltor.video-format-ir/v1`). Answered by the `video-re-analyst-narration-voice` subagent and challenged by `video-re-challenger`.

Measures the delivery (coverage, words per minute, pauses, emphasis, processing) so a licensed or synthetic voice can reproduce it, without cloning or keeping the source voice.

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
- `text`: one technique description, at most 300 characters, no copied content
- `list`: array of short strings (technique names or kinds)
- `timestamps`: array of seconds from the start of the source
- `rule`: one procedural generation rule string, at most 400 characters, written in terms of parameters
- `object`: a JSON object with the keys the question's how_to_answer names

## Evidence this lens leans on

- audio.speech_segments (video_re_speech_segments)
- audio.speech_wpm (video_re_speech_rate)
- captions[] timing
- audio.integrated_lufs

Optional detector envelopes (spec `baltor.video-detection/v1`) when installed: `video_re_detect_voice_pitch_pace`, `video_re_detect_silence_gaps`, `video_re_detect_reverb_room`, `video_re_detect_dynamics_compression`, `video_re_detect_stereo_width`, `video_re_detect_music_presence`. Treat their results as measured evidence and cite the detector as the tool.

## What to inspect beyond evidence.json

A1 spectrograms of 2-3 sentences, A4 silences, A6 RMS for emphasis; never save or splice the voice.

## Pitfalls challengers check first

- Guessing speaker identity, age or ethnicity; describe pitch register and delivery only
- Calling a voice synthetic from quality alone
- Computing wpm over the whole runtime instead of speech time

## Parameters this lens usually proposes

- voice_engine (string)
- voice_id (string)
- words_per_minute (range)
- pause_ms (range)
- delivery (enum)

## IR paths this lens writes

- `/audio/music/vocals_under_narration` (1)
- `/audio/music_under_voice_db` (1)
- `/audio/narration/breaths` (1)
- `/audio/narration/consistency` (1)
- `/audio/narration/coverage_ratio` (1)
- `/audio/narration/cut_to_voice_ms` (1)
- `/audio/narration/delivery` (1)
- `/audio/narration/effects` (1)
- `/audio/narration/emphasis` (1)
- `/audio/narration/end_offset_s` (1)
- `/audio/narration/language` (1)
- `/audio/narration/loudness_spread_db` (1)
- `/audio/narration/noise_floor_db` (1)
- `/audio/narration/panning` (1)
- `/audio/narration/pause_ms` (1)
- `/audio/narration/pitch_register` (1)
- `/audio/narration/planned_gaps` (1)
- `/audio/narration/presence` (1)
- `/audio/narration/processing` (1)
- `/audio/narration/sentence_end_contour` (1)
- `/audio/narration/source_kind` (1)
- `/audio/narration/tone` (1)
- `/audio/narration/voice_count` (1)
- `/audio/narration/wpm_by_beat` (1)
- `/audio/words_per_minute` (1)
- `/generation_rules/-` (4)
- `/parameters/-` (1)
- `/render_binding/mapping/tts_hint` (1)

## Questions (31)

### narration_voice-001 · `ratio` → `/audio/narration/coverage_ratio`

**Is there narration, and what share of the runtime is covered by speech?**

- Why it matters: Fills narration coverage; drives how much script is needed.
- How to answer: Sum of evidence.audio.speech_segments durations / source.duration_s (video_re_speech_segments).
- Evidence required: evidence.audio.speech_segments; evidence.source.duration_s
- Challenge: Voice activity detectors flag sung vocals and dense music; check two segments on an A1 spectrogram.

### narration_voice-002 · `enum` → `/audio/narration/source_kind`

**Does the voice sound synthetic (text-to-speech) or recorded human speech?**

- Choices: `synthetic`, `human`, `mixed`, `not-determinable`
- Why it matters: Tells the pipeline whether a TTS engine can match the delivery.
- How to answer: Inspect A1 spectrograms of 3 sentences: very regular pitch contours, identical prosody on repeated phrases and absent breaths suggest TTS. Method is always inferred.
- Evidence required: A1 on 3 sentences
- Challenge: Modern TTS can be indistinguishable; confidence above 0.6 needs at least two independent cues.

### narration_voice-003 · `object` → `/audio/narration/pitch_register`

**What is the pitch register of the voice (low, mid, high) and the approximate fundamental frequency range?**

- Why it matters: Guides voice selection without identifying anyone.
- How to answer: Read the lowest harmonic band on A1 spectrograms (or use librosa.pyin if installed, marked measured). Report Hz range.
- Evidence required: A1 spectrograms
- Challenge: Answers that infer gender, age or ethnicity are rejected; only pitch and delivery are allowed.

### narration_voice-004 · `number` → `/audio/words_per_minute`

**What is the speaking rate in words per minute of speech time?**

- Why it matters: Fills audio.words_per_minute.
- How to answer: Read evidence.audio.speech_wpm (video_re_speech_rate); state whether it divides by speech time or by runtime.
- Evidence required: evidence.audio.speech_wpm
- Challenge: Recompute from caption word count / total speech segment minutes; a mismatch above 10% needs an explanation.

### narration_voice-005 · `object` → `/audio/narration/wpm_by_beat`

**How much does speaking rate vary across beats (wpm per beat role)?**

- Why it matters: Becomes per-beat rate targets.
- How to answer: Words per beat (captions) / speech time per beat.
- Evidence required: evidence.captions[]; evidence.audio.speech_segments; timeline beats
- Challenge: Beats with under 10 words give unstable rates; mark them.

### narration_voice-006 · `object` → `/audio/narration/pause_ms`

**How long are pauses between sentences and between items (median ms each)?**

- Why it matters: Sets pause lengths for the TTS plan.
- How to answer: Gaps between speech segments, split into within-item and at item boundaries.
- Evidence required: evidence.audio.speech_segments; timeline beats
- Challenge: Confirm two gaps with A4 silencedetect.

### narration_voice-007 · `object` → `/audio/narration/loudness_spread_db`

**What is the dynamic range of the voice (momentary loudness spread during speech)?**

- Why it matters: Sets compression targets for the narration chain.
- How to answer: A3 momentary loudness restricted to speech segments; report p10 and p90.
- Evidence required: A3; evidence.audio.speech_segments
- Challenge: Music under voice raises the floor; note the music level estimate.

### narration_voice-008 · `list` → `/audio/narration/emphasis`

**How are key words emphasised (louder, slower, higher pitch, pause before)?**

- Why it matters: Becomes emphasis markup rules for TTS (SSML-like or engine-specific).
- How to answer: Around 4 key numbers or words, compare A6 RMS, local rate and pitch (A1) with neighbouring words.
- Evidence required: A6; A1
- Challenge: Report the measurement per instance.

### narration_voice-009 · `enum` → `/audio/narration/delivery`

**What is the delivery style (conversational, announcer, documentary, energetic hype, calm explainer, whisper)?**

- Choices: `conversational`, `announcer`, `documentary`, `hype`, `calm-explainer`, `whisper`, `other`
- Why it matters: Fills delivery for voice selection.
- How to answer: Combine rate (004), pitch variation (A1), loudness spread (007) and pause pattern (006); method inferred.
- Evidence required: narration measurements
- Challenge: Each style claim must cite at least two measurements.

### narration_voice-010 · `enum` → `/audio/narration/breaths`

**Are breaths audible between phrases or edited out?**

- Choices: `audible`, `removed`, `mixed`
- Why it matters: Becomes an editing rule for the narration track.
- How to answer: A1 spectrograms of pauses: broadband soft noise bursts before phrases are breaths.
- Evidence required: A1 on pauses
- Challenge: Check 4 pauses.

### narration_voice-011 · `object` → `/audio/narration/processing`

**How is the voice processed (dry or with room reverb; heavy or light compression; de-essing)?**

- Why it matters: Fills the voice processing chain.
- How to answer: A1: reverb tails extend energy after words end; compression shows narrow loudness spread (007); sibilance bands near 5-9 kHz.
- Evidence required: A1; loudness spread
- Challenge: Each processing claim needs its cue.

### narration_voice-012 · `enum` → `/audio/narration/tone`

**Is the voice bright or warm (where is most energy, above or below about 1 kHz)?**

- Choices: `bright`, `neutral`, `warm`
- Why it matters: Fills EQ guidance.
- How to answer: A1 spectrogram energy distribution during speech; compare with A6 RMS after highpass=f=2000 versus lowpass=f=500.
- Evidence required: A1; A6 filtered
- Challenge: Report the two filtered RMS values.

### narration_voice-013 · `number` → `/audio/music_under_voice_db`

**Is the voice clearly dominant over music during speech (approximate level difference in dB)?**

- Why it matters: Sets voice-to-music balance.
- How to answer: A5 mid versus side loudness during speech (stereo only), or A6 RMS during speech versus in speech gaps with music only.
- Evidence required: A5; A6
- Challenge: Side-channel estimates fail when music is near mono; check A7 channels and say which method was used.

### narration_voice-014 · `ms` → `/audio/narration/cut_to_voice_ms`

**How soon after a cut does speech start, when a sentence starts at a cut?**

- Why it matters: Sets cut-to-voice latency.
- How to answer: For cuts followed by a speech segment start within 1 s, compute the delay; median.
- Evidence required: evidence.shots[]; evidence.audio.speech_segments
- Challenge: Report n.

### narration_voice-015 · `integer` → `/audio/narration/voice_count`

**How many distinct voices speak (narrator, characters, quoted speakers)?**

- Why it matters: Decides how many voice slots the format needs.
- How to answer: A1 spectrograms: distinct pitch ranges and timbres; F1 frames for on-screen speakers.
- Evidence required: A1; frames: F1
- Challenge: One narrator changing tone is one voice.

### narration_voice-016 · `list` → `/audio/narration/effects`

**Are pitch or character effects applied to voices (sped-up, robotic, telephone filter)?**

- Why it matters: Adds voice effects.
- How to answer: A1 for formant shifts and band-limiting.
- Evidence required: A1
- Challenge: Timestamp each effect.

### narration_voice-017 · `number` → `/audio/narration/noise_floor_db`

**What is the noise floor in speech gaps without music (dBFS)?**

- Why it matters: Sets the cleanliness target for narration.
- How to answer: A6 RMS in gaps where A1 shows no music.
- Evidence required: A6; A1
- Challenge: If music fills every gap, answer not determinable.

### narration_voice-018 · `enum` → `/audio/narration/sentence_end_contour`

**Do sentences end with falling intonation, rising intonation (upspeak), or flat?**

- Choices: `falling`, `rising`, `flat`, `mixed`
- Why it matters: Guides prosody settings.
- How to answer: A1: track the lowest harmonic in the last word of 6 sentences.
- Evidence required: A1
- Challenge: Questions naturally rise; exclude them.

### narration_voice-019 · `boolean` → `/generation_rules/-`

**Is there evidence that speech was time-stretched to fit picture (unnatural rate shifts, smeared consonants, pitch artefacts)?**

- Why it matters: A quality rule: this project forbids time-stretching speech to fit.
- How to answer: Compare local wpm across sentences and inspect A1 for phase smearing on fast passages.
- Evidence required: local wpm; A1
- Challenge: Natural rate changes are common; require an artefact, not just a rate change.

### narration_voice-020 · `ratio` → `/generation_rules/-`

**Is each item's narration contained within its beat, or does speech spill over beat boundaries?**

- Why it matters: Becomes a narration-to-beat alignment rule.
- How to answer: Check whether speech segments cross item boundaries by more than 300 ms.
- Evidence required: evidence.audio.speech_segments; timeline beats
- Challenge: Report the share and the crossings.

### narration_voice-021 · `text` → `/audio/narration/language`

**What language is the narration in, and is it consistent?**

- Why it matters: Fills narration language for TTS and caption tools.
- How to answer: From captions or transcription output language tag (evidence.tools or adapter output); confirm by reading two caption cards (analysis only).
- Evidence required: evidence.captions[] (analysis only); evidence.tools
- Challenge: Do not infer nationality or accent origin of the speaker.

### narration_voice-022 · `list` → `/parameters/-`

**Which narration parameters should a new video set (voice engine, voice id, wpm range, pause lengths, delivery)?**

- Why it matters: Feeds the parameteriser.
- How to answer: Collect 004, 006, 009 and 012 into parameters; engine and voice are open slots (licensed or local TTS).
- Evidence required: narration answers
- Challenge: No parameter may reference cloning the source voice.

### narration_voice-023 · `rule` → `/generation_rules/-`

**Write the narration budget rule (words per beat = beat_s x wpm / 60 x speech share).**

- Why it matters: Lets the script writer hit beat lengths without stretching speech.
- How to answer: Use 001, 004 and per-beat coverage; test on 3 beats.
- Evidence required: narration answers; timeline beats
- Challenge: Predict words for 3 observed beats; errors over 20% reject the rule.

### narration_voice-024 · `enum` → `/generation_rules/-`

**Are numbers spoken digit by digit, as full words, or abbreviated (for example 'three point two million')?**

- Choices: `full-words`, `digit-by-digit`, `abbreviated`, `mixed`
- Why it matters: Becomes a text normalisation rule before TTS.
- How to answer: Compare spoken numbers (A1 timing and captions) with on-screen digits.
- Evidence required: evidence.captions[] (analysis only); frames: F3 numbers
- Challenge: Check 3 numbers.

### narration_voice-025 · `boolean` → `/audio/narration/panning`

**Is the voice centred in the stereo image (mono-compatible)?**

- Why it matters: Fills voice panning.
- How to answer: Compare A5 side loudness during speech with mid loudness: near-silent side during speech-only passages means centred.
- Evidence required: A5
- Challenge: Mono files make this trivially true; check A7 channels first.

### narration_voice-026 · `enum` → `/audio/narration/presence`

**Is the narrator seen on screen (lip-synced presenter) or off-screen (voiceover)?**

- Choices: `on-screen`, `off-screen`, `both`
- Why it matters: Decides whether a presenter shot is part of the format.
- How to answer: F2 bursts during speech: visible mouth movement matching speech.
- Evidence required: frames: F2; evidence.audio.speech_segments
- Challenge: Do not identify the presenter.

### narration_voice-027 · `boolean` → `/audio/music/vocals_under_narration`

**Does music with sung vocals overlap the narration?**

- Why it matters: Becomes a mix rule (instrumental under narration).
- How to answer: A1 during speech: a second harmonic series with sustained notes.
- Evidence required: A1
- Challenge: Give a timestamp.

### narration_voice-028 · `seconds` → `/audio/narration/end_offset_s`

**How many seconds before the end does narration stop?**

- Why it matters: Sets the narration end offset.
- How to answer: source.duration_s - last speech_segments end_s.
- Evidence required: evidence.audio.speech_segments; evidence.source.duration_s
- Challenge: Recompute.

### narration_voice-029 · `timestamps` → `/audio/narration/planned_gaps`

**Does narration deliberately stop for music or sound moments (planned silences), and how many?**

- Why it matters: Adds planned narration gaps.
- How to answer: Speech gaps over 1 s where music or sfx rises (A3).
- Evidence required: evidence.audio.speech_segments; A3
- Challenge: List each gap.

### narration_voice-030 · `enum` → `/audio/narration/consistency`

**Is the recording tone consistent throughout (same mic, room and level), or patched from sessions?**

- Choices: `consistent`, `patched`, `not-determinable`
- Why it matters: A quality rule for TTS or recorded narration (render in one pass or match levels).
- How to answer: Compare A1 spectral shape and noise floor across the beginning, middle and end.
- Evidence required: A1; A6
- Challenge: Name the segments compared.

### narration_voice-031 · `list` → `/render_binding/mapping/tts_hint`

**Which open-source TTS engines could approximate this delivery (for example Kokoro, Piper, Pocket TTS), and which settings matter (rate, voice, pauses)?**

- Why it matters: Gives the render binding a TTS hint; always inferred.
- How to answer: Match measured rate, register and delivery to engines available locally; never propose cloning the source voice.
- Evidence required: narration answers
- Challenge: Reject any hint that involves voice cloning of the source speaker.

## Recipes referenced above

Set `SRC` (the source video), `WORK` (scratch directory), `T` (seconds) and `D` (duration) first. Frames and images you write can be inspected with the Read tool.

- **F1** Single frame: ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -q:v 2 "$WORK/f_T.jpg"
- **F2** Burst sheet, 10 frames over 1 s: ffmpeg -v error -ss T -t 1 -i "$SRC" -vf "fps=10,scale=270:-2,tile=5x2" -frames:v 1 "$WORK/burst_T.jpg"
- **F3** Full-resolution crop (add ,scale=iw*2:-1:flags=lanczos to enlarge): ffmpeg -v error -ss T -i "$SRC" -frames:v 1 -vf "crop=W:H:X:Y" "$WORK/crop_T.png"
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
[{"id": "narration_voice-001", "ir_path": "/audio/narration/coverage_ratio", "answer_type": "ratio"}, {"id": "narration_voice-002", "ir_path": "/audio/narration/source_kind", "answer_type": "enum", "choices": ["synthetic", "human", "mixed", "not-determinable"]}, {"id": "narration_voice-003", "ir_path": "/audio/narration/pitch_register", "answer_type": "object"}, {"id": "narration_voice-004", "ir_path": "/audio/words_per_minute", "answer_type": "number"}, {"id": "narration_voice-005", "ir_path": "/audio/narration/wpm_by_beat", "answer_type": "object"}, {"id": "narration_voice-006", "ir_path": "/audio/narration/pause_ms", "answer_type": "object"}, {"id": "narration_voice-007", "ir_path": "/audio/narration/loudness_spread_db", "answer_type": "object"}, {"id": "narration_voice-008", "ir_path": "/audio/narration/emphasis", "answer_type": "list"}, {"id": "narration_voice-009", "ir_path": "/audio/narration/delivery", "answer_type": "enum", "choices": ["conversational", "announcer", "documentary", "hype", "calm-explainer", "whisper", "other"]}, {"id": "narration_voice-010", "ir_path": "/audio/narration/breaths", "answer_type": "enum", "choices": ["audible", "removed", "mixed"]}, {"id": "narration_voice-011", "ir_path": "/audio/narration/processing", "answer_type": "object"}, {"id": "narration_voice-012", "ir_path": "/audio/narration/tone", "answer_type": "enum", "choices": ["bright", "neutral", "warm"]}, {"id": "narration_voice-013", "ir_path": "/audio/music_under_voice_db", "answer_type": "number"}, {"id": "narration_voice-014", "ir_path": "/audio/narration/cut_to_voice_ms", "answer_type": "ms"}, {"id": "narration_voice-015", "ir_path": "/audio/narration/voice_count", "answer_type": "integer"}, {"id": "narration_voice-016", "ir_path": "/audio/narration/effects", "answer_type": "list"}, {"id": "narration_voice-017", "ir_path": "/audio/narration/noise_floor_db", "answer_type": "number"}, {"id": "narration_voice-018", "ir_path": "/audio/narration/sentence_end_contour", "answer_type": "enum", "choices": ["falling", "rising", "flat", "mixed"]}, {"id": "narration_voice-019", "ir_path": "/generation_rules/-", "answer_type": "boolean"}, {"id": "narration_voice-020", "ir_path": "/generation_rules/-", "answer_type": "ratio"}, {"id": "narration_voice-021", "ir_path": "/audio/narration/language", "answer_type": "text"}, {"id": "narration_voice-022", "ir_path": "/parameters/-", "answer_type": "list"}, {"id": "narration_voice-023", "ir_path": "/generation_rules/-", "answer_type": "rule"}, {"id": "narration_voice-024", "ir_path": "/generation_rules/-", "answer_type": "enum", "choices": ["full-words", "digit-by-digit", "abbreviated", "mixed"]}, {"id": "narration_voice-025", "ir_path": "/audio/narration/panning", "answer_type": "boolean"}, {"id": "narration_voice-026", "ir_path": "/audio/narration/presence", "answer_type": "enum", "choices": ["on-screen", "off-screen", "both"]}, {"id": "narration_voice-027", "ir_path": "/audio/music/vocals_under_narration", "answer_type": "boolean"}, {"id": "narration_voice-028", "ir_path": "/audio/narration/end_offset_s", "answer_type": "seconds"}, {"id": "narration_voice-029", "ir_path": "/audio/narration/planned_gaps", "answer_type": "timestamps"}, {"id": "narration_voice-030", "ir_path": "/audio/narration/consistency", "answer_type": "enum", "choices": ["consistent", "patched", "not-determinable"]}, {"id": "narration_voice-031", "ir_path": "/render_binding/mapping/tts_hint", "answer_type": "list"}]
```
