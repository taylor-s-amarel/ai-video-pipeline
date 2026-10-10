"""Smooth camera follow with a dead zone, look-ahead and world bounds.

Uses the critically damped "smooth damp" spring (no overshoot, frame-rate
independent) popularised in Game Programming Gems 4 (Thomas Lowe), with:

* dead zone: the camera ignores target motion inside a box around the centre;
* look-ahead: the camera leads the target in its direction of travel;
* bounds: the camera view never leaves the world rectangle.

Useful for top-down and side-on game footage, map flyovers and following a
moving subject in 2.5D scenes.

Usage::

    from damped_follow_camera import FollowCamera
    cam = FollowCamera(view=(1080, 1920), world=(0, 0, 4000, 6000), smooth_time=0.25)
    for target in positions:
        cx, cy = cam.update(target, dt=1/30)
"""

from __future__ import annotations

from dataclasses import dataclass, field


def smooth_damp(current: float, target: float, velocity: float, smooth_time: float, dt: float,
                max_speed: float = float("inf")) -> tuple[float, float]:
    smooth_time = max(1e-4, smooth_time)
    omega = 2.0 / smooth_time
    x = omega * dt
    exp = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
    change = current - target
    max_change = max_speed * smooth_time
    change = max(-max_change, min(max_change, change))
    tgt = current - change
    temp = (velocity + omega * change) * dt
    velocity = (velocity - omega * temp) * exp
    out = tgt + (change + temp) * exp
    # prevent overshooting the original target
    if (target - current > 0) == (out > target):
        out = target
        velocity = (out - target) / dt if dt > 0 else 0.0
    return out, velocity


@dataclass
class FollowCamera:
    view: tuple[float, float]
    world: tuple[float, float, float, float] | None = None  # x0, y0, x1, y1
    smooth_time: float = 0.3
    dead_zone: tuple[float, float] = (0.0, 0.0)  # half-size in pixels
    look_ahead: float = 0.0  # seconds of target velocity to lead by
    position: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _vel: list[float] = field(default_factory=lambda: [0.0, 0.0])
    _last_target: tuple[float, float] | None = None
    _started: bool = False

    def update(self, target, dt: float) -> tuple[float, float]:
        tx, ty = float(target[0]), float(target[1])
        if not self._started:
            self.position = [tx, ty]
            self._started = True
            self._last_target = (tx, ty)
            return self._clamp()
        if self.look_ahead and dt > 0 and self._last_target is not None:
            tx += (tx - self._last_target[0]) / dt * self.look_ahead
            ty += (ty - self._last_target[1]) / dt * self.look_ahead
        self._last_target = (float(target[0]), float(target[1]))
        goal = []
        for axis, t in enumerate((tx, ty)):
            c, dz = self.position[axis], self.dead_zone[axis]
            if t > c + dz:
                goal.append(t - dz)
            elif t < c - dz:
                goal.append(t + dz)
            else:
                goal.append(c)
        for axis in (0, 1):
            self.position[axis], self._vel[axis] = smooth_damp(
                self.position[axis], goal[axis], self._vel[axis], self.smooth_time, dt)
        return self._clamp()

    def _clamp(self) -> tuple[float, float]:
        if self.world:
            x0, y0, x1, y1 = self.world
            hw, hh = self.view[0] / 2, self.view[1] / 2
            for axis, (lo, hi, half) in enumerate(((x0, x1, hw), (y0, y1, hh))):
                if hi - lo <= 2 * half:
                    self.position[axis] = (lo + hi) / 2
                else:
                    self.position[axis] = min(max(self.position[axis], lo + half), hi - half)
        return self.position[0], self.position[1]

    def view_rect(self) -> tuple[float, float, float, float]:
        return (self.position[0] - self.view[0] / 2, self.position[1] - self.view[1] / 2, self.view[0], self.view[1])
