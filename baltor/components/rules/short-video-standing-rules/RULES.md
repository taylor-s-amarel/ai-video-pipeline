
# Short-video standing rules (photographic contract v8)

1. Complete film, 60 s or longer, with a full arc. Check: ffprobe duration >= 60 and a storyboard with hook, turn and payoff.
2. Realistic large photo at exactly (54,96)-(1026,1824), 972x1728. Check: photo layer rect in the spec; never shrunk for text.
3. Exposed 5% border moves from first to last frame. Check: frame difference in the border region > 0.6 (0-255) in every 2 s window.
4. Bold yellow #FFD21F editorial title over the upper photo, glyph centre near y=320. Check: title bbox centre y in 12-22% of height.
5. Genuine frosted glass behind title, captions and credits: sampled composite, 48 px margin, blur radius 18, rounded 2.2 px feather. Check: backing pixels differ from an unblurred sample and follow the scene underneath.
6. No authored layer above 98% opacity (8-bit cap 249). Check: every spec layer opacity <= 0.98; rendered layer alpha <= 249.
7. Five-layer foundation plus four independently clocked 2x2 panels with 28 px feathered seams. Check: frozen-foreground control shows each panel moving.
8. Captions faithful to every spoken phrase, onset within 3 frames, trailing hold <= 0.5 s. Check: caption starts vs measured phrase starts.
9. Key-word pop; no progress bars, stacked labels or restarted badges mid-phrase. Check: spec has no such layers.
10. Feathered edges; no hard rectangular cutouts. Check: visual review of frames at 0 s, every caption transition and the ending.
11. Real numbers with sources for every fact. Check: each FACT scene has key_number and a claim-ledger source.
12. Kokoro af_heart at native speed, never time-stretched; music ~18 dB under voice, credited per the creator's terms. Check: recipe settings and credit text; listening pass recorded as performed or not.
