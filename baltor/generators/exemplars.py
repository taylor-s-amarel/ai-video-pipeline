#!/usr/bin/env python3
"""One reference component for each of the twelve Baltor kinds.

These are the patterns every other generator follows. They are built around
the short-video house rules this project settled on and around the Baltor
service connection itself.
"""

from __future__ import annotations

import json

from _lib import GeneratorRun, agent_md, command_md, dumps, effects, skill_md

HOUSE_RULES = {
    "min_duration_s": 60,
    "aspect": "9:16",
    "resolution": [1080, 1920],
    "max_layer_opacity": 0.98,
    "title": {
        "first_frame": True,
        "position": "upper third, overlaid on the main photo",
        "center_y_max_fraction": 0.40,
        "color": "#FFD21F",
        "weight": "bold",
        "backing": "frosted glass: blurred background, 55-75% tint, feathered edges",
    },
    "captions": {
        "lines_on_screen": 1,
        "max_words": 7,
        "sync_tolerance_ms": 150,
        "keyword_pop": "scale 1.0 -> 1.12 -> 1.0 over 180 ms on the key word",
        "backing": "frosted glass",
        "forbidden": ["progress bars", "stacked label panels", "repeated section labels"],
    },
    "background": {
        "moving": True,
        "min_mean_frame_diff": 0.6,
        "layers_min": 5,
        "edges": "feathered, no hard rectangular cutouts",
    },
    "photo": {"min_frame_width_fraction": 0.80, "never_shrink_for_title": True},
    "facts": {"label": "FACT N", "numbers_required": True, "sources_required": True},
    "audio": {"narration": "neural TTS timed to captions", "music": "real instruments, credited when CC-BY",
              "music_under_voice_db": -18},
}

CHECK_MP4 = r'''"""Check an exported MP4 against measurable short-video house rules using ffprobe.

Usage: python mp4_qa_probe.py video.mp4 [--min-duration 60] [--json]
Exit status 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from dataclasses import asdict, dataclass


@dataclass
class Check:
    name: str
    passed: bool
    detail: str


def probe(path: str) -> dict:
    if not shutil.which("ffprobe"):
        raise RuntimeError("ffprobe is not installed")
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(out)


def evaluate(info: dict, min_duration: float = 60.0, width: int = 1080, height: int = 1920) -> list[Check]:
    streams = info.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)
    duration = float(info.get("format", {}).get("duration", 0) or 0)
    checks = [Check("duration", duration >= min_duration, f"{duration:.2f}s (minimum {min_duration:.0f}s)")]
    if video is None:
        checks.append(Check("video_stream", False, "no video stream"))
    else:
        w, h = int(video.get("width", 0)), int(video.get("height", 0))
        checks.append(Check("resolution", (w, h) == (width, height), f"{w}x{h} (expected {width}x{height})"))
        checks.append(Check("codec", video.get("codec_name") in {"h264", "hevc"}, str(video.get("codec_name"))))
        checks.append(Check("pixel_format", video.get("pix_fmt") == "yuv420p", str(video.get("pix_fmt"))))
    checks.append(Check("audio_stream", audio is not None, audio.get("codec_name", "") if audio else "no audio"))
    if audio is not None:
        checks.append(Check("audio_rate", int(audio.get("sample_rate", 0)) >= 44100, f"{audio.get('sample_rate')} Hz"))
    faststart = info.get("format", {}).get("format_name", "")
    checks.append(Check("container", "mp4" in faststart, faststart))
    return checks


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("video")
    ap.add_argument("--min-duration", type=float, default=60.0)
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    checks = evaluate(probe(a.video), a.min_duration, a.width, a.height)
    if a.json:
        print(json.dumps([asdict(c) for c in checks], indent=2))
    else:
        for c in checks:
            print(f"{'PASS' if c.passed else 'FAIL'}  {c.name:<14} {c.detail}")
    return 0 if all(c.passed for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''

TEST_CHECK_MP4 = r'''import mp4_qa_probe as m


def info(duration=64.0, w=1080, h=1920, audio=True):
    streams = [{"codec_type": "video", "width": w, "height": h, "codec_name": "h264", "pix_fmt": "yuv420p"}]
    if audio:
        streams.append({"codec_type": "audio", "codec_name": "aac", "sample_rate": "48000"})
    return {"streams": streams, "format": {"duration": str(duration), "format_name": "mov,mp4,m4a,3gp,3g2,mj2"}}


