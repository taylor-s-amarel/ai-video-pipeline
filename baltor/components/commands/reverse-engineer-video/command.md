---
description: "Reverse-engineer a local video into a reusable, parametric format IR"
argument-hint: "<video file> [--lenses all|a,b] [--out DIR] [--text-mode masked|full]"
---

Reverse-engineer this video into a reusable, parametric format: $ARGUMENTS

Arguments: a local video file (required); optional `--lenses` (default: all 18), `--out DIR` (default
`video_re/<file stem>`), `--text-mode masked|full` (default masked).

Boundary: The swarm lifts technique and structure only. Never store, transcribe or reuse the source's footage, frames, music, voice or script text. Keyframes and spectrograms are temporary analysis files in a scratch directory and are never copied into the format IR or a variant. On-screen text may be quoted only as a locating note in evidence.note, at most 6 words, and narration is never quoted. Patterns replace content words with slots, e.g. 'FACT {n}' or '{number} {unit} {noun}'. Analysing a public video for technique is fine; republishing its content is not.

0. Preflight. Check the file exists and that the user supplied it or may analyse it. Do not download anything:
   if only a URL was given, ask for the file. Never upload or republish the source.
1. Measure (load and disassemble). Run the `video_re_evidence_bundle` code module on the file:
   `python3 .baltor/lib/video-re-evidence-bundle/video_re_evidence_bundle.py VIDEO --out-dir OUT/evidence --text-mode masked`
   (`--text-mode full` only when the user asked for it; `--fast` for a quicker pass; `--help` for the rest). It
   writes `evidence.json`, `details/<module>.json`, keyframes and contact sheets. Report every `errors[]` entry:
   those measurements are missing, not zero.
2. Analyse. Start one subagent per lens, in parallel, each with `EVIDENCE`, `SRC`, `WORK=OUT/work/<lens>` and
   `OUT=OUT/answers/<lens>.json`: `video-re-analyst-structure-beats`, `video-re-analyst-hook-first-seconds`, `video-re-analyst-script-rhetoric`, `video-re-analyst-pacing-cut-rhythm`, `video-re-analyst-shot-list-framing`, `video-re-analyst-camera-motion`, `video-re-analyst-layers-compositing`, `video-re-analyst-background-system`, `video-re-analyst-typography-captions`, `video-re-analyst-text-animation`, `video-re-analyst-color-grade`, `video-re-analyst-characters-animation-style`, `video-re-analyst-transitions-effects`, `video-re-analyst-narration-voice`, `video-re-analyst-music-sfx-mix`, `video-re-analyst-retention-cta`, `video-re-analyst-platform-fit-safe-areas`, `video-re-analyst-rights-originality-boundary`.
3. Challenge. Run `video-re-challenger` on each lens's answers in parallel (`OUT/challenge/<lens>.json`), then
   once over all surviving answers for the cross-lens checks (`OUT/challenge/cross.json`).
4. Lift. Run `video-re-lifter` on the surviving answers: `OUT/format_ir.json`, `OUT/lift_report.json`.
5. Parameterise. Run `video-re-parameteriser`: updated `OUT/format_ir.json`, `OUT/parameterise_report.json`.
6. Validate with `video_re_ir_validate`; fix until it reports no errors.
7. Delete `OUT/work` (frames, crops, spectrograms) unless the user asked to keep it for review. It never goes
   into the IR.
8. Report: format_id, beats, parameters with ranges, the number of generation rules, open questions, the
   measurements that were missing, and the next step (`/render-from-format`, then `/compare-formats`).

The `video_re_pipeline` skill ships a `workflow.js` that runs this same fan-out automatically.
