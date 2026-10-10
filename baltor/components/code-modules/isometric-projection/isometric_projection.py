"""Isometric and 2:1 dimetric projection for 2.5D scenes and tile maps.

``project`` maps world (x, y, z) to screen (sx, sy) with y pointing down on
screen. Two modes:

* ``iso``: true isometric (axes 120 degrees apart, 30-degree ground lines)
* ``pixel``: the 2:1 "pixel art" dimetric used for tile games (ground lines
  rise 1 pixel per 2 across, about 26.565 degrees)

Also: tile <-> screen conversion for diamond tile maps, a depth key for
painter's-algorithm sorting and ground-plane unprojection (z = 0).

Usage::

    from isometric_projection import project, unproject_ground, tile_to_screen, screen_to_tile, depth_key
    project((3, 2, 1), unit=64, mode="pixel")
    tile_to_screen(5, 3, tile_w=128, tile_h=64)
"""

from __future__ import annotations

import math

ISO_COS = math.cos(math.radians(30))
ISO_SIN = math.sin(math.radians(30))


def _basis(mode: str):
    if mode == "iso":
        return ISO_COS, ISO_SIN
    if mode == "pixel":
        return 1.0, 0.5
    raise ValueError("mode must be 'iso' or 'pixel'")


def project(p, unit: float = 32.0, mode: str = "iso", origin=(0.0, 0.0)) -> tuple[float, float]:
    x, y, z = p
    cx, cy = _basis(mode)
    sx = (x - y) * cx * unit + origin[0]
    sy = (x + y) * cy * unit - z * unit + origin[1]
    return sx, sy


def unproject_ground(s, unit: float = 32.0, mode: str = "iso", origin=(0.0, 0.0)) -> tuple[float, float]:
    """Inverse of ``project`` for points on the ground plane (z = 0)."""
    cx, cy = _basis(mode)
    a = (s[0] - origin[0]) / (cx * unit)
    b = (s[1] - origin[1]) / (cy * unit)
    return (a + b) / 2, (b - a) / 2


def tile_to_screen(col: int, row: int, tile_w: float = 64, tile_h: float = 32, origin=(0.0, 0.0)):
    """Top corner of a diamond tile."""
    return (col - row) * tile_w / 2 + origin[0], (col + row) * tile_h / 2 + origin[1]


def screen_to_tile(sx: float, sy: float, tile_w: float = 64, tile_h: float = 32, origin=(0.0, 0.0)):
    """Integer tile under a screen point (diamond picking)."""
    x, y = sx - origin[0], sy - origin[1]
    col = (x / (tile_w / 2) + y / (tile_h / 2)) / 2
    row = (y / (tile_h / 2) - x / (tile_w / 2)) / 2
    return math.floor(col), math.floor(row)


def depth_key(p) -> tuple[float, float]:
    """Sort key: draw smaller keys first (further back)."""
    x, y, z = p
    return (x + y, z)


def sort_back_to_front(objects, key=lambda o: o["pos"]):
    return sorted(objects, key=lambda o: depth_key(key(o)))