def test_full_length_vertical_video_passes():
    assert all(c.passed for c in m.evaluate(info()))


def test_short_preview_fails_duration():
    checks = {c.name: c for c in m.evaluate(info(duration=6.0))}
    assert not checks["duration"].passed


def test_missing_audio_fails():
    checks = {c.name: c for c in m.evaluate(info(audio=False))}
    assert not checks["audio_stream"].passed


def test_wrong_resolution_fails():
    checks = {c.name: c for c in m.evaluate(info(w=1920, h=1080))}
    assert not checks["resolution"].passed
'''

VIDEO_SPEC_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://github.com/taylor-s-amarel/ai-video-pipeline/baltor/contract-schemas/short-video-spec",
    "title": "Short video spec",
    "description": "Everything a renderer needs for one vertical short: hook title, scenes, layers, captions, narration and music credits.",
    "type": "object",
    "additionalProperties": False,
    "required": ["title_hook", "duration_s", "format", "scenes", "narration", "music"],
    "properties": {
        "title_hook": {
            "type": "object", "additionalProperties": False,
            "required": ["text", "color", "position"],
            "properties": {
                "text": {"type": "string", "minLength": 2, "maxLength": 48},
                "color": {"type": "string", "pattern": "^#[0-9A-Fa-f]{6}$"},
                "position": {"enum": ["upper-third-over-photo", "center-over-photo"]},
                "backing": {"enum": ["frosted-glass", "none"], "default": "frosted-glass"},
                "hold_s": {"type": "number", "minimum": 0.8, "maximum": 4},
            },
        },
        "duration_s": {"type": "number", "minimum": 60, "maximum": 180},
        "format": {"enum": ["1080x1920", "1080x1350", "1920x1080"]},
        "scenes": {
            "type": "array", "minItems": 3,
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["start_s", "end_s", "layers"],
                "properties": {
                    "start_s": {"type": "number", "minimum": 0},
                    "end_s": {"type": "number", "exclusiveMinimum": 0},
                    "label": {"type": "string", "pattern": "^(FACT|TIP|STEP) [0-9]{1,2}$"},
                    "key_number": {"type": "string", "maxLength": 24},
                    "layers": {
                        "type": "array", "minItems": 1,
                        "items": {
                            "type": "object", "additionalProperties": False,
                            "required": ["kind", "source", "opacity"],
                            "properties": {
                                "kind": {"enum": ["background-video", "background-image", "grid-2x2", "photo",
                                                  "particles", "light", "texture", "overlay", "text"]},
                                "source": {"type": "string"},
                                "opacity": {"type": "number", "minimum": 0, "maximum": 0.98},
                                "blend": {"enum": ["normal", "screen", "multiply", "overlay", "soft-light", "add"]},
                                "feather_px": {"type": "number", "minimum": 0, "maximum": 200},
                                "motion": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
        "captions": {
            "type": "array",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["start_s", "end_s", "text"],
                "properties": {
                    "start_s": {"type": "number", "minimum": 0},
                    "end_s": {"type": "number", "exclusiveMinimum": 0},
                    "text": {"type": "string", "maxLength": 60},
                    "pop_word": {"type": "string"},
                },
            },
        },
        "narration": {
            "type": "object", "additionalProperties": False, "required": ["engine", "voice"],
            "properties": {
                "engine": {"type": "string"},
                "voice": {"type": "string"},
                "words_per_minute": {"type": "number", "minimum": 120, "maximum": 175},
            },
        },
        "music": {
            "type": "object", "additionalProperties": False, "required": ["title", "licence"],
            "properties": {
                "title": {"type": "string"},
                "artist": {"type": "string"},
                "licence": {"type": "string"},
                "url": {"type": "string", "format": "uri"},
                "attribution": {"type": "string"},
                "gain_db": {"type": "number", "maximum": -6},
            },
        },
        "sources": {"type": "array", "items": {"type": "string", "format": "uri"}},
    },
}


def scene(i, start, end, label=None, number=None):
    s = {
        "start_s": start, "end_s": end,
        "layers": [
            {"kind": "background-video", "source": "ocean-waves-loop", "opacity": 0.92, "motion": "loop"},
            {"kind": "grid-2x2", "source": "four-motion-panels", "opacity": 0.35, "blend": "screen"},
            {"kind": "light", "source": "soft-light-sweep", "opacity": 0.4, "blend": "add"},
            {"kind": "particles", "source": "dust-bokeh", "opacity": 0.3, "blend": "screen"},
            {"kind": "photo", "source": f"photo-{i:02d}.jpg", "opacity": 0.98, "feather_px": 48, "motion": "ken-burns-in"},
        ],
    }
    if label:
        s["label"] = label
    if number:
        s["key_number"] = number
    return s


VALID_EXAMPLE = {
    "title_hook": {"text": "SHE LIVED UNDERWATER FOR 14 DAYS", "color": "#FFD21F",
                   "position": "upper-third-over-photo", "backing": "frosted-glass", "hold_s": 2.2},
    "duration_s": 64,
    "format": "1080x1920",
    "scenes": [scene(1, 0, 16, "FACT 1", "14 days"), scene(2, 16, 32, "FACT 2", "50 feet"),
               scene(3, 32, 48, "FACT 3", "86 hours"), scene(4, 48, 64, "FACT 4", "35 species")],
    "captions": [{"start_s": 2.3, "end_s": 4.1, "text": "In 1970, five scientists", "pop_word": "1970"}],
    "narration": {"engine": "kokoro-82m", "voice": "af_heart", "words_per_minute": 150},
    "music": {"title": "With These Hands", "artist": "Scott Buckley", "licence": "CC-BY-4.0",
              "url": "https://www.scottbuckley.com.au/library/with-these-hands/",
              "attribution": "Music: “With These Hands” by Scott Buckley, CC BY 4.0", "gain_db": -18},
    "sources": ["https://www.nasa.gov/"],
}

INVALID_EXAMPLE = json.loads(json.dumps(VALID_EXAMPLE))
INVALID_EXAMPLE["duration_s"] = 6
INVALID_EXAMPLE["scenes"][0]["layers"][4]["opacity"] = 1.0

HOOK_PY = r'''#!/usr/bin/env python3
"""PreToolUse hook: refuse a `git commit` when staged changes contain something that looks like a credential.

Claude Code passes the tool call as JSON on stdin. Exit code 2 blocks the call and shows stderr to the agent.
Works for any harness that can run a command before a shell call and read JSON from stdin.
"""

