from __future__ import annotations

import math
import random

import pygame

from ..utils.timer import Timer

MODES = ("centered", "deadzone")


class Camera2D:
    __slots__ = (
        "x",
        "y",
        "viewport_w",
        "viewport_h",
        "mode",
        "target",
        "target_pos",
        "lerp_speed",
        "lookahead",
        "_velocity",
        "bounds",
        "deadzone",
        "_shake_timer",
        "_shake_intensity",
        "_shake_ox",
        "_shake_oy",
    )

    def __init__(
        self,
        viewport_width: int,
        viewport_height: int,
        mode: str = "centered",
    ) -> None:
        if viewport_width < 1 or viewport_height < 1:
            raise ValueError("viewport must be at least 1x1")
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
        self.x = 0.0
        self.y = 0.0
        self.viewport_w = viewport_width
        self.viewport_h = viewport_height
        self.mode = mode
        self.target = None
        self.target_pos: tuple[float, float] | None = None
        self.lerp_speed = 0.0
        self.lookahead: tuple[float, float] = (0.0, 0.0)
        self._velocity: tuple[float, float] = (0.0, 0.0)
        self.bounds: tuple[float, float, float, float] | None = None
        if mode == "deadzone":
            dw = viewport_width * 0.5
            dh = viewport_height * 0.5
            self.deadzone = pygame.Rect(
                (viewport_width - dw) / 2,
                (viewport_height - dh) / 2,
                dw,
                dh,
            )
        else:
            self.deadzone = None
        self._shake_timer = Timer(0.0, start_finished=True)
        self._shake_intensity = 0.0
        self._shake_ox = 0.0
        self._shake_oy = 0.0

    def follow(self, target) -> None:
        self.target = target
        self.target_pos = None

    def follow_at(self, x: float, y: float) -> None:
        self.target = None
        self.target_pos = (float(x), float(y))

    @property
    def velocity(self) -> tuple[float, float]:
        return self._velocity

    @velocity.setter
    def velocity(self, value: tuple[float, float]) -> None:
        try:
            vx, vy = value
        except (TypeError, ValueError):
            raise ValueError(f"velocity must be an (x, y) pair, got {value!r}") from None
        if not math.isfinite(vx) or not math.isfinite(vy):
            raise ValueError(f"velocity must be finite, got {(vx, vy)!r}")
        self._velocity = (float(vx), float(vy))

    def set_bounds(
        self,
        min_x: float,
        min_y: float,
        max_x: float,
        max_y: float,
    ) -> Camera2D:
        if min_x > max_x or min_y > max_y:
            raise ValueError(f"invalid bounds {(min_x, min_y, max_x, max_y)!r}")
        self.bounds = (min_x, min_y, max_x, max_y)
        return self

    def clear_bounds(self) -> None:
        self.bounds = None

    def shake(self, duration: float, intensity: float) -> None:
        if duration < 0 or not math.isfinite(duration):
            raise ValueError(f"duration must be finite and >= 0, got {duration!r}")
        if intensity < 0 or not math.isfinite(intensity):
            raise ValueError(f"intensity must be finite and >= 0, got {intensity!r}")
        self._shake_timer = Timer(duration)
        self._shake_intensity = float(intensity)

    def update(self, dt: float) -> None:
        if not math.isfinite(dt) or dt < 0:
            dt = 0.0
        focus = None
        if self.target is not None:
            focus = (float(self.target.x), float(self.target.y))
        elif self.target_pos is not None:
            focus = self.target_pos
        if focus is None:
            self.x += self._velocity[0] * dt
            self.y += self._velocity[1] * dt
        else:
            cx = focus[0] + self.lookahead[0]
            cy = focus[1] + self.lookahead[1]
            if self.mode == "centered":
                self._move_toward(
                    cx - self.viewport_w / 2,
                    cy - self.viewport_h / 2,
                    dt,
                )
            elif self.deadzone is not None:
                self._follow_deadzone(cx, cy, dt)
        if self.bounds is not None:
            min_x, min_y, max_x, max_y = self.bounds
            if max_x - min_x < self.viewport_w:
                self.x = min_x - (self.viewport_w - (max_x - min_x)) / 2
            else:
                self.x = max(min_x, min(self.x, max_x - self.viewport_w))
            if max_y - min_y < self.viewport_h:
                self.y = min_y - (self.viewport_h - (max_y - min_y)) / 2
            else:
                self.y = max(min_y, min(self.y, max_y - self.viewport_h))
        if not self._shake_timer.reached():
            self._shake_timer.update(dt)
            i = self._shake_intensity
            self._shake_ox = random.uniform(-i, i)
            self._shake_oy = random.uniform(-i, i)
            if self._shake_timer.reached():
                self._shake_ox = 0.0
                self._shake_oy = 0.0

    @property
    def offset(self) -> tuple[float, float]:
        return (self.x + self._shake_ox, self.y + self._shake_oy)

    def _move_toward(self, target_x: float, target_y: float, dt: float) -> None:
        if self.lerp_speed > 0:
            t = 1.0 - math.exp(-self.lerp_speed * dt)
            self.x += (target_x - self.x) * t
            self.y += (target_y - self.y) * t
        else:
            self.x = target_x
            self.y = target_y

    def _follow_deadzone(self, cx: float, cy: float, dt: float) -> None:
        sx = cx - self.x
        sy = cy - self.y
        dz = self.deadzone
        dx = dy = 0.0
        if sx < dz.left:
            dx = sx - dz.left
        elif sx > dz.right:
            dx = sx - dz.right
        if sy < dz.top:
            dy = sy - dz.top
        elif sy > dz.bottom:
            dy = sy - dz.bottom
        self._move_toward(self.x + dx, self.y + dy, dt)
