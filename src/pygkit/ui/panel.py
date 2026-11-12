"""Passive image-or-polygon panel widget for pygkit UI.

A ``Panel`` is a non-interactive display element: it draws a shaped
background (polygon fill + outline, or the shared chrome engine's
rounded-rect fallback) and exposes ``content_rect`` and ``header_rect``
so callers can place children at the correct offsets without manual
padding arithmetic.

Typical use::

    style = {"bg": "#262432", "border": "#433f56", "radius": 10}
    panel = Panel(width=320, height=220, style=style)
    panel.render(screen, (px, py))   # or add it to a container/layout

Polygon shape (widget-specific geometry, not chrome)::

    panel = Panel(
        width=210, height=56,
        polygon=poly,                       # local vertices
        style={"bg": "#06b6d4", "border": "#06b6d4"},
        content_rect=pygame.Rect(8, 8, 193, 39),
        header_rect=pygame.Rect(0, 0, 210, 48),
    )
"""

from __future__ import annotations

from typing import Optional, Tuple, Unpack

import pygame
from pygame import Rect, Surface

from .base import UIBase, UIOptions
from .theming import UIStyle


class Panel(UIBase):
    """Passive display panel sharing the chrome engine.

    Without ``polygon`` the fallback renders via the shared chrome
    engine (flat/gradient/border from the style). With a polygon
    (>= 3 local vertices) the shape is filled from the style's ``bg``
    and stroked from its ``border`` at ``outline_width`` — the only
    widget-local chrome drawing left, because pygame rects cannot
    express arbitrary shapes.
    """

    DEFAULT_STYLE: UIStyle = {
        "bg": (30, 30, 36, 255),
        "border": (80, 80, 90, 255),
        "radius": 6,
    }

    def __init__(
        self,
        *,
        style: UIStyle | None = None,
        background_image: Surface | None = None,
        polygon: "Optional[list[tuple[int, int]]]" = None,
        outline_width: int = 2,
        content_rect: Optional[Rect] = None,
        header_rect: Optional[Rect] = None,
        **overrides: Unpack[UIOptions],
    ) -> None:
        overrides.setdefault("width", 0)
        overrides.setdefault("height", 0)
        self.polygon = list(polygon) if polygon else []
        self.outline_width = max(0, outline_width)
        self.content_rect: Optional[Rect] = content_rect
        self.header_rect: Optional[Rect] = header_rect
        super().__init__(overrides, style=style, background_image=background_image)

    def render(self, screen: Surface, pos_offset: Tuple[int, int] = (0, 0)) -> None:
        if self.polygon and len(self.polygon) >= 3:
            self.draw_polygon(
                self.polygon,
                outline_width=self.outline_width,
                content_rect=self.content_rect,
            )
            pos = (
                self.box_model["offset_x"] + pos_offset[0],
                self.box_model["offset_y"] + pos_offset[1],
            )
            self.draw_shadow(screen, pos)
            for plugin in self.renderable_plugins:
                plugin(self.local_surface)
            screen.blit(self.local_surface, pos)
            return
        super().render(screen, pos_offset)

    def update(self, dt: float = 0.0) -> None:
        pass
