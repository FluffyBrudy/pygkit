from __future__ import annotations

from typing import Unpack

import pygame
from pygame import Surface
from pygame.typing import ColorLike

from ..utils.interpolation import SimpleInterpolation
from .base import UIBase, UIOptions
from .theming import UIStyle


PROGRESSBAR_DEFAULTS: UIOptions = {
    "width": 250,
    "height": 24,
    "border_width": 2,
    "padding_x": 2,
    "padding_y": 2,
    "margin_x": 0,
    "margin_y": 0,
}


class ProgressBarUI(UIBase):
    """Progress track whose chrome comes from :class:`UIStyle`.

    ``fg`` is the procedural fill color. ``track_image``, ``fill_image``,
    and ``empty_tint`` remain widget-specific authored-art inputs.
    """

    DEFAULT_STYLE: UIStyle = {
        "bg": (33, 37, 43, 255),
        "fg": (255, 255, 255, 255),
        "border": (40, 44, 52, 255),
        "radius": 6,
    }

    def __init__(
        self,
        *,
        style: UIStyle | None = None,
        background_image: Surface | None = None,
        track_image: Surface | None = None,
        fill_image: Surface | None = None,
        empty_tint: ColorLike | None = (0, 0, 0, 110),
        **overrides: Unpack[UIOptions],
    ) -> None:
        options: UIOptions = {**PROGRESSBAR_DEFAULTS, **overrides}
        super().__init__(options, style=style, background_image=background_image)
        self.interpolation = SimpleInterpolation(speed=3.0)
        self.track_image = track_image
        self.fill_image = fill_image
        self.empty_tint = empty_tint
        self._silhouettes: dict[tuple[int, tuple[int, int, int, int]], Surface] = {}

    def invalidate(self) -> None:
        super().invalidate()
        if hasattr(self, "_silhouettes"):
            self._silhouettes.clear()

    def set_progress(self, value: float) -> None:
        self.interpolation.set(value)

    def get_progress(self) -> float:
        return self.interpolation.current

    def update(self, dt: float = 0.0) -> None:
        self.interpolation.update(dt)

    @staticmethod
    def _rgba(color: ColorLike | None) -> tuple[int, int, int, int] | None:
        if color is None:
            return None
        parsed = pygame.Color(color)
        return parsed.r, parsed.g, parsed.b, parsed.a

    def _silhouette(self, color: ColorLike | None) -> Surface | None:
        """Track-shaped color layer, built once per normalized color."""
        if color is None or self.track_image is None:
            return None
        rgba = self._rgba(color)
        key = (id(self.track_image), rgba)
        cached = self._silhouettes.get(key)
        if cached is None:
            mask = pygame.mask.from_surface(self.track_image, 127)
            cached = mask.to_surface(
                surface=None, setcolor=rgba, unsetcolor=(0, 0, 0, 0)
            )
            self._silhouettes[key] = cached
        return cached

    def _render_art_track(self) -> None:
        """Render authored track art and its clipped fill into ``local_surface``."""
        assert self.track_image is not None
        self.local_surface.fill((0, 0, 0, 0))
        self.draw_background_image()
        self.local_surface.blit(self.track_image, (0, 0))
        left, top = self.box_model["left"], self.box_model["top"]
        content_width = self.box_model["content_width"]
        content_height = self.box_model["content_height"]
        fill_width = int(content_width * self.interpolation.current)
        if fill_width <= 0:
            return
        if self.fill_image is not None:
            fw, fh = self.fill_image.get_size()
            self.local_surface.blit(
                self.fill_image,
                (left, top),
                (
                    left,
                    top,
                    min(fill_width, max(0, fw - left)),
                    min(content_height, max(0, fh - top)),
                ),
            )
            return

        fill_color = self._resolved_style().fg
        layer = self._silhouette(fill_color)
        if layer is not None:
            self.local_surface.blit(layer, (left, top), (left, top, fill_width, content_height))
            tint = self._silhouette(self.empty_tint)
            end_x = left + fill_width
            content_end = left + content_width
            if tint is not None and end_x < content_end:
                self.local_surface.blit(tint, (end_x, top), (end_x, top, content_end - end_x, content_height))
            return

        if fill_color is not None and fill_width > 0:
            pygame.draw.rect(
                self.local_surface,
                fill_color,
                (left, top, fill_width, content_height),
            )

    def render(self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)) -> None:
        pos = (
            self.box_model["offset_x"] + pos_offset[0],
            self.box_model["offset_y"] + pos_offset[1],
        )
        resolved = self._resolved_style()
        self.draw_shadow(screen, pos)

        if self.track_image is not None:
            self._render_art_track()
        else:
            self.draw_base()
            fill_width = int(self.box_model["content_width"] * self.interpolation.current)
            if fill_width > 0 and resolved.fg is not None:
                pygame.draw.rect(
                    self.local_surface,
                    resolved.fg,
                    (
                        self.box_model["left"],
                        self.box_model["top"],
                        fill_width,
                        self.box_model["content_height"],
                    ),
                    border_radius=max(0, resolved.radius - self.border_width),
                )
        screen.blit(self.local_surface, pos)
