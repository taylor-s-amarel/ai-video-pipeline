"""ASS karaoke timing tags from word timestamps (\\k, \\kf, \\ko).

Each word gets a karaoke tag whose duration (centiseconds) runs until the
next word starts, so the highlight follows the voice. The text before the
first word starts is covered by a leading empty tag; rounding errors are
carried forward so the total never drifts from the real word times.

Usage::

    from ass_karaoke_tags import karaoke_text
    karaoke_text(words, cue_start=1.0, mode="kf")
    # '{\\k20}{\\kf35}FIVE {\\kf48}SCIENTISTS ...'
"""

from __future__ import annotations

MODES = {"k", "kf", "K", "ko"}


def _esc(t: str) -> str:
    return t.replace("\\", "\uff3c").replace("{", "\\{").replace("}", "\\}")


def karaoke_text(words: list[dict], cue_start: float, cue_end: float | None = None, mode: str = "kf") -> str:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {sorted(MODES)}")
    if not words:
        return ""
    parts = []
    lead_cs = int(round((words[0]["start"] - cue_start) * 100))
    if lead_cs < 0:
        raise ValueError("first word starts before the cue")
    if lead_cs:
        parts.append(f"{{\\k{lead_cs}}}")
    elapsed_cs = lead_cs
    for i, w in enumerate(words):
        nxt = words[i + 1]["start"] if i + 1 < len(words) else (cue_end if cue_end is not None else w["end"])
        target_cs = int(round((nxt - cue_start) * 100))
        dur = max(1, target_cs - elapsed_cs)
        elapsed_cs += dur
        sep = " " if i + 1 < len(words) else ""
        parts.append(f"{{\\{mode}{dur}}}{_esc(w['word'])}{sep}")
    return "".join(parts)


def durations(karaoke: str) -> list[int]:
    import re
    return [int(x) for x in re.findall(r"\\(?:kf|ko|k|K)(\d+)", karaoke)]
