# Community source collections

Built 2026-10-10 by `generators/community_sources.py`. Each file is `feeds/<id>.json` (baltor.feed-collection/v1); the catalogue also renders it as JSON Feed, RSS and Markdown.

| Collection | Items | fetched | search-result | unverified | What it is for |
|---|---|---|---|---|---|
| `community-aggregators-forums` | 27 | 0 | 27 | 0 | Aggregators, research listings and official forums |
| `community-ai-oss-voices` | 42 | 0 | 42 | 0 | AI engineering, agent practitioners and open-source maintainers |
| `community-creator-marketing-security-voices` | 21 | 0 | 21 | 0 | Creator platform policy, creator economy, marketing and security sources |
| `community-gamedev-3d-educators` | 33 | 0 | 32 | 1 | Game dev, Godot, Blender, graphics and animation educators and news |
| `community-pennsylvania-startups` | 20 | 0 | 20 | 0 | Pennsylvania and startup communities and programmes |
| `community-reddit-ai-agents` | 27 | 0 | 27 | 0 | Subreddits: AI coding agents, local models and LLM engineering |
| `community-reddit-gamedev-3d-animation` | 37 | 0 | 37 | 0 | Subreddits: Godot, indie game dev, 3D, low-poly, pixel art and animation |
| `community-reddit-makers-home-cad` | 16 | 0 | 16 | 0 | Subreddits: home automation, ESP32, CAD and 3D printing |
| `community-reddit-marketing-security` | 16 | 0 | 16 | 0 | Subreddits: marketing, SEO, analytics and defensive security |
| `community-reddit-story-topic-mining` | 20 | 0 | 20 | 0 | Subreddits: topic mining for facts, history, comparisons and relationship stories |
| `community-reddit-video-audio-creators` | 33 | 0 | 33 | 0 | Subreddits: video editing, ffmpeg, YouTube/TikTok growth, faceless channels, TTS and audio |
| `community-releases-agents-ai` | 36 | 36 | 0 | 0 | Release feeds: coding agents, MCP and local AI tools |
| `community-releases-game-3d-2d` | 28 | 28 | 0 | 0 | Release feeds: Godot, Blender, 3D assets, 2D and animation tools |
| `community-releases-maker-marketing-security` | 17 | 17 | 0 | 0 | Release feeds: home automation, CAD, 3D printing, analytics and security tools |
| `community-releases-video-audio` | 21 | 21 | 0 | 0 | Release feeds: video, TTS and audio tools |
| `community-topic-mining-feeds` | 15 | 0 | 15 | 0 | Topic mining feeds for facts, history, science and trends |

Total: 409 items in 16 collections.

Export any collection to OPML for a feed reader:

```
python3 feed_collection_opml.py feeds/community-releases-agents-ai.json -o agents.opml
```
