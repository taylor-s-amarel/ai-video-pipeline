"""Custom pronunciations for TTS: respelling replacements and W3C PLS files.

Many local TTS engines accept only plain text, so the dependable fix for a
mispronounced name is a respelling ("Earle" -> "Earl", "Gamboa" ->
"Gam-BOH-ah"). ``apply`` replaces whole words case-insensitively (keeping
the original capitalisation style), longest entries first, never inside
other words. ``to_pls`` writes a Pronunciation Lexicon Specification 1.0
document for engines that read lexicons, with IPA or alias entries.

Usage::

    from pronunciation_lexicon import Lexicon
    lex = Lexicon({"Gamboa": "Gam-BOH-ah", "NOAA": "Noah", "Kokoro": "koh-KOH-roh"})
    lex.apply("Gamboa met NOAA staff.")     # 'Gam-BOH-ah met Noah staff.'
    open("names.pls", "w").write(lex.to_pls(lang="en-US"))
"""

from __future__ import annotations

import json
import re
from xml.sax.saxutils import escape


class Lexicon:
    def __init__(self, entries: dict[str, str] | None = None, ipa: dict[str, str] | None = None):
        self.entries = dict(entries or {})
        self.ipa = dict(ipa or {})
        for k in list(self.entries) + list(self.ipa):
            if not k.strip() or "\n" in k:
                raise ValueError(f"bad lexicon key {k!r}")

    @classmethod
    def from_json(cls, text: str) -> "Lexicon":
        data = json.loads(text)
        return cls(data.get("respell", {}), data.get("ipa", {}))

    def to_json(self) -> str:
        return json.dumps({"respell": self.entries, "ipa": self.ipa}, indent=2, ensure_ascii=False, sort_keys=True)

    def apply(self, text: str) -> str:
        if not self.entries:
            return text
        keys = sorted(self.entries, key=len, reverse=True)
        pattern = re.compile(r"(?<![\w-])(" + "|".join(re.escape(k) for k in keys) + r")(?![\w-])", re.I)
        lookup = {k.lower(): v for k, v in self.entries.items()}

        def rep(m):
            src, out = m.group(0), lookup[m.group(0).lower()]
            if src.isupper() and len(src) > 1 and not out.isupper():
                return out  # acronym key: use the respelling as written
            if src[0].isupper():
                return out[0].upper() + out[1:]
            return out[0].lower() + out[1:]
        return pattern.sub(rep, text)

    def to_pls(self, lang: str = "en-US") -> str:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<lexicon version="1.0" xmlns="http://www.w3.org/2005/01/pronunciation-lexicon"',
                 f'         alphabet="ipa" xml:lang="{escape(lang)}">']
        for word in sorted(set(self.entries) | set(self.ipa)):
            lines.append("  <lexeme>")
            lines.append(f"    <grapheme>{escape(word)}</grapheme>")
            if word in self.ipa:
                lines.append(f"    <phoneme>{escape(self.ipa[word])}</phoneme>")
            else:
                lines.append(f"    <alias>{escape(self.entries[word])}</alias>")
            lines.append("  </lexeme>")
        lines.append("</lexicon>")
        return "\n".join(lines) + "\n"
