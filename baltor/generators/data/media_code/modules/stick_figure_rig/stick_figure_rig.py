"""A stick-figure rig: forward kinematics, named poses and Pillow rendering.

Joint angles are in degrees, relative to the parent bone (0 = continuing the
parent's direction; positive = clockwise on screen, since y points down). The
root is the pelvis. ``pose_points`` returns 2D joint positions and ``render``
draws the figure with round caps on a transparent RGBA canvas. Opacity is
capped at 0.98 to match the house rule that no layer is fully opaque.

Usage::

    from stick_figure_rig import Rig, POSES
    rig = Rig(scale=1.0)
    pts = rig.pose_points(POSES["wave"], root=(540, 1200))
    img = rig.render(POSES["wave"], size=(1080, 1920), root=(540, 1200), color=(255, 255, 255))
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

# bone: (parent joint, child joint, length, rest direction in degrees for root-level bones)
BONES = [
    ("pelvis", "chest", 120, -90), ("chest", "neck", 30, None), ("neck", "head", 45, None),
    ("chest", "l_elbow", 70, None), ("l_elbow", "l_hand", 65, None),
    ("chest", "r_elbow", 70, None), ("r_elbow", "r_hand", 65, None),
    ("pelvis", "l_knee", 85, 90), ("l_knee", "l_foot", 85, None),
    ("pelvis", "r_knee", 85, 90), ("r_knee", "r_foot", 85, None),
]
JOINTS = ["chest", "neck", "head", "l_elbow", "l_hand", "r_elbow", "r_hand", "l_knee", "l_foot", "r_knee", "r_foot"]

POSES = {
    "stand": {"l_elbow": -160, "l_hand": 10, "r_elbow": 160, "r_hand": -10, "l_knee": 8, "l_foot": -4,
              "r_knee": -8, "r_foot": 4},
    "wave": {"l_elbow": -160, "l_hand": 10, "r_elbow": 70, "r_hand": 60, "l_knee": 8, "r_knee": -8},
    "cheer": {"l_elbow": -40, "l_hand": -10, "r_elbow": 40, "r_hand": 10, "l_knee": 10, "r_knee": -10},
    "walk_a": {"l_elbow": -150, "l_hand": 20, "r_elbow": 170, "r_hand": -20, "l_knee": -25, "l_foot": 20,
               "r_knee": 20, "r_foot": 15},
    "walk_b": {"l_elbow": -170, "l_hand": 20, "r_elbow": 150, "r_hand": -20, "l_knee": 20, "l_foot": 15,
               "r_knee": -25, "r_foot": 20},
    "think": {"chest": -5, "l_elbow": -160, "l_hand": 10, "r_elbow": 130, "r_hand": 120, "head": 15,
              "l_knee": 8, "r_knee": -8},
    "shrug": {"l_elbow": -100, "l_hand": -80, "r_elbow": 100, "r_hand": 80, "neck": 10, "l_knee": 8, "r_knee": -8},
}


class Rig:
    def __init__(self, scale: float = 1.0, lengths: dict | None = None):
        self.scale = scale
        self.lengths = {child: length for _, child, length, _ in BONES}
        if lengths:
            unknown = set(lengths) - set(self.lengths)
            if unknown:
                raise ValueError(f"unknown joints {sorted(unknown)}")
            self.lengths.update(lengths)

    def pose_points(self, pose: dict, root=(0.0, 0.0)) -> dict:
        unknown = set(pose) - set(JOINTS)
        if unknown:
            raise ValueError(f"unknown joints in pose: {sorted(unknown)}")
        pts = {"pelvis": (float(root[0]), float(root[1]))}
        absang = {}
        for parent, child, _, rest in BONES:
            # root-level bones (spine, legs) use their rest direction; others follow the parent bone
            base = rest if rest is not None else absang[parent]
            a = base + pose.get(child, 0.0)
            absang[child] = a
            px, py = pts[parent]
            length = self.lengths[child] * self.scale
            pts[child] = (px + length * math.cos(math.radians(a)), py + length * math.sin(math.radians(a)))
        return pts

    def render(self, pose: dict, size=(1080, 1920), root=None, color=(255, 255, 255), width: int | None = None,
               opacity: float = 0.98, head_radius: float | None = None) -> Image.Image:
        if not 0 <= opacity <= 0.98:
            raise ValueError("opacity must be within [0, 0.98]")
        root = root or (size[0] / 2, size[1] * 0.62)
        pts = self.pose_points(pose, root)
        w = width or max(2, int(round(14 * self.scale)))
        r = head_radius or 38 * self.scale
        img = Image.new("RGBA", tuple(size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        rgba = (*color[:3], int(round(255 * opacity)))
        for parent, child, _, _ in BONES:
            if child == "head":
                continue
            d.line([pts[parent], pts[child]], fill=rgba, width=w, joint="curve")
            for p in (pts[parent], pts[child]):
                d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=rgba)
        hx, hy = pts["head"]
        d.ellipse([hx - r, hy - r, hx + r, hy + r], outline=rgba, width=w)
        return img
