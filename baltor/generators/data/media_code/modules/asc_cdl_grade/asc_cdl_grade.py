"""ASC CDL colour grading: slope, offset, power and saturation.

The ASC Color Decision List applies, per channel,
``out = clamp(in * slope + offset) ** power``, then a saturation step around
Rec. 709 luma: ``luma + sat * (c - luma)``. CDLs are tiny, portable and
supported by most grading tools, so a grade made here can travel.

* ``apply`` grades float or uint8 RGB with numpy;
* ``to_cc_xml`` / ``from_cc_xml`` read and write a ColorCorrection (.cc)
  element;
* ``ffmpeg_lutrgb`` gives the slope/offset/power part as an ffmpeg
  ``lutrgb`` filter (saturation is not per-channel, so it is left out; add
  ``hue=s=...`` for an approximation).

Usage::

    from asc_cdl_grade import CDL, apply
    cdl = CDL(slope=(1.05, 1.0, 0.95), offset=(0.0, 0.0, 0.01), power=(1.0, 1.0, 1.05), saturation=1.1)
    graded = apply(img, cdl)
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

import numpy as np

W709 = np.array([0.2126, 0.7152, 0.0722])


@dataclass
class CDL:
    slope: tuple = (1.0, 1.0, 1.0)
    offset: tuple = (0.0, 0.0, 0.0)
    power: tuple = (1.0, 1.0, 1.0)
    saturation: float = 1.0
    id: str = "grade"

    def validate(self) -> None:
        if any(s < 0 for s in self.slope) or any(p <= 0 for p in self.power) or self.saturation < 0:
            raise ValueError("slope and saturation must be >= 0 and power > 0")


def apply(img: np.ndarray, cdl: CDL) -> np.ndarray:
    cdl.validate()
    a = np.asarray(img)
    u8 = a.dtype == np.uint8
    c = a[..., :3].astype(np.float64) / (255.0 if u8 else 1.0)
    c = np.clip(c * np.array(cdl.slope) + np.array(cdl.offset), 0, 1) ** np.array(cdl.power)
    luma = (c @ W709)[..., None]
    c = np.clip(luma + cdl.saturation * (c - luma), 0, 1)
    if u8:
        out = (c * 255 + 0.5).astype(np.uint8)
        return np.concatenate([out, a[..., 3:4]], -1) if a.shape[-1] == 4 else out
    return c


def _triple(v):
    return " ".join(f"{x:.6f}" for x in v)


def to_cc_xml(cdl: CDL) -> str:
    cc = ET.Element("ColorCorrection", id=cdl.id)
    sop = ET.SubElement(cc, "SOPNode")
    ET.SubElement(sop, "Slope").text = _triple(cdl.slope)
    ET.SubElement(sop, "Offset").text = _triple(cdl.offset)
    ET.SubElement(sop, "Power").text = _triple(cdl.power)
    sat = ET.SubElement(cc, "SatNode")
    ET.SubElement(sat, "Saturation").text = f"{cdl.saturation:.6f}"
    return ET.tostring(cc, encoding="unicode")


def from_cc_xml(text: str) -> CDL:
    root = ET.fromstring(text)
    cc = root if root.tag.endswith("ColorCorrection") else next(e for e in root.iter() if e.tag.endswith("ColorCorrection"))

    def find(tag):
        el = next((e for e in cc.iter() if e.tag.endswith(tag)), None)
        return el.text.split() if el is not None and el.text else None

    def trip(tag, default):
        v = find(tag)
        return tuple(float(x) for x in v) if v else default

    sat = find("Saturation")
    return CDL(trip("Slope", (1.0,) * 3), trip("Offset", (0.0,) * 3), trip("Power", (1.0,) * 3),
               float(sat[0]) if sat else 1.0, cc.get("id", "grade"))


def ffmpeg_lutrgb(cdl: CDL) -> str:
    cdl.validate()
    parts = []
    for ch, s, o, p in zip("rgb", cdl.slope, cdl.offset, cdl.power):
        parts.append(f"{ch}='255*pow(clip(val/255*{s:g}+{o:g},0,1),{p:g})'")
    return "lutrgb=" + ":".join(parts)
