from __future__ import annotations

from dataclasses import dataclass
from typing import Unpack

import pygame
from pygame import Surface

from .anchors import place
from .base import UIBase, UIOptions
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
    def __init__(
        self,
        *,
        image: Surface | None = None,
        width: int = 0,
        height: int = 0,
        **overrides: Unpack[UIOptions],
    ) -> None:
        self.image = image
        options: UIOptions = {
            **{
                "width": width if width > 0 else (image.get_width() if image is not None else 0),
                "height": height if height > 0 else (image.get_height() if image is not None else 0),
                "border_radius": 6,
                "border_width": 0,
                "background": (20, 22, 28, 255),
            },
            **overrides,
        }
        super().__init__(options)
        self.entries: list[_Entry] = []

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
        return child

    def remove(self, child: Widget) -> bool:
        for i, entry in enumerate(self.entries):
            if entry.child is child:
                del self.entries[i]
                return True
        return False

    def relayout(self) -> None:
        within = self._content_rect()
        for entry in self.entries:
            if entry.at is not None:
                entry.rect = pygame.Rect(entry.at[0], entry.at[1], *entry.child.size)
            else:
                entry.rect = place(entry.child.size, within, entry.anchor, entry.dx, entry.dy)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for entry in reversed(self.entries):
                press = getattr(entry.child, "press", None)
                if press is not None and press(event.pos):
                    return True
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for entry in reversed(self.entries):
                activate = getattr(entry.child, "activate", None)
                if activate is not None and activate(event.pos):
                    return True
            return False
        return False

    def update(self, dt: float = 0.0) -> None:
        for entry in self.entries:
            entry.child.update(dt)

    def render(self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)) -> None:
        self.draw_base()
        if self.image is not None:
            self.local_surface.blit(self.image, (0, 0))
        pos = (
            self.box_model["offset_x"] + pos_offset[0],
            self.box_model["offset_y"] + pos_offset[1],
        )
        screen.blit(self.local_surface, pos)
        for entry in self.entries:
            entry.child.render(screen, (pos[0] + entry.rect.x, pos[1] + entry.rect.y))
