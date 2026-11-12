import math
from typing import List, Optional, Tuple, Unpack

import pygame
from pygame import SRCALPHA, Surface, draw, transform

from ..utils.timer import Timer
from .base import UIBase, UIOptions


class CooldownOverlay(UIBase):
    def __init__(
        self,
        timer: Timer,
        size: int | float,
        icon: Optional[Surface] = None,
        overlay_color: tuple[int, int, int, int] = (0, 0, 0, 255),
        disabled_color: tuple[int, int, int, int] = (50, 50, 55, 200),
        **overrides: Unpack[UIOptions],
    ) -> None:
        super().__init__({"width": int(size), "height": int(size), **overrides})

        self.timer = timer
        self.overlay_color = overlay_color
        self.disabled_color = disabled_color
        self.disabled = False

        content_w = self.box_model["content_width"]
        content_h = self.box_model["content_height"]

        r = min(content_w, content_h) / 2
        self.radius = r
        self.scalar: float = 1.0
        b = overrides.get("border_radius", 0)
        if b < r:
            self.scalar = (math.sqrt(2 * (r - b) ** 2) + b) / r

        self.overlay_parent = Surface((content_w, content_h), SRCALPHA)
        self._disabled_surf: Optional[Surface] = None
        self.add_plugin(self._draw_overlay)
        self.add_plugin(self._draw_disabled_overlay)
        if icon is not None:
            scale = content_w / icon.width, content_h / icon.height
            self.icon = transform.scale_by(icon, scale)
            self.add_plugin(self._draw_icon)

    def _draw_icon(self, surface: Surface) -> None:
        icon: Optional[Surface] = getattr(self, "icon", None)
        if icon is None:
            return

        center_x = self.box_model["content_width"] // 2
        center_y = self.box_model["content_height"] // 2

        rect = icon.get_rect(
            center=(
                self.box_model["left"] + center_x,
                self.box_model["top"] + center_y,
            )
        )

        if self.disabled:
            icon.set_alpha(80)
        elif not self.timer.reached():
            icon.set_alpha(150)
        elif icon.get_alpha() != 255:
            icon.set_alpha(255)
        surface.blit(icon, rect.topleft)

    def _draw_overlay(self, surface: Surface) -> None:
        if self.disabled or self.timer.reached():
            return

        progress = 1.0 - self.timer.ratio()

        center = (self.radius, self.radius)
        points: List[Tuple[float, float]] = [center]

        end_degrees = int(progress * 360)

        for degree in range(-90, end_degrees - 90):
            angle = math.radians(degree)
            x = self.radius + self.radius * math.cos(angle) * self.scalar
            y = self.radius + self.radius * math.sin(angle) * self.scalar
            points.append((x, y))

        op = self.overlay_parent
        op.fill((0, 0, 0, 0))

        if len(points) > 2:
            draw.polygon(op, self.overlay_color, points)

        pos = self.box_model["left"], self.box_model["top"]
        surface.blit(op, pos)

    def _draw_disabled_overlay(self, surface: Surface) -> None:
        if not self.disabled:
            return

        w = self.box_model["content_width"]
        h = self.box_model["content_height"]
        if self._disabled_surf is None or self._disabled_surf.get_size() != (w, h):
            self._disabled_surf = Surface((w, h), SRCALPHA)

        self._disabled_surf.fill(self.disabled_color)
        pos = self.box_model["left"], self.box_model["top"]
        surface.blit(self._disabled_surf, pos)
