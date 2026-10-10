"""Generate short-video topic ideas by crossing niches x angles x formats x hooks.

Deterministic (no network, no global random state): the same config, seed and history always give the
same ideas in the same order. Near-duplicates are removed, every idea gets a score with a per-scorer
breakdown, and the final pick is spread across formats, niches, subjects and hooks so a series does
not become one template repeated (the pattern platform "inauthentic content" rules target).

Ideas are prompts, not facts: every idea leaves here with ``status: "needs-sources"``.

Config (JSON file or dict)::

    {
      "niches":  [{"id": "space", "label": "Space", "subjects": ["Olympus Mons", "Europa"],
                   "risk": [], "exclude_formats": []}],
      "angles":  [{"id": "scale", "template": "how big {subject} really is",
                   "formats": ["size-scale-comparison", "versus-comparison"]}],
      "formats": [{"id": "size-scale-comparison", "label": "Size and scale comparison", "durations": [60, 90]}],
      "hooks":   [{"id": "really", "template": "How big is {subject}, really?", "formats": ["*"],
                   "angles": ["scale"]}],
      "weights": {"specificity": 1.0, "curiosity": 1.0, "format_fit": 1.0, "novelty": 1.0, "risk": 1.0},
      "limits":  {"max_per_format": 3, "max_per_niche": 4, "max_per_subject": 1, "max_per_hook": 3},
      "dedupe_threshold": 0.8
    }

Usage::

    python topic_matrix_generator.py config.json --limit 30 --seed 7 --history used_titles.txt
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import string
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

STOPWORDS = frozenset(
    "a an and are as at be by did do does for from how in into is it its of on or really than that the "
    "this to was what when where which who why will with you your".split()
)
CURIOSITY_MARKERS = ("?", " really", " actually", "nobody", "why ", "what if", " vs", " versus", " than ",
                     "secret", "hidden", "wrong", "myth", "before", "after", "still", "only")
QUESTION_OPENERS = ("how big", "how long", "how much", "how many", "how far", "how fast", "how old",
                    "why", "what if", "which", "who", "when")
RISK_PENALTY = {
    "regulated-finance": 0.35, "medical": 0.35, "legal": 0.3, "news": 0.25, "real-people": 0.25,
    "minors": 0.4, "tragedy": 0.3, "politics": 0.3, "user-generated": 0.3, "dangerous-activity": 0.35,
}
DEFAULT_WEIGHTS = {"specificity": 1.0, "curiosity": 1.0, "format_fit": 1.0, "novelty": 1.0, "risk": 1.0}
DEFAULT_LIMITS = {"max_per_format": 3, "max_per_niche": 4, "max_per_subject": 1, "max_per_hook": 3}

Scorer = Callable[["Idea", "Context"], float]


@dataclass
class Idea:
    niche: str
    subject: str
    angle: str
    format: str
    hook: str
    title: str
    angle_text: str
    durations: list[int] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    format_fit: float = 0.5
    score: float = 0.0
    score_breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def id(self) -> str:
        key = "|".join((self.niche, self.subject, self.angle, self.format, self.hook))
        return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]

    def to_dict(self) -> dict:
        return {
            "id": self.id, "niche": self.niche, "subject": self.subject, "angle": self.angle,
            "angle_text": self.angle_text, "format": self.format, "hook": self.hook, "title": self.title,
            "durations_s": self.durations, "score": round(self.score, 4),
            "score_breakdown": {k: round(v, 4) for k, v in sorted(self.score_breakdown.items())},
            "risk_flags": self.risk_flags, "status": "needs-sources",
        }


@dataclass
class Context:
    history_tokens: list[frozenset[str]]
    seed: int


def tokens(text: str) -> frozenset[str]:
    text = text.lower().translate(str.maketrans({c: " " for c in string.punctuation}))
    return frozenset(t for t in text.split() if t and t not in STOPWORDS)


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _fill(template: str, capitalize: bool = True, **values: str) -> str:
    out = template
    for k, v in values.items():
        out = out.replace("{" + k + "}", v)
    if re.search(r"\{[a-z_]+\}", out):
        raise ValueError(f"unfilled placeholder in template: {template!r}")
    return out[0].upper() + out[1:] if (out and capitalize) else out


def _allows(listing: Iterable[str] | None, value: str) -> bool:
    listing = list(listing or ["*"])
    return "*" in listing or value in listing


# ----------------------------------------------------------------------------- scorers

def score_specificity(idea: Idea, ctx: Context) -> float:
    s = 0.0
    words = idea.subject.split()
    if len(words) >= 2 or any(ch.isdigit() for ch in idea.subject) or idea.subject[:1].isupper():
        s += 0.6
    if idea.title.lower().startswith(QUESTION_OPENERS) or any(q in idea.title.lower() for q in QUESTION_OPENERS[:6]):
        s += 0.4
    return min(s, 1.0)


def score_curiosity(idea: Idea, ctx: Context) -> float:
    text = " " + idea.title.lower() + " "
    hits = sum(1 for m in CURIOSITY_MARKERS if m in text)
    return min(hits / 2.0, 1.0)


def score_format_fit(idea: Idea, ctx: Context) -> float:
    return idea.format_fit


def score_novelty(idea: Idea, ctx: Context) -> float:
    if not ctx.history_tokens:
        return 1.0
    t = tokens(idea.title + " " + idea.subject)
    return 1.0 - max(jaccard(t, h) for h in ctx.history_tokens)


def score_risk(idea: Idea, ctx: Context) -> float:
    """Returned as a penalty (subtracted)."""
    return min(sum(RISK_PENALTY.get(f, 0.2) for f in idea.risk_flags), 1.0)


SCORERS: dict[str, Scorer] = {
    "specificity": score_specificity,
    "curiosity": score_curiosity,
    "format_fit": score_format_fit,
    "novelty": score_novelty,
    "risk": score_risk,
}
PENALTIES = {"risk"}


# ----------------------------------------------------------------------------- generation

def expand(config: dict) -> list[Idea]:
    """Every compatible niche x subject x angle x format x hook combination, in a stable order."""
    niches = sorted(config.get("niches", []), key=lambda n: n["id"])
    angles = sorted(config.get("angles", []), key=lambda a: a["id"])
    formats = {f["id"]: f for f in config.get("formats", [])}
    hooks = sorted(config.get("hooks", []), key=lambda h: h["id"])
    out: list[Idea] = []
    for niche in niches:
        excluded = set(niche.get("exclude_formats", []))
        for subject in sorted(dict.fromkeys(niche.get("subjects", []))):
            for angle in angles:
                if not _allows(angle.get("niches"), niche["id"]):
                    continue
                angle_formats = angle.get("formats", ["*"])
                for fid in sorted(formats):
                    if fid in excluded or not _allows(angle_formats, fid):
                        continue
                    fit = 1.0 if fid in angle_formats else 0.5
                    for hook in hooks:
                        if not _allows(hook.get("formats"), fid) or not _allows(hook.get("angles"), angle["id"]):
                            continue
                        angle_raw = _fill(angle["template"], capitalize=False, subject=subject)
                        angle_text = _fill(angle["template"], subject=subject)
                        title = _fill(hook["template"], subject=subject, angle=angle_raw,
                                      format=formats[fid].get("label", fid))
                        out.append(Idea(
                            niche=niche["id"], subject=subject, angle=angle["id"], format=fid,
                            hook=hook["id"], title=title, angle_text=angle_text,
                            durations=list(formats[fid].get("durations", [60])),
                            risk_flags=sorted(set(niche.get("risk", [])) | set(angle.get("risk", []))),
                            format_fit=fit,
                        ))
    return out


def _tiebreak(seed: int, idea_id: str) -> str:
    return hashlib.sha1(f"{seed}:{idea_id}".encode()).hexdigest()


def score_all(ideas: list[Idea], ctx: Context, weights: dict[str, float],
              scorers: dict[str, Scorer]) -> None:
    for idea in ideas:
        total = 0.0
        breakdown = {}
        for name, fn in scorers.items():
            w = weights.get(name, 1.0)
            if w == 0:
                continue
            value = float(fn(idea, ctx))
            breakdown[name] = value
            total += -w * value if name in PENALTIES else w * value
        idea.score = total
        idea.score_breakdown = breakdown


def dedupe(ideas: list[Idea], threshold: float = 0.8) -> list[Idea]:
    """Drop exact and near-duplicate titles (token Jaccard >= threshold); ideas must be pre-sorted best first."""
    kept: list[Idea] = []
    kept_tokens: list[frozenset[str]] = []
    seen_keys: set[str] = set()
    for idea in ideas:
        t = tokens(idea.title)
        key = " ".join(sorted(t)) + "|" + idea.format
        if key in seen_keys:
            continue
        if any(jaccard(t, k) >= threshold for k in kept_tokens):
            continue
        seen_keys.add(key)
        kept.append(idea)
        kept_tokens.append(t)
    return kept


def select_diverse(ideas: list[Idea], limit: int, limits: dict[str, int]) -> list[Idea]:
    counts: dict[tuple[str, str], int] = {}
    caps = {"format": limits.get("max_per_format"), "niche": limits.get("max_per_niche"),
            "subject": limits.get("max_per_subject"), "hook": limits.get("max_per_hook")}
    picked: list[Idea] = []
    for idea in ideas:
        if len(picked) >= limit:
            break
        ok = True
        for dim, cap in caps.items():
            if cap is None:
                continue
            value = idea.niche + "/" + idea.subject if dim == "subject" else getattr(idea, dim)
            if counts.get((dim, value), 0) >= cap:
                ok = False
                break
        if not ok:
            continue
        for dim in caps:
            value = idea.niche + "/" + idea.subject if dim == "subject" else getattr(idea, dim)
            counts[(dim, value)] = counts.get((dim, value), 0) + 1
        picked.append(idea)
    return picked


def generate(config: dict, limit: int = 30, seed: int = 0, history: Iterable[str] = (),
             scorers: dict[str, Scorer] | None = None) -> list[dict]:
    """Return up to ``limit`` scored, deduplicated, diversified ideas as dicts."""
    all_scorers = dict(SCORERS)
    all_scorers.update(scorers or {})
    weights = dict(DEFAULT_WEIGHTS)
    weights.update(config.get("weights", {}))
    limits = dict(DEFAULT_LIMITS)
    limits.update(config.get("limits", {}))
    ctx = Context(history_tokens=[tokens(h) for h in history if h.strip()], seed=seed)
    ideas = expand(config)
    score_all(ideas, ctx, weights, all_scorers)
    ideas.sort(key=lambda i: (-round(i.score, 9), _tiebreak(seed, i.id)))
    ideas = dedupe(ideas, float(config.get("dedupe_threshold", 0.8)))
    return [i.to_dict() for i in select_diverse(ideas, limit, limits)]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("config", help="JSON config with niches, angles, formats and hooks")
    ap.add_argument("--limit", type=int, default=30)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--history", help="text file of titles already used, one per line")
    ap.add_argument("--format", choices=["json", "tsv"], default="json")
    a = ap.parse_args(argv)
    config = json.loads(Path(a.config).read_text(encoding="utf-8"))
    history = Path(a.history).read_text(encoding="utf-8").splitlines() if a.history else []
    ideas = generate(config, a.limit, a.seed, history)
    if a.format == "json":
        print(json.dumps(ideas, indent=2, ensure_ascii=False))
    else:
        print("score\tformat\tniche\ttitle\trisk")
        for i in ideas:
            print(f"{i['score']:.3f}\t{i['format']}\t{i['niche']}\t{i['title']}\t{','.join(i['risk_flags'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
