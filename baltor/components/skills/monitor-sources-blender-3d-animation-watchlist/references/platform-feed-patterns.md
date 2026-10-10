# Platform feed patterns and cautions

Checked on 2026-10-10. "Evidence" says how: **fetched** means a live feed of that shape was retrieved;
**docs** means the pattern comes from the platform's own documentation found in search results;
**third-party** means only feed directories or guides were found.

| Platform | Feed URL pattern | Evidence | Cautions |
|---|---|---|---|
| Reddit | `https://www.reddit.com/r/<name>/.rss`, also `/new/.rss`, `/top/.rss?t=day` | third-party guides (reddit.com blocks research crawlers) | Datacenter IPs and generic user agents are often blocked; private or quarantined communities have no feed; Data API Terms restrict commercial reuse; posts belong to their authors. |
| GitHub | `https://github.com/<owner>/<repo>/releases.atom`, `tags.atom`, `commits/<branch>.atom` | fetched (100+ feeds) | Unauthenticated rate limits per IP; some feeds exceed 1 MB; repositories without releases return an empty feed, use tags or commits instead; mirrors (Blender, Krita, Kdenlive, FFmpeg) expose tags only. |
| YouTube | `https://www.youtube.com/feeds/videos.xml?channel_id=UC...` | third-party | Needs the 24-character channel id, not a @handle; a third-party report notes intermittent 404s since December 2025; fall back to the channel page. |
| arXiv | `https://rss.arxiv.org/rss/<cat>` or `/atom/<cat>`; combine with `+` | docs (info.arxiv.org/help/rss.html) | Updated once a day around midnight US Eastern; no weekend announcements; review arXiv's Terms of Use for APIs. |
| Discourse forums | `https://<forum>/latest.rss`, `top.rss`, `hot.rss`, `c/<slug>/<id>.rss` | docs (meta.discourse.org "Finding Discourse RSS feeds") | `latest` orders by last reply, not creation; replies themselves need `/posts.json`. |
| Hacker News | `https://news.ycombinator.com/rss` (front page) | third-party, consistent | Only the front page is consistently documented as official. |
| hnrss.org | `https://hnrss.org/newest?q=a+OR+b`, `/frontpage`, `/show` | third-party docs | Community-run service, not Y Combinator. |
| Substack | `https://<publication>/feed` | Feedly help docs | Publications can disable RSS; paid posts are truncated; only `/feed` works, not `/rss` or `/feed.xml`. |
| Mastodon | `https://<instance>/@<user>.rss` | third-party guides | Public posts only; boosts are not included; use the account's home instance. |
| Bluesky | `https://bsky.app/profile/<handle>/rss` | third-party (OpenRSS) | Accounts that limit posts to logged-in users publish nothing. |
| Wikipedia | `https://<lang>.wikipedia.org/w/api.php?action=featuredfeed&feed=<name>&feedformat=atom` with `<name>` = `onthisday`, `featured` or `potd` | MediaWiki FeaturedFeeds docs | Text is CC BY-SA; picture-of-the-day feeds carry no licence data, open each file page; send a descriptive User-Agent. |
| itch.io | `https://<user>.itch.io/<game>/devlog.rss` | examples in search results | Per-game devlogs only. |
| Google Trends | `https://trends.google.com/trending/rss?geo=US` | third-party tools | No official API; Google can change the URL without notice. |
| WordPress sites | `/feed/` | widely used convention | Confirm with autodiscovery before relying on it. |

## When a site has no confirmed feed

1. Fetch the page once and run `discover_feeds(html, base_url)` to read `<link rel="alternate">` tags.
2. If nothing is advertised, monitor the page at most daily and compare a content hash; do not scrape
   item text into a public product.
3. Record the result in the watchlist (`note`) so the next run does not repeat the search.

## Polite defaults

| Setting | Default | Notes |
|---|---|---|
| Minimum interval per host | 5 s | 60 s for reddit.com; respect any documented limit that is stricter |
| Polls per feed per day | 24 | Daily is enough for arXiv, Wikipedia and policy pages |
| Timeout | 20 s | |
| Maximum body | 5 MB | Some GitHub release feeds are 1-2 MB |
| Backoff on 429/503 | Retry-After, else 5 min doubling | Stop the host for the run after three failures |
| User-Agent | tool name + version + contact URL | Never impersonate a browser |
