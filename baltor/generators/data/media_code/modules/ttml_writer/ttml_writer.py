"""TTML (Timed Text Markup Language) writer for caption delivery.

Writes a small, valid TTML 1.0 document (``http://www.w3.org/ns/ttml``)
with one region at the bottom, one style and a ``<p>`` per cue, times as
``HH:MM:SS.mmm``. Text is XML-escaped by ElementTree; line breaks become
``<br/>``. ``read`` parses such documents back (clock-time values with
fractional seconds, and offset times like ``12.5s``).

Usage::

    from ttml_writer import dumps, read
    xml = dumps([(1.0, 2.5, "Hello & welcome"), (2.6, 4.0, "Line one\\nLine two")], lang="en")
    cues = read(xml)
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

TT = "http://www.w3.org/ns/ttml"
TTS = "http://www.w3.org/ns/ttml#styling"
XML = "http://www.w3.org/XML/1998/namespace"
ET.register_namespace("", TT)
ET.register_namespace("tts", TTS)


def clock(seconds: float) -> str:
    if seconds < 0:
        raise ValueError("negative time")
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


def dumps(cues, lang: str = "en", font_family: str = "proportionalSansSerif", color: str = "white") -> str:
    tt = ET.Element(f"{{{TT}}}tt", {f"{{{XML}}}lang": lang})
    head = ET.SubElement(tt, f"{{{TT}}}head")
    styling = ET.SubElement(head, f"{{{TT}}}styling")
    ET.SubElement(styling, f"{{{TT}}}style", {"xml:id": "s1", f"{{{TTS}}}fontFamily": font_family,
                                               f"{{{TTS}}}color": color, f"{{{TTS}}}textAlign": "center"})
    layout = ET.SubElement(head, f"{{{TT}}}layout")
    ET.SubElement(layout, f"{{{TT}}}region", {"xml:id": "bottom", f"{{{TTS}}}origin": "10% 70%",
                                               f"{{{TTS}}}extent": "80% 20%", f"{{{TTS}}}displayAlign": "after"})
    body = ET.SubElement(tt, f"{{{TT}}}body", {"style": "s1", "region": "bottom"})
    div = ET.SubElement(body, f"{{{TT}}}div")
    for start, end, text in cues:
        if end <= start:
            raise ValueError(f"cue at {start} ends before it starts")
        p = ET.SubElement(div, f"{{{TT}}}p", {"begin": clock(start), "end": clock(end)})
        lines = text.split("\n")
        p.text = lines[0]
        for line in lines[1:]:
            br = ET.SubElement(p, f"{{{TT}}}br")
            br.tail = line
    xml = ET.tostring(tt, encoding="unicode")
    # ElementTree writes xml:id as a literal attribute name; that is the correct serialisation
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + xml + "\n"


def parse_time(value: str) -> float:
    v = value.strip()
    m = re.match(r"^(\d+):(\d{2}):(\d{2})(?:\.(\d+))?$", v)
    if m:
        h, mi, s, frac = m.groups()
        return int(h) * 3600 + int(mi) * 60 + int(s) + (int(frac) / 10 ** len(frac) if frac else 0)
    m = re.match(r"^([\d.]+)(h|m|s|ms)$", v)
    if m:
        n, unit = float(m[1]), m[2]
        return n * {"h": 3600, "m": 60, "s": 1, "ms": 0.001}[unit]
    raise ValueError(f"unsupported TTML time {value!r}")


def read(xml: str) -> list[tuple[float, float, str]]:
    root = ET.fromstring(xml.encode("utf-8") if isinstance(xml, str) else xml)
    out = []
    for p in root.iter(f"{{{TT}}}p"):
        parts = [p.text or ""]
        for child in p:
            if child.tag == f"{{{TT}}}br":
                parts.append("\n")
            else:
                parts.append("".join(child.itertext()))
            parts.append(child.tail or "")
        out.append((parse_time(p.get("begin")), parse_time(p.get("end")), "".join(parts)))
    return out
