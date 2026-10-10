"""Build valid SSML 1.1 for engines that accept it.

Elements: ``speak`` (with xml:lang), ``break`` (time or strength), ``prosody``
(rate, pitch, volume), ``emphasis``, ``say-as``, ``sub`` and ``phoneme``
(IPA or x-sampa). Text is XML-escaped; attribute values are validated
against the SSML 1.1 value forms. Engine support varies: espeak-ng reads SSML
with its ``-m`` flag; Kokoro and Piper take plain text, so strip SSML or use
their own speed settings for them.

Usage::

    from ssml_builder import speak, brk, prosody, emphasis, say_as, sub
    doc = speak(["In ", say_as("1970", "date", format="y"), ", ", emphasis("five"), " scientists",
                 brk("400ms"), prosody("lived underwater.", rate="90%")], lang="en-US")
"""

from __future__ import annotations

import re
from xml.sax.saxutils import escape, quoteattr

NS = "http://www.w3.org/2001/10/synthesis"
STRENGTHS = {"none", "x-weak", "weak", "medium", "strong", "x-strong"}
RATE_WORDS = {"x-slow", "slow", "medium", "fast", "x-fast", "default"}
PITCH_WORDS = {"x-low", "low", "medium", "high", "x-high", "default"}
VOLUME_WORDS = {"silent", "x-soft", "soft", "medium", "loud", "x-loud", "default"}
EMPHASIS = {"strong", "moderate", "none", "reduced"}


def _content(parts) -> str:
    if isinstance(parts, str):
        return escape(parts)
    return "".join(p.xml if isinstance(p, Node) else escape(str(p)) for p in parts)


class Node:
    def __init__(self, xml: str):
        self.xml = xml

    def __str__(self) -> str:
        return self.xml


def brk(time: str | None = None, strength: str | None = None) -> Node:
    if time is not None and not re.fullmatch(r"\d+(\.\d+)?(ms|s)", time):
        raise ValueError("break time must look like 300ms or 1.5s")
    if strength is not None and strength not in STRENGTHS:
        raise ValueError(f"strength must be one of {sorted(STRENGTHS)}")
    attrs = (f" time={quoteattr(time)}" if time else "") + (f" strength={quoteattr(strength)}" if strength else "")
    return Node(f"<break{attrs}/>")


def prosody(content, rate: str | None = None, pitch: str | None = None, volume: str | None = None) -> Node:
    attrs = ""
    if rate is not None:
        if not (rate in RATE_WORDS or re.fullmatch(r"\d+(\.\d+)?%", rate)):
            raise ValueError("rate must be a keyword or a non-negative percentage like 90%")
        attrs += f" rate={quoteattr(rate)}"
    if pitch is not None:
        if not (pitch in PITCH_WORDS or re.fullmatch(r"[+-]?\d+(\.\d+)?(Hz|%|st)", pitch)):
            raise ValueError("pitch must be a keyword or a value like +2st, -10%, 120Hz")
        attrs += f" pitch={quoteattr(pitch)}"
    if volume is not None:
        if not (volume in VOLUME_WORDS or re.fullmatch(r"[+-]\d+(\.\d+)?dB", volume)):
            raise ValueError("volume must be a keyword or a value like +3dB")
        attrs += f" volume={quoteattr(volume)}"
    return Node(f"<prosody{attrs}>{_content(content)}</prosody>")


def emphasis(content, level: str = "moderate") -> Node:
    if level not in EMPHASIS:
        raise ValueError(f"level must be one of {sorted(EMPHASIS)}")
    return Node(f"<emphasis level={quoteattr(level)}>{_content(content)}</emphasis>")


def say_as(content: str, interpret_as: str, format: str | None = None) -> Node:
    if not re.fullmatch(r"[a-z-]+", interpret_as):
        raise ValueError("interpret-as must be a lower-case token")
    fmt = f" format={quoteattr(format)}" if format else ""
    return Node(f"<say-as interpret-as={quoteattr(interpret_as)}{fmt}>{escape(content)}</say-as>")


def sub(written: str, alias: str) -> Node:
    return Node(f"<sub alias={quoteattr(alias)}>{escape(written)}</sub>")


def phoneme(written: str, ph: str, alphabet: str = "ipa") -> Node:
    if alphabet not in ("ipa", "x-sampa"):
        raise ValueError("alphabet must be ipa or x-sampa")
    return Node(f"<phoneme alphabet={quoteattr(alphabet)} ph={quoteattr(ph)}>{escape(written)}</phoneme>")


def speak(content, lang: str = "en-US") -> str:
    if not re.fullmatch(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*", lang):
        raise ValueError("lang must be a BCP 47 tag like en-US")
    return (f'<speak version="1.1" xmlns="{NS}" xml:lang={quoteattr(lang)}>' + _content(content) + "</speak>")


def strip_ssml(ssml: str) -> str:
    """Plain text for engines without SSML support (sub aliases are spoken, breaks become spaces)."""
    t = re.sub(r'<sub alias="([^"]*)">[^<]*</sub>', lambda m: m.group(1), ssml)
    t = re.sub(r"<break[^>]*/>", " ", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&")
    return re.sub(r"\s{2,}", " ", t).strip()
