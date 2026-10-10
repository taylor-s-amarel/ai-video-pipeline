"""Build ffmpeg ``zoompan`` filters for smooth, eased Ken Burns moves on a still.

The zoom follows an in-out-sine curve from ``z0`` to ``z1`` over ``frames``
output frames; x/y keep the focus point under the same normalised position.
zoompan positions are whole pixels, which causes visible jitter on slow moves;
``prescale`` first scales the still up (default 4x the output width) so the
rounding error becomes sub-pixel after the final downscale.

Usage::

    from ken_burns_zoompan_filter import zoompan_filter, command
    vf = zoompan_filter(frames=150, out_size=(1080, 1920), z0=1.0, z1=1.2, focus=(0.5, 0.4))
    argv = command("photo.jpg", "move.mp4", frames=150, fps=30, vf=vf)
"""

from __future__ import annotations


def zoompan_filter(frames: int, out_size=(1080, 1920), z0: float = 1.0, z1: float = 1.15,
                   focus=(0.5, 0.5), fps: float = 30, prescale: float = 4.0, cover: bool = True) -> str:
    if frames < 2:
        raise ValueError("frames must be >= 2")
    if z0 < 1 or z1 < 1:
        raise ValueError("zoompan zoom values must be >= 1")
    ow, oh = out_size
    fx, fy = focus
    if not (0 <= fx <= 1 and 0 <= fy <= 1):
        raise ValueError("focus must be within [0, 1]")
    parts = []
    if cover:
        # crop the still to the output aspect first so zoom 1.0 fills the frame
        parts.append(f"scale=w='if(gt(a,{ow}/{oh}),-2,{ow * prescale:.0f})':h='if(gt(a,{ow}/{oh}),{oh * prescale:.0f},-2)'")
        parts.append(f"crop={ow * prescale:.0f}:{oh * prescale:.0f}")
    elif prescale != 1:
        parts.append(f"scale={ow * prescale:.0f}:-2")
    p = f"on/{frames - 1}"
    z = f"{z0}+({z1}-{z0})*(1-cos(PI*{p}))/2"
    x = f"max(0,min(iw-iw/zoom,{fx}*iw-iw/zoom/2))"
    y = f"max(0,min(ih-ih/zoom,{fy}*ih-ih/zoom/2))"
    parts.append(f"zoompan=z='{z}':x='{x}':y='{y}':d={frames}:s={ow}x{oh}:fps={fps:g}")
    parts.append("setsar=1")
    return ",".join(parts)


def command(image: str, output: str, frames: int, fps: float = 30, vf: str | None = None,
            crf: int = 18) -> list[str]:
    """argv for rendering a single still into a move clip (no shell quoting needed)."""
    vf = vf or zoompan_filter(frames, fps=fps)
    return ["ffmpeg", "-nostdin", "-y", "-i", image, "-vf", vf, "-frames:v", str(frames),
            "-c:v", "libx264", "-crf", str(crf), "-pix_fmt", "yuv420p", "-movflags", "+faststart", output]
