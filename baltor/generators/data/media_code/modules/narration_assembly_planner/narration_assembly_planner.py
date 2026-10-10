"""Assemble TTS chunks into one narration track with natural pauses.

Given each chunk's audio duration, its boundary type and optional
chunk-local word timings, plans:

* the start time of every chunk, with pauses by boundary (sentence 0.25 s,
  paragraph 0.6 s, section 1.0 s by default) and a lead-in;
* global word timings (chunk-local times shifted), ready for captions;
* an ffmpeg ``filter_complex`` that delays and mixes the chunk files into one
  track without re-timing them (``adelay`` + ``amix`` with normalisation off).

Usage::

    from narration_assembly_planner import plan, ffmpeg_argv
    p = plan([{"file": "c1.wav", "duration": 3.2, "boundary": "sentence", "words": [...]}, ...])
    argv = ffmpeg_argv(p, "narration.wav")
"""

from __future__ import annotations

PAUSES = {"sentence": 0.25, "paragraph": 0.6, "section": 1.0, "end": 0.0, "none": 0.0}


def plan(chunks: list[dict], lead_in: float = 0.3, tail: float = 0.5, pauses: dict | None = None) -> dict:
    pauses = {**PAUSES, **(pauses or {})}
    t = lead_in
    placed, words = [], []
    for i, c in enumerate(chunks):
        if c["duration"] <= 0:
            raise ValueError(f"chunk {i} has no duration")
        b = c.get("boundary", "sentence")
        if b not in pauses:
            raise ValueError(f"unknown boundary {b!r}")
        placed.append({"file": c.get("file"), "start": round(t, 4), "end": round(t + c["duration"], 4)})
        for w in c.get("words", []):
            words.append({**w, "start": round(t + w["start"], 4), "end": round(t + w["end"], 4)})
        t += c["duration"]
        if i < len(chunks) - 1:
            t += pauses[b]
    return {"chunks": placed, "words": words, "duration": round(t + tail, 4)}


def ffmpeg_argv(p: dict, out: str, sample_rate: int = 48000) -> list[str]:
    argv = ["ffmpeg", "-nostdin", "-y"]
    for c in p["chunks"]:
        if not c["file"]:
            raise ValueError("every chunk needs a file to build the mix")
        argv += ["-i", c["file"]]
    parts = []
    for i, c in enumerate(p["chunks"]):
        ms = int(round(c["start"] * 1000))
        parts.append(f"[{i}:a]aresample={sample_rate},aformat=channel_layouts=mono,adelay={ms}:all=1[d{i}]")
    n = len(p["chunks"])
    mix_in = "".join(f"[d{i}]" for i in range(n))
    parts.append(f"{mix_in}amix=inputs={n}:normalize=0:dropout_transition=0,apad=whole_dur={p['duration']}[out]")
    return argv + ["-filter_complex", ";".join(parts), "-map", "[out]", "-t", f"{p['duration']}",
                   "-c:a", "pcm_s16le", out]
