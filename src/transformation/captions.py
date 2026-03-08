"""Generate animated captions (CapCut-style) from transcription data."""

import re
from pathlib import Path
from dataclasses import dataclass

from src.analysis.transcriber import TranscriptionResult, WordTimestamp


@dataclass
class CaptionStyle:
    font_name: str = "Arial"
    font_size: int = 52
    primary_color: str = "&H00FFFFFF"   # white (ASS BGR format)
    highlight_color: str = "&H0000FFFF"  # yellow
    outline_color: str = "&H00000000"    # black
    outline_width: int = 3
    shadow: int = 0
    bold: bool = True
    alignment: int = 2  # bottom center
    margin_v: int = 60
    margin_l: int = 40
    margin_r: int = 40


# ASS header template
ASS_HEADER = """[Script Info]
Title: Auto-generated captions
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{font_name},{font_size},{primary_color},&H000000FF,{outline_color},&H80000000,{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},{margin_l},{margin_r},{margin_v},1
Style: Highlight,{font_name},{font_size},{highlight_color},&H000000FF,{outline_color},&H80000000,{bold},0,0,0,100,100,0,0,1,{outline_width},{shadow},{alignment},{margin_l},{margin_r},{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _format_ass_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _chunk_words(words: list[WordTimestamp], max_words: int = 5,
                  max_duration: float = 3.0) -> list[list[WordTimestamp]]:
    """Group words into display chunks."""
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)

        chunk_duration = current_chunk[-1].end - current_chunk[0].start
        if len(current_chunk) >= max_words or chunk_duration >= max_duration:
            chunks.append(current_chunk)
            current_chunk = []

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def generate_captions_ass(transcript: TranscriptionResult,
                           output_path: str | Path,
                           style: CaptionStyle | None = None,
                           mode: str = "word_highlight") -> Path:
    """Generate ASS subtitle file with animated captions.

    Modes:
    - "word_highlight": Show word chunks, highlight current word (CapCut-style)
    - "sentence": Show full sentences with fade-in
    - "karaoke": Karaoke-style progressive fill
    """
    style = style or CaptionStyle()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    header = ASS_HEADER.format(
        font_name=style.font_name,
        font_size=style.font_size,
        primary_color=style.primary_color,
        highlight_color=style.highlight_color,
        outline_color=style.outline_color,
        outline_width=style.outline_width,
        shadow=style.shadow,
        bold="-1" if style.bold else "0",
        alignment=style.alignment,
        margin_l=style.margin_l,
        margin_r=style.margin_r,
        margin_v=style.margin_v,
    )

    events = []

    # Collect all words from all segments
    all_words = []
    for seg in transcript.segments:
        all_words.extend(seg.words)

    if not all_words:
        # Fallback to sentence-level if no word timestamps
        mode = "sentence"

    if mode == "word_highlight":
        chunks = _chunk_words(all_words)

        for chunk in chunks:
            chunk_start = chunk[0].start
            chunk_end = chunk[-1].end

            for i, word in enumerate(chunk):
                # Build text line: all words in chunk, current word highlighted
                parts = []
                for j, w in enumerate(chunk):
                    if j == i:
                        parts.append(
                            f"{{\\rHighlight}}{w.word.upper()}{{\\rCaption}}"
                        )
                    else:
                        parts.append(w.word.upper())

                text = " ".join(parts)
                start_time = _format_ass_time(word.start)
                end_time = _format_ass_time(word.end)

                events.append(
                    f"Dialogue: 0,{start_time},{end_time},Caption,,0,0,0,,{text}"
                )

    elif mode == "karaoke":
        chunks = _chunk_words(all_words, max_words=6)

        for chunk in chunks:
            chunk_start = chunk[0].start
            chunk_end = chunk[-1].end
            start_time = _format_ass_time(chunk_start)
            end_time = _format_ass_time(chunk_end)

            # Build karaoke tags
            kara_parts = []
            for w in chunk:
                duration_cs = int((w.end - w.start) * 100)
                kara_parts.append(f"{{\\kf{duration_cs}}}{w.word.upper()}")

            text = " ".join(kara_parts)
            events.append(
                f"Dialogue: 0,{start_time},{end_time},Caption,,0,0,0,,{text}"
            )

    elif mode == "sentence":
        for seg in transcript.segments:
            start_time = _format_ass_time(seg.start)
            end_time = _format_ass_time(seg.end)
            text = seg.text.upper()
            # Fade in/out effect
            fade = "{\\fad(200,200)}"
            events.append(
                f"Dialogue: 0,{start_time},{end_time},Caption,,0,0,0,,{fade}{text}"
            )

    content = header + "\n".join(events) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def generate_srt(transcript: TranscriptionResult,
                  output_path: str | Path) -> Path:
    """Generate standard SRT subtitle file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    for i, seg in enumerate(transcript.segments, 1):
        start_h = int(seg.start // 3600)
        start_m = int((seg.start % 3600) // 60)
        start_s = int(seg.start % 60)
        start_ms = int((seg.start % 1) * 1000)

        end_h = int(seg.end // 3600)
        end_m = int((seg.end % 3600) // 60)
        end_s = int(seg.end % 60)
        end_ms = int((seg.end % 1) * 1000)

        lines.append(str(i))
        lines.append(
            f"{start_h:02d}:{start_m:02d}:{start_s:02d},{start_ms:03d} --> "
            f"{end_h:02d}:{end_m:02d}:{end_s:02d},{end_ms:03d}"
        )
        lines.append(seg.text)
        lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return output_path
