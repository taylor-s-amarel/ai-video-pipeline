
# Short Video Studio plugin

Assemble the plugin directory from the catalogue:

```
python3 baltor/tools/baltor_catalog.py read render_short --out plugin/commands-src
python3 baltor/tools/baltor_catalog.py read short_video_rules_reviewer --out plugin/agents-src
python3 baltor/tools/baltor_catalog.py read short_video_house_style --out plugin/skills/short-video-house-style
```

Then copy `command.md` to `commands/render-short.md` and `agent.md` to `agents/short-video-rules-reviewer.md`,
and put this `plugin.json` in `plugin/.claude-plugin/plugin.json`.
