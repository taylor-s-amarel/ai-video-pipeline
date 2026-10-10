"""Named ffmpeg encode profiles for delivery, review proxies and masters.

Profiles are this project's own settings (not platform requirements):

* ``vertical-1080x1920-h264``: H.264 High, CRF 18, preset slow, yuv420p,
  2-second GOP, AAC 192 kb/s 48 kHz, ``+faststart`` (playback can start
  before the whole file downloads);
* ``landscape-1920x1080-h264``: same settings at 16:9;
* ``review-proxy-540x960``: small, fast file for quick review;
* ``master-ffv1-mkv``: lossless FFV1 video + FLAC audio for archiving
  editable masters.

``argv`` builds the full command; ``describe`` summarises a profile.

Usage::

    from ffmpeg_encode_profiles import argv
    cmd = argv("vertical-1080x1920-h264", "edit.mov", "final.mp4", fps=30)
"""

from __future__ import annotations

PROFILES = {
    "vertical-1080x1920-h264": {"size": (1080, 1920), "vcodec": ["-c:v", "libx264", "-profile:v", "high",
                                "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p"],
                                "acodec": ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"], "faststart": True,
                                "gop_s": 2.0, "ext": ".mp4"},
    "landscape-1920x1080-h264": {"size": (1920, 1080), "vcodec": ["-c:v", "libx264", "-profile:v", "high",
                                 "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p"],
                                 "acodec": ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"], "faststart": True,
                                 "gop_s": 2.0, "ext": ".mp4"},
    "review-proxy-540x960": {"size": (540, 960), "vcodec": ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
                             "-pix_fmt", "yuv420p"], "acodec": ["-c:a", "aac", "-b:a", "96k"], "faststart": True,
                             "gop_s": 2.0, "ext": ".mp4"},
    "master-ffv1-mkv": {"size": None, "vcodec": ["-c:v", "ffv1", "-level", "3", "-g", "1"],
                        "acodec": ["-c:a", "flac"], "faststart": False, "gop_s": None, "ext": ".mkv"},
}


def describe(name: str) -> dict:
    if name not in PROFILES:
        raise KeyError(f"unknown profile {name!r}; known: {', '.join(PROFILES)}")
    return dict(PROFILES[name])


def argv(profile: str, src: str, dst: str, fps: float | None = 30, extra_vf: str | None = None,
         audio: bool = True) -> list[str]:
    p = describe(profile)
    if not dst.endswith(p["ext"]):
        raise ValueError(f"{profile} writes {p['ext']} files")
    vf = []
    if extra_vf:
        vf.append(extra_vf)
    if p["size"]:
        w, h = p["size"]
        vf.append(f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,setsar=1")
    if fps:
        vf.append(f"fps={fps:g}")
    cmd = ["ffmpeg", "-nostdin", "-y", "-i", src]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += p["vcodec"]
    if p["gop_s"] and fps:
        g = int(round(p["gop_s"] * fps))
        cmd += ["-g", str(g), "-keyint_min", str(g), "-sc_threshold", "0"]
    cmd += p["acodec"] if audio else ["-an"]
    if p["faststart"]:
        cmd += ["-movflags", "+faststart"]
    return cmd + [dst]
