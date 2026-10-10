
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
