"""Advanced SubStation Alpha (.ass) writer for styled, burned-in captions.

Produces a complete script that libass (ffmpeg ``ass``/``subtitles`` filters)
renders: ``[Script Info]`` with PlayResX/PlayResY matching the video, a
``[V4+ Styles]`` section and ``[Events]``. Colours are given as ``#RRGGBB``
plus opacity and converted to ASS ``&HAABBGGRR`` (ASS alpha 00 = opaque).
Plain caption text is escaped: braces become ``\\{`` / ``\\}`` (which libass
draws literally), newlines become ``\\N`` and a backslash is replaced with a
full-width reverse solidus so user text can never inject override tags.
Override tags you *want* go in ``Event.tags``.

Usage::

    from ass_subtitle_writer import Style, Event, Script
    s = Script(1080, 1920)
    s.styles.append(Style("Caption", font="Inter", size=72, color="#FFFFFF", outline=6, align=2, margin_v=360))
    s.events.append(Event(1.0, 2.4, "FIVE SCIENTISTS {LIVED}", style="Caption", tags="\\fad(80,80)"))
    open("captions.ass", "w", encoding="utf-8").write(s.dumps())
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

STYLE_FORMAT = ("Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, "
                "Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding")
EVENT_FORMAT = "Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"


def ass_color(hex_rgb: str, opacity: float = 1.0) -> str:
    """'#RRGGBB' + opacity (1 = opaque) -> '&HAABBGGRR'."""
    h = hex_rgb.lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", h):
        raise ValueError(f"colour must be #RRGGBB, got {hex_rgb!r}")
    if not 0 <= opacity <= 1:
        raise ValueError("opacity must be within [0, 1]")
    r, g, b = h[0:2], h[2:4], h[4:6]
    alpha = round((1 - opacity) * 255)
    return f"&H{alpha:02X}{b}{g}{r}".upper()


def ass_time(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("negative timestamp")
    cs = int(round(seconds * 100))
    h, cs = divmod(cs, 360000)
    m, cs = divmod(cs, 6000)
    s, cs = divmod(cs, 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def escape_text(text: str) -> str:
    return (text.replace("\\", "＼").replace("{", "\\{").replace("}", "\\}")
            .replace("\r\n", "\n").replace("\n", "\\N"))


@dataclass
class Style:
    name: str = "Default"
    font: str = "Arial"
    size: int = 64
    color: str = "#FFFFFF"
    opacity: float = 1.0
    secondary: str = "#FF0000"
    outline_color: str = "#000000"
    back_color: str = "#000000"
    back_opacity: float = 0.5
    bold: bool = True
    italic: bool = False
    scale_x: int = 100
    scale_y: int = 100
    spacing: float = 0
    angle: float = 0
    border_style: int = 1  # 1 outline + shadow, 3 opaque box
    outline: float = 4
    shadow: float = 0
    align: int = 2  # numpad layout: 1-3 bottom, 4-6 middle, 7-9 top
    margin_l: int = 60
    margin_r: int = 60
    margin_v: int = 120

    def line(self) -> str:
        if "," in self.name or "," in self.font:
            raise ValueError("style and font names may not contain commas")
        if self.align not in range(1, 10):
            raise ValueError("align must be 1-9")
        vals = [self.name, self.font, self.size, ass_color(self.color, self.opacity),
                ass_color(self.secondary), ass_color(self.outline_color), ass_color(self.back_color, self.back_opacity),
                -1 if self.bold else 0, -1 if self.italic else 0, 0, 0, self.scale_x, self.scale_y,
                f"{self.spacing:g}", f"{self.angle:g}", self.border_style, f"{self.outline:g}", f"{self.shadow:g}",
                self.align, self.margin_l, self.margin_r, self.margin_v, 1]
        return "Style: " + ",".join(str(v) for v in vals)


@dataclass
class Event:
    start: float
    end: float
    text: str
    style: str = "Default"
    tags: str = ""          # raw override tags without braces, e.g. "\\fad(80,80)\\pos(540,1500)"
    layer: int = 0
    raw: bool = False       # True: ``text`` already contains ASS markup and is not escaped

    def line(self) -> str:
        if self.end <= self.start:
            raise ValueError(f"event at {self.start}s ends before it starts")
        body = self.text if self.raw else escape_text(self.text)
        if self.tags:
            body = "{" + self.tags + "}" + body
        return f"Dialogue: {self.layer},{ass_time(self.start)},{ass_time(self.end)},{self.style},,0,0,0,,{body}"


@dataclass
class Script:
    play_res_x: int = 1080
    play_res_y: int = 1920
    title: str = "captions"
    wrap_style: int = 0
    styles: list = field(default_factory=list)
    events: list = field(default_factory=list)

    def dumps(self) -> str:
        styles = self.styles or [Style()]
        names = {s.name for s in styles}
        for e in self.events:
            if e.style not in names:
                raise ValueError(f"event uses undefined style {e.style!r}")
        lines = ["[Script Info]", f"Title: {self.title}", "ScriptType: v4.00+", f"WrapStyle: {self.wrap_style}",
                 "ScaledBorderAndShadow: yes", f"PlayResX: {self.play_res_x}", f"PlayResY: {self.play_res_y}",
                 "YCbCr Matrix: TV.709", "", "[V4+ Styles]", f"Format: {STYLE_FORMAT}"]
        lines += [s.line() for s in styles]
        lines += ["", "[Events]", f"Format: {EVENT_FORMAT}"]
        lines += [e.line() for e in sorted(self.events, key=lambda e: (e.start, e.layer))]
        return "\n".join(lines) + "\n"
