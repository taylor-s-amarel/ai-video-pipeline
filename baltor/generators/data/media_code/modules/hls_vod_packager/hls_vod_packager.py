"""Package a video as HLS VOD (segments + playlists) with ffmpeg.

``rendition_argv`` encodes one rendition with keyframes aligned to the
segment length (so every segment starts on a keyframe) and writes a VOD
media playlist; ``master_playlist`` writes the multivariant playlist that
lists renditions with bandwidth and resolution; ``parse_media_playlist``
reads segment durations back for checks.

Usage::

    from hls_vod_packager import rendition_argv, master_playlist
    cmd = rendition_argv("final.mp4", "hls/720p", height=1280, width=720, video_kbps=2500, segment_s=4, fps=30)
    open("hls/master.m3u8", "w").write(master_playlist([{"uri": "720p/index.m3u8", "bandwidth": 2800000,
                                                          "resolution": (720, 1280)}]))
"""

from __future__ import annotations

import math
import re


def rendition_argv(src: str, out_dir: str, width: int, height: int, video_kbps: int, segment_s: float = 4.0,
                   fps: float = 30, audio_kbps: int = 128) -> list[str]:
    if segment_s <= 0 or video_kbps <= 0:
        raise ValueError("segment length and bitrate must be > 0")
    g = int(round(segment_s * fps))
    return ["ffmpeg", "-nostdin", "-y", "-i", src,
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "veryfast", "-b:v", f"{video_kbps}k", "-maxrate", f"{int(video_kbps * 1.1)}k",
            "-bufsize", f"{video_kbps * 2}k", "-g", str(g), "-keyint_min", str(g), "-sc_threshold", "0",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", f"{audio_kbps}k",
            "-f", "hls", "-hls_time", f"{segment_s:g}", "-hls_playlist_type", "vod",
            "-hls_segment_filename", f"{out_dir}/seg_%03d.ts", f"{out_dir}/index.m3u8"]


def master_playlist(renditions: list[dict]) -> str:
    lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
    for r in sorted(renditions, key=lambda r: r["bandwidth"]):
        if "\n" in r["uri"] or r["uri"].startswith("#"):
            raise ValueError("bad rendition uri")
        attrs = f"BANDWIDTH={int(r['bandwidth'])}"
        if r.get("resolution"):
            attrs += f",RESOLUTION={r['resolution'][0]}x{r['resolution'][1]}"
        if r.get("codecs"):
            attrs += f',CODECS="{r["codecs"]}"'
        lines += [f"#EXT-X-STREAM-INF:{attrs}", r["uri"]]
    return "\n".join(lines) + "\n"


def parse_media_playlist(text: str) -> dict:
    if not text.startswith("#EXTM3U"):
        raise ValueError("not an M3U8 playlist")
    durs = [float(x) for x in re.findall(r"#EXTINF:([\d.]+)", text)]
    target = re.search(r"#EXT-X-TARGETDURATION:(\d+)", text)
    return {"segments": len(durs), "durations": durs, "total": round(sum(durs), 3),
            "target_duration": int(target.group(1)) if target else None, "vod": "#EXT-X-ENDLIST" in text}


def check_segments(info: dict) -> list[str]:
    probs = []
    if info["target_duration"] is not None:
        for i, d in enumerate(info["durations"]):
            if math.ceil(d) > info["target_duration"] + 0:
                probs.append(f"segment {i} ({d}s) exceeds target duration {info['target_duration']}s")
    if not info["vod"]:
        probs.append("playlist has no #EXT-X-ENDLIST (not a finished VOD)")
    return probs
