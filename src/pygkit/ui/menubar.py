from __future__ import annotations

from dataclasses import dataclass
from typing import Unpack

import pygame
from pygame import Surface

from .anchors import place
from .base import UIBase, UIOptions
from .container import dispatch_to_widgets
from .theming import UIStyle


MENUBAR_DEFAULT_STYLE: UIStyle = {
    "bg": (20, 22, 28, 255),
    "radius": 6,
}
from ..protocols import Widget


@dataclass
class _Entry:
    child: Widget
    anchor: str
    at: tuple[int, int] | None
    dx: int
    dy: int
    rect: pygame.Rect


class Menubar(UIBase):
    """Anchored widget group with optional shared clipped background art.

    ``image=`` is retained as an alias for ``background_image=``. Children
    may be interactive widgets *or* layout containers (VBox, HBox, ...):
    mouse events route through containers to their visible leaves, so a
    button inside a nested layout behaves like a direct child. Hit rects
    refresh automatically when a child resizes or the bar's box model
    changes; ``relayout()`` stays as a manual escape hatch.
    """
    def __init__(
        self,
        *,
        image: Surface | None = None,
        background_image: Surface | None = None,
        width: int = 0,
        height: int = 0,
        style: UIStyle | None = None,
        **overrides: Unpack[UIOptions],
    ) -> None:
        if image is not None and background_image is not None:
            raise ValueError("pass either image or background_image, not both")
        art = background_image if background_image is not None else image
        if style is None:
            style = MENUBAR_DEFAULT_STYLE
        options: UIOptions = {
            **{
                "width": width if width > 0 else (art.get_width() if art is not None else 0),
                "height": height if height > 0 else (art.get_height() if art is not None else 0),
                "border_width": 0,
            },
            **overrides,
        }
        super().__init__(options, style=style, background_image=art)
        self.entries: list[_Entry] = []
        self._layout_dirty = True
        self._settings_snapshot: object = None

    def _content_rect(self) -> pygame.Rect:
        return pygame.Rect(
            self.box_model["left"],
            self.box_model["top"],
            self.box_model["content_width"],
            self.box_model["content_height"],
        )

    def add(
        self,
        child: Widget,
        *,
        at: tuple[int, int] | None = None,
        anchor: str = "topleft",
        dx: int = 0,
        dy: int = 0,
    ) -> Widget:
        if not isinstance(child, Widget):
            raise TypeError(f"Menubar.add() needs render/update/size, got {type(child).__name__}")
        rect = (
            pygame.Rect(at[0], at[1], *child.size)
            if at is not None
            else place(child.size, self._content_rect(), anchor, dx, dy)
        )
        self.entries.append(_Entry(child, anchor, at, dx, dy, rect))
        self._layout_dirty = True
        return child

    def remove(self, child: Widget) -> bool:
        for i, entry in enumerate(self.entries):
            if entry.child is child:
                del self.entries[i]
                self._layout_dirty = True
                return True
        return False

    def relayout(self) -> None:
        within = self._content_rect()
        for entry in self.entries:
            if entry.at is not None:
                entry.rect = pygame.Rect(entry.at[0], entry.at[1], *entry.child.size)
            else:
                entry.rect = place(entry.child.size, within, entry.anchor, entry.dx, entry.dy)

    def _layout_snapshot(self) -> object:
        """Everything that can move a child: its size, its placement, and
        the bar's content rect (drifts e.g. after set_style)."""
        return (
            tuple(self._content_rect()),
            tuple(
                (entry.child.size, entry.anchor, entry.at, entry.dx, entry.dy)
                for entry in self.entries
            ),
        )

    def _ensure_layout(self) -> None:
        snapshot = self._layout_snapshot()
        if self._layout_dirty or snapshot != self._settings_snapshot:
            self.relayout()
            self._layout_dirty = False
            self._settings_snapshot = snapshot

    def handle_event(self, event: pygame.event.Event) -> bool:
        self._ensure_layout()
        return dispatch_to_widgets(
            (entry.child for entry in reversed(self.entries)), event
        )

    def clear_hover(self) -> None:
        """Clear hover recursively when this bar is occluded by a sibling."""
        for entry in self.entries:
            clear_hover = getattr(entry.child, "clear_hover", None)
            if clear_hover is not None:
                clear_hover()

    def update(self, dt: float = 0.0) -> None:
        self._ensure_layout()
        for entry in self.entries:
            entry.child.update(dt)

    def render(self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)) -> None:
        self._ensure_layout()
        self.draw_base()
        pos = (
            self.box_model["offset_x"] + pos_offset[0],
            self.box_model["offset_y"] + pos_offset[1],
        )
        self.draw_shadow(screen, pos)
        screen.blit(self.local_surface, pos)
        for entry in self.entries:
            entry.child.render(screen, (pos[0] + entry.rect.x, pos[1] + entry.rect.y))
