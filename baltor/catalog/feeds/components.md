# Baltor components in this repository

Base components in release 3ae8b538466f (12 items; variants omitted).

Updated 2026-10-10. 12 items.

| Item | Kind | Licence | Summary |
|---|---|---|---|
| [Baltor Public Good plugin marketplace](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/plugin-marketplaces/baltor-public-good-marketplace) | repository | MIT | Marketplace listing for the free Public Good plugins in this repository, installable with /plugin marketplace add. |
| [Baltor service MCP connection](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/protocol-server-configs/baltor-service-mcp) | repository | MIT | MCP entries that connect Claude Code, Codex and OpenCode to the Baltor endpoint over streamable HTTP with a bearer token from the environment. |
| [Block commits that stage credentials](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/hooks/block-staged-secrets) | repository | MIT | PreToolUse hook that refuses a git commit when the staged diff contains something that looks like an API key or private key. |
| [Claude Code settings for a media project](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/harness-settings/claude-code-media-project-settings) | repository | MIT | Project settings that allow ffmpeg/ffprobe and the catalogue tool, deny reading .env and credentials, and wire the secrets hook. |
| [MP4 QA probe](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/code-modules/mp4-qa-probe) | repository | MIT | Checks an exported MP4 with ffprobe: minimum duration, 1080x1920, H.264/yuv420p, AAC audio present. Exit 1 on any failure. |
| [/render-short](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/commands/render-short) | repository | MIT | Slash command that turns a topic into a full 60+ second house-style short: script with sources, spec, render, QA, then delivery. |
| [Short-video house style](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/skills/short-video-house-style) | repository | MIT | Current photographic contract for 60+ s vertical shorts: 972x1728 photo, moving 5% border, yellow hook at y~320, genuine frosted glass, layers <= 249/255, faithful captions. |
| [Short-video rules reviewer](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/subagents/short-video-rules-reviewer) | repository | MIT | Reviews a rendered short and its spec against the house rules and returns pass/fail per rule with frame timestamps. |
| [Short video spec](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/contract-schemas/short-video-spec) | repository | MIT | JSON Schema for one vertical short: hook title, 60+ s duration, scenes with layers capped at 98% opacity, captions, narration and credited music. |
| [Short-video standing rules](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/rules/short-video-standing-rules) | repository | MIT | Numbered, testable rule set for shorts with machine-readable thresholds (duration, opacity cap, title placement, caption sync). |
| [Short Video Studio plugin](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/plugin-manifests/short-video-studio-plugin) | repository | MIT | Claude Code plugin manifest bundling the house-style skill, the rules reviewer subagent and the /render-short command. |
| [Instructions for a video render step](https://github.com/taylor-s-amarel/ai-video-pipeline/tree/main/baltor/components/instruction-files/video-render-step-instructions) | repository | MIT | CLAUDE.md / AGENTS.md section for a step that renders video: deliver full exports, keep stated rules, verify before sending. |
