import math
from typing import List, Optional, Tuple, Unpack

import pygame
from pygame import SRCALPHA, Surface, draw

from ..utils.timer import Timer
from .base import UIBase, UIOptions
from .theming import UIStyle


class CooldownOverlay(UIBase):
    """Cooldown sweep over optional, shape-clipped icon/background art.

    ``icon=`` remains the concise HUD API; it is rendered through
    :class:`UIBase` as ``background_image`` and therefore uses the same
    content rectangle and ``style.radius`` clipping as the sweep.
    """
    def __init__(
        self,
        timer: Timer,
        size: int | float,
        icon: Optional[Surface] = None,
        overlay_color: tuple[int, int, int, int] = (0, 0, 0, 255),
        disabled_color: tuple[int, int, int, int] = (50, 50, 55, 200),
        style: UIStyle | None = None,
        background_image: Surface | None = None,
        **overrides: Unpack[UIOptions],
    ) -> None:
        if int(size) <= 0:
            raise ValueError(f"size must be > 0, got {size!r}")
        if icon is not None and background_image is not None:
            raise ValueError("pass either icon or background_image, not both")
        super().__init__(
            {"width": int(size), "height": int(size), **overrides},
            style=style,
            background_image=background_image if background_image is not None else icon,
        )

        self.timer = timer
        self.overlay_color = overlay_color
        self.disabled_color = disabled_color
        self.disabled = False

        self.overlay_parent = Surface((1, 1), SRCALPHA)
        self._disabled_surf: Optional[Surface] = None
        self._refresh_clip_geometry()
        self.add_plugin(self._draw_overlay)
        self.add_plugin(self._draw_disabled_overlay)

    def set_style(self, style: UIStyle) -> None:
        """Replace chrome and rebuild the matching sweep/disabled clip."""
        super().set_style(style)
        self._refresh_clip_geometry()

    def _refresh_clip_geometry(self) -> None:
        """Rebuild layers derived from content geometry and style radius."""
        content_w = max(0, self.box_model["content_width"])
        content_h = max(0, self.box_model["content_height"])
        r = min(content_w, content_h) / 2
        self.radius = r
        self.scalar = 1.0
        style_radius = self._resolved_style().radius
        if r > 0 and style_radius < r:
            self.scalar = (math.sqrt(2 * (r - style_radius) ** 2) + style_radius) / r

        self.overlay_parent = Surface((max(1, content_w), max(1, content_h)), SRCALPHA)
        self._disabled_surf = None
        content_radius = max(0, style_radius - self.border_width)
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

    def update(self, dt: float = 0.0) -> None:
        _ = dt

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