import json
import re
import subprocess
import sys

PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_-]{24,}"),
    re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9]{32,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
]


def staged_additions() -> str:
    proc = subprocess.run(["git", "diff", "--cached", "--unified=0", "--no-color"],
                          capture_output=True, text=True)
    return "\n".join(line[1:] for line in proc.stdout.splitlines()
                     if line.startswith("+") and not line.startswith("+++"))


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (event.get("tool_input") or {}).get("command", "")
    if not re.search(r"\bgit\b[^|;&]*\bcommit\b", command):
        return 0
    added = staged_additions()
    hits = [p.pattern for p in PATTERNS if p.search(added)]
    if hits:
        print("Blocked: staged changes contain what looks like a credential "
              f"({len(hits)} pattern(s)). Remove it, rotate the key, and stage again.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

with GeneratorRun(__file__) as run:
    # 1. skill
    run.component(
        "skill", "short_video_house_style",
        title="Short-video house style",
        summary="The settled look for 60+ second vertical shorts: bold yellow hook over the photo, frosted text, moving layered background, synced one-line captions.",
        subkind="style-preset", domain="video",
        files={
            "SKILL.md": skill_md(
                "short-video-house-style",
                "Use when planning, rendering or reviewing a vertical short (Reels, Shorts, TikTok) for this project. "
                "Gives the measurable house rules for title, captions, layers, background motion, narration and music.",
                """
# Short-video house style

Apply every rule below unless the user changes one explicitly. Each rule has a
measurable check so a render can be verified before it is sent.

## Deliver
- Full videos only: at least 60 seconds, 1080x1920, H.264 + AAC. No short previews unless asked.
- Never resend an older video as new work.

## Title hook (first frame)
- Bold yellow (`#FFD21F`), on the first frame, placed in the **upper third and overlaid on the main photo**.
  Never shrink or move the photo to make room for it.
- Behind it: a frosted-glass panel (blurred background, 55-75% tint, feathered edges).
- The title is its own short hook (2-7 words), not a copy of the first caption.

## Captions
- One synced line at a time, at most 7 words, frosted backing, within 150 ms of the spoken words.
- A small pop on the key word (scale 1.0 -> 1.12 -> 1.0 over 180 ms).
- No progress bars, stacked label panels or repeated section labels.
- `FACT N` / `TIP N` labels pop in when a new item starts; the key number sits under the label.

## Layers and background
- At least five layers; the background visibly moves for the whole video (video loop, 2x2 motion grid, light, particles, texture).
- No visual layer is fully opaque: every layer is at most 98% opacity.
- Feathered edges; never a hard rectangular cutout.
- The main photo stays large: at least 80% of the frame width.

## Audio
- Neural narration (for example Kokoro) at 140-160 words per minute, captions timed from the speech.
- Real music (recorded or well-arranged instruments) about 18 dB under the voice. Credit CC-BY music in the post text.

## Content
- Lead with a specific, curiosity-creating hook. Use real numbers, dates and outcomes, each with a source.

## Verify before sending
Run `scripts/check_rules.py spec.json` on the render spec and the `mp4_qa_probe` module on the export.
""",
            ),
            "rules.json": dumps(HOUSE_RULES),
            "scripts/check_rules.py": r'''#!/usr/bin/env python3
"""Check a short-video spec (see the short_video_spec contract schema) against the house rules in ../rules.json."""

import json
import sys
from pathlib import Path

RULES = json.loads((Path(__file__).resolve().parents[1] / "rules.json").read_text())


def problems(spec: dict) -> list[str]:
    out = []
    if spec.get("duration_s", 0) < RULES["min_duration_s"]:
        out.append(f"duration {spec.get('duration_s')}s is under {RULES['min_duration_s']}s")
    title = spec.get("title_hook", {})
    if title.get("color", "").upper() != RULES["title"]["color"]:
        out.append(f"title colour {title.get('color')} is not {RULES['title']['color']}")
    if title.get("position") != "upper-third-over-photo":
        out.append("title must sit in the upper third over the photo")
    for i, scene in enumerate(spec.get("scenes", [])):
        for layer in scene.get("layers", []):
            if layer.get("opacity", 1) > RULES["max_layer_opacity"]:
                out.append(f"scene {i + 1}: layer {layer.get('source')} opacity {layer['opacity']} > {RULES['max_layer_opacity']}")
        if len(scene.get("layers", [])) < RULES["background"]["layers_min"]:
            out.append(f"scene {i + 1}: fewer than {RULES['background']['layers_min']} layers")
        if not any(l.get("kind", "").startswith(("background-video", "grid-2x2")) for l in scene.get("layers", [])):
            out.append(f"scene {i + 1}: no moving background layer")
    for c in spec.get("captions", []):
        if len(c.get("text", "").split()) > RULES["captions"]["max_words"]:
            out.append(f"caption '{c['text']}' is longer than {RULES['captions']['max_words']} words")
    return out


if __name__ == "__main__":
    found = problems(json.loads(Path(sys.argv[1]).read_text()))
    for p in found:
        print("FAIL", p)
    print("all house rules pass" if not found else f"{len(found)} problem(s)")
    sys.exit(1 if found else 0)
''',
        },
        tags=["video", "shorts", "style", "captions", "house-rules"],
        step_kinds=["plan", "render", "review"],
        effects_=effects(filesystem="read", executes="python"),
        examples=["Render the Sylvia Earle short in house style", "Review this export against the house rules"],
    )

    # 2. code module
    run.component(
        "code-module", "mp4_qa_probe",
        title="MP4 QA probe",
        summary="Checks an exported MP4 with ffprobe: minimum duration, 1080x1920, H.264/yuv420p, AAC audio present. Exit 1 on any failure.",
        subkind="qa-check", domain="video",
        files={"mp4_qa_probe.py": CHECK_MP4, "test_mp4_qa_probe.py": TEST_CHECK_MP4},
        entry="mp4_qa_probe.py",
        tags=["video", "qa", "ffprobe", "mp4"],
        step_kinds=["verify", "render"],
        effects_=effects(filesystem="read", executes="python", side_effects=["runs ffprobe"]),
        depends_on=[{"identity": "ffprobe", "external": True}],
    )

    # 3. contract schema
    run.component(
        "contract-schema", "short_video_spec",
        title="Short video spec",
        summary="JSON Schema for one vertical short: hook title, 60+ s duration, scenes with layers capped at 98% opacity, captions, narration and credited music.",
        subkind="render-recipe", domain="video",
        files={
            "schema.json": dumps(VIDEO_SPEC_SCHEMA),
            "examples/sylvia-earle-underwater.json": dumps(VALID_EXAMPLE),
            "examples/invalid-short-and-opaque.json": dumps(INVALID_EXAMPLE),
        },
        tags=["video", "schema", "render", "contract"],
        step_kinds=["plan", "render", "verify"],
    )

    # 4. hook
    run.component(
        "hook", "block_staged_secrets",
        title="Block commits that stage credentials",
        summary="PreToolUse hook that refuses a git commit when the staged diff contains something that looks like an API key or private key.",
        subkind="guardrail", domain="security",
        files={
            "hook.py": HOOK_PY,
            "hook.json": dumps({"events": ["PreToolUse"], "matcher": "Bash",
                                "command": "python3 .baltor/hooks/block-staged-secrets/hook.py", "timeout": 20}),
            "settings.fragment.json": dumps({"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": "python3 .baltor/hooks/block-staged-secrets/hook.py", "timeout": 20}]}]}}),
        },
        tags=["security", "git", "secrets", "guardrail"],
        step_kinds=["secure", "build"],
        effects_=effects(filesystem="read", executes="python", side_effects=["runs git diff --cached"]),
    )

    # 5. subagent
    run.component(
        "subagent", "short_video_rules_reviewer",
        title="Short-video rules reviewer",
        summary="Reviews a rendered short and its spec against the house rules and returns pass/fail per rule with frame timestamps.",
        subkind="review-lens", domain="video",
        files={"agent.md": agent_md(
            "short-video-rules-reviewer",
            "Use after a short video is rendered and before it is sent. Checks the export and its spec against the house rules and reports every failure with a timestamp.",
            """
You review one rendered vertical short before anyone sees it.

1. Run `python3 mp4_qa_probe.py <video>` (the mp4_qa_probe code module) and the house-style
   `scripts/check_rules.py <spec.json>`. Record every FAIL.
2. Extract frames at 0.0 s, 1.0 s and every 5 s with
   `ffmpeg -ss T -i video.mp4 -frames:v 1 frame_T.png` and inspect them:
   - first frame: bold yellow title in the upper third over the photo, frosted backing, photo not shrunk;
   - one caption line, no progress bars or stacked labels;
   - background visibly different between consecutive frames;
   - no hard rectangular cutouts or watermark patches.
3. Compare caption timings with the narration's word timestamps when they exist; flag drift over 150 ms.
4. Report a table: rule, pass/fail, evidence (timestamp or measured value), fix. Do not say a rule
   passed unless you measured it; say "not checked" instead.
""", tools=["Read", "Bash", "Glob"])},
        tags=["video", "review", "qa", "subagent"],
        step_kinds=["review", "verify"],
        effects_=effects(filesystem="read", executes="shell", side_effects=["runs ffmpeg/ffprobe to extract frames"]),
        harnesses=["claude-code", "opencode", "baltor-harness"],
    )

    # 6. command
    run.component(
        "command", "render_short",
        title="/render-short",
        summary="Slash command that turns a topic into a full 60+ second house-style short: script with sources, spec, render, QA, then delivery.",
        subkind="workflow", domain="video",
        files={"command.md": command_md(
            "Make a full house-style vertical short from a topic",
            """
Make one complete short about: $ARGUMENTS

1. Research 4-10 specific facts with numbers and dates. Keep the source URL for each.
2. Write the hook title (2-7 words) and a 140-160 wpm narration script that runs 60-90 seconds.
3. Write `spec.json` that validates against the `short_video_spec` contract schema.
4. Generate narration, time captions from the speech, render with at least five moving layers.
5. Run the `short-video-rules-reviewer` subagent. Fix every FAIL and re-render.
6. Deliver the full MP4 with a posting caption and any music credit. Never deliver a preview instead.
""", argument_hint="<topic>")},
        tags=["video", "command", "workflow"],
        step_kinds=["plan", "render", "publish"],
        harnesses=["claude-code", "opencode", "baltor-harness"],
    )

    # 7. instruction file
    run.component(
        "instruction-file", "video_render_step_instructions",
        title="Instructions for a video render step",
        summary="CLAUDE.md / AGENTS.md section for a step that renders video: deliver full exports, keep stated rules, verify before sending.",
        subkind="step-template", domain="video",
        files={"INSTRUCTIONS.md": """
## Video render step

- Read the house rules (`short-video-house-style` skill) before writing any render code.
- Keep a rule ledger: every rule the user states goes in `RULES.md` in this step and is checked before each render.
  A new request never silently drops an older rule; ask only when two rules conflict.
- Deliver full-length exports. Do not send short previews unless the user asks for one.
- Save the editable source and the export to durable storage before reporting success.
- Report measured results only. Write "not checked" for anything you did not measure.
- Do not suggest paid services when an open-source tool does the job. Do not ask for approvals already given.
"""},
        tags=["video", "instructions", "claude-md", "agents-md"],
        step_kinds=["render"],
    )

    # 8. rules
    run.component(
        "rules", "short_video_standing_rules",
        title="Short-video standing rules",
        summary="Numbered, testable rule set for shorts with machine-readable thresholds (duration, opacity cap, title placement, caption sync).",
        subkind="rule-set", domain="video",
        files={
            "RULES.md": """
# Short-video standing rules

1. Full video, 60 s or longer. Check: ffprobe duration >= 60.
2. Bold yellow hook title on the first frame, upper third, over the photo. Check: title box centre y <= 40% of height.
3. Frosted-glass backing behind the title and captions. Check: backing layer has blur > 0 and opacity 0.55-0.75.
4. No visual layer above 98% opacity. Check: every spec layer opacity <= 0.98.
5. Background visibly moves throughout. Check: mean absolute frame difference in a background region > 0.6 (0-255 scale) for every 2 s window.
6. One caption line at a time, <= 7 words, synced within 150 ms. Check: caption start vs word timestamp.
7. Key word pops; no progress bars or stacked labels. Check: spec has no progress/label layers.
8. Photo stays large: >= 80% of frame width; never shrunk for the title.
9. Feathered edges; no hard rectangular cutouts. Check: visual review of frames at 0 s and every 5 s.
10. Real numbers with sources for every fact. Check: each FACT scene has key_number and a source URL.
11. Music is real and credited when CC-BY. Check: spec.music.attribution present for CC-BY.
""",
            "rules.json": dumps(HOUSE_RULES),
        },
        tags=["video", "rules", "qa"],
        step_kinds=["render", "review"],
    )

    # 9. protocol server configuration
    run.component(
        "protocol-server-configuration", "baltor_service_mcp",
        title="Baltor service MCP connection",
        summary="MCP entries that connect Claude Code, Codex and OpenCode to the Baltor endpoint over streamable HTTP with a bearer token from the environment.",
        subkind="harness-adapter", domain="baltor",
        files={
            "mcp.json": dumps({"mcpServers": {"baltor": {
                "type": "http", "url": "https://baltor.ai/mcp",
                "headers": {"Authorization": "Bearer ${BALTOR_SERVICE_TOKEN}"}}}}),
            "codex.toml": '[mcp_servers.baltor]\nurl = "https://baltor.ai/mcp"\nbearer_token_env_var = "BALTOR_SERVICE_TOKEN"\n',
            "opencode.json": dumps({"$schema": "https://opencode.ai/config.json", "mcp": {"baltor": {
                "type": "remote", "url": "https://baltor.ai/mcp", "enabled": True,
                "headers": {"Authorization": "Bearer {env:BALTOR_SERVICE_TOKEN}"}}}}),
            "README.md": """
# Baltor service MCP connection

Tools served: `intelligence_search(query)` and `provisioning_read(identity, expected_digest)`.
Create one client token per device or tool and keep it in `BALTOR_SERVICE_TOKEN`; the files hold
only the variable name. Check the service first: `curl https://baltor.ai/api/v1/capabilities`.

Until the hosted endpoint is live, the `baltor_local_catalog_mcp` configuration serves the same two
tools from this repository's catalogue over stdio.
""",
        },
        tags=["baltor", "mcp", "streamable-http", "connection"],
        step_kinds=["build", "research"],
        effects_=effects(network="declared", hosts=["baltor.ai"], secrets=["BALTOR_SERVICE_TOKEN"]),
    )

    # 10. harness settings
    run.component(
        "harness-settings", "claude_code_media_project_settings",
        title="Claude Code settings for a media project",
        summary="Project settings that allow ffmpeg/ffprobe and the catalogue tool, deny reading .env and credentials, and wire the secrets hook.",
        subkind="settings-profile", domain="video",
        files={"settings.json": dumps({
            "permissions": {
                "allow": ["Bash(ffmpeg:*)", "Bash(ffprobe:*)", "Bash(python3 baltor/tools/baltor_catalog.py:*)",
                          "Bash(git status:*)", "Bash(git diff:*)"],
                "deny": ["Read(./.env)", "Read(./.env.*)", "Read(./config/client_secret.json)",
                         "Read(./.youtube_credentials.json)"],
            },
            "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [
                {"type": "command", "command": "python3 .baltor/hooks/block-staged-secrets/hook.py", "timeout": 20}]}]},
        })},
        entry="settings.json",
        tags=["claude-code", "settings", "permissions", "video"],
        step_kinds=["build", "render", "secure"],
        harnesses=["claude-code"],
        depends_on=[{"identity": "block_staged_secrets"}],
        install={"claude-code": {"path": ".baltor/settings/claude-code-media-project-settings/",
                                 "merge_into": ".claude/settings.json"}},
    )

    # 11. plugin manifest
    run.component(
        "plugin-manifest", "short_video_studio_plugin",
        title="Short Video Studio plugin",
        summary="Claude Code plugin manifest bundling the house-style skill, the rules reviewer subagent and the /render-short command.",
        subkind="plugin-bundle", domain="video",
        files={"plugin.json": dumps({
            "name": "short-video-studio",
            "version": "1.0.0",
            "description": "House-style vertical shorts: plan, render, review and deliver full 60+ second videos.",
            "author": {"name": "Baltor"},
            "license": "MIT",
            "keywords": ["video", "shorts", "captions", "ffmpeg"],
            "commands": ["./commands/render-short.md"],
            "agents": ["./agents/short-video-rules-reviewer.md"],
            "skills": ["./skills/short-video-house-style"],
        }), "README.md": """
# Short Video Studio plugin

Assemble the plugin directory from the catalogue:

```
python3 baltor/tools/baltor_catalog.py read render_short --out plugin/commands-src
python3 baltor/tools/baltor_catalog.py read short_video_rules_reviewer --out plugin/agents-src
python3 baltor/tools/baltor_catalog.py read short_video_house_style --out plugin/skills/short-video-house-style
```

Then copy `command.md` to `commands/render-short.md` and `agent.md` to `agents/short-video-rules-reviewer.md`,
and put this `plugin.json` in `plugin/.claude-plugin/plugin.json`.
"""},
        tags=["plugin", "claude-code", "video"],
        step_kinds=["build", "render"],
        harnesses=["claude-code"],
        depends_on=[{"identity": "short_video_house_style"}, {"identity": "short_video_rules_reviewer"},
                    {"identity": "render_short"}],
    )

    # 12. plugin marketplace
    run.component(
        "plugin-marketplace", "baltor_public_good_marketplace",
        title="Baltor Public Good plugin marketplace",
        summary="Marketplace listing for the free Public Good plugins in this repository, installable with /plugin marketplace add.",
        subkind="plugin-bundle", domain="baltor",
        files={"marketplace.json": dumps({
            "name": "baltor-public-good",
            "owner": {"name": "Baltor", "url": "https://github.com/taylor-s-amarel/ai-video-pipeline"},
            "metadata": {"description": "Free plugins built from the Baltor Public Good collection.", "version": "1.0.0"},
            "plugins": [{"name": "short-video-studio", "source": "./plugins/short-video-studio",
                         "description": "House-style vertical shorts: plan, render, review, deliver.", "version": "1.0.0"}],
        })},
        tags=["plugin", "marketplace", "claude-code"],
        step_kinds=["build"],
        harnesses=["claude-code"],
        depends_on=[{"identity": "short_video_studio_plugin"}],
    )
