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
        if int(size) <= 0:
            raise ValueError(f"size must be > 0, got {size!r}")
        super().__init__({"width": int(size), "height": int(size), **overrides})

        self.timer = timer
        self.overlay_color = overlay_color
        self.disabled_color = disabled_color
        self.disabled = False

        content_w = max(0, self.box_model["content_width"])
        content_h = max(0, self.box_model["content_height"])

        r = min(content_w, content_h) / 2
        self.radius = r
        self.scalar: float = 1.0
        b = self.border["radius"]
        if r > 0 and b < r:
            self.scalar = (math.sqrt(2 * (r - b) ** 2) + b) / r

        self.overlay_parent = Surface((max(1, content_w), max(1, content_h)), SRCALPHA)
        self._disabled_surf: Optional[Surface] = None
        # Rounded mask matching the content-box background shape, so the
        # icon, sweep, and disabled layers share one silhouette. Square
        # when the radius is 0 (no-op, skipped). Built once; the sweep
        # reuses it per frame with a single blit.
        content_radius = max(0, b - self.border["width"])
        if content_radius > 0 and content_w > 0 and content_h > 0:
            mask = Surface((content_w, content_h), SRCALPHA)
            mask.fill((0, 0, 0, 0))
            draw.rect(
                mask,
                (255, 255, 255, 255),
                (0, 0, content_w, content_h),
                border_radius=content_radius,
            )
            self._mask: Optional[Surface] = mask
        else:
            self._mask = None
        self.add_plugin(self._draw_overlay)
        self.add_plugin(self._draw_disabled_overlay)
        if icon is not None:
            scale = content_w / icon.width, content_h / icon.height
            scaled = transform.scale_by(icon.copy(), scale)
            canvas = Surface(scaled.get_size(), SRCALPHA)
            canvas.blit(scaled, (0, 0))
            if self._mask is not None:
                canvas.blit(self._mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.icon = canvas
            self.add_plugin(self._draw_icon)

    def update(self, dt: float = 0.0) -> None:
        # Read-only by design: the overlay never ticks the timer.
        # The owner of the timer advances it; HUD only reads
        # ratio()/reached(). Kept so Container.update() propagation
        # keeps working for mixed children.
        _ = dt

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

        if self._mask is not None:
            op.blit(self._mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

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
        if self._mask is not None:
            self._disabled_surf.blit(self._mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        pos = self.box_model["left"], self.box_model["top"]
        surface.blit(self._disabled_surf, pos)
