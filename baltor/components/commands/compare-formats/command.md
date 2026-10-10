---
description: "Score a variant against its source format and propose IR fixes"
argument-hint: "<source format_ir.json> <variant.mp4 | variant format_ir.json> [--round N]"
---

Compare a variant with its source format and propose fixes: $ARGUMENTS

Arguments: the source `format_ir.json` and either a rendered variant (mp4) or its `format_ir.json`; optional
`--round N` and `--history DIR`.

Boundary: The swarm lifts technique and structure only. Never store, transcribe or reuse the source's footage, frames, music, voice or script text. Keyframes and spectrograms are temporary analysis files in a scratch directory and are never copied into the format IR or a variant. On-screen text may be quoted only as a locating note in evidence.note, at most 6 words, and narration is never quoted. Patterns replace content words with slots, e.g. 'FACT {n}' or '{number} {unit} {noun}'. Analysing a public video for technique is fine; republishing its content is not.

1. Run `video-re-round-trip-judge` with `SOURCE_IR`, the variant and the history. It measures the variant with
   `video_re_evidence_bundle`, lifts it with the same swarm when needed, scores it with `video_re_ir_diff_fidelity` per dimension (timeline,
   cut rhythm, layers, typography, motion, audio, script pattern) and checks originality.
2. Show the per-dimension scores, the change from the previous round, the originality result and the proposed
   JSON Patch fixes with their evidence.
3. If the judge says continue, apply the patches the user accepts to the IR, validate with `video_re_ir_validate`,
   re-render with `/render-from-format` and compare again. Stop when the judge's stop rule says fidelity has
   stopped improving.
