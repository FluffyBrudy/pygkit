from __future__ import annotations

from dataclasses import dataclass
from typing import Unpack

import pygame
from pygame import SRCALPHA, Surface
from pygame.font import Font
from pygame.typing import ColorLike

from ..signals import Signal
from .base import UIBase, UIOptions


@dataclass
class ButtonStyle:
    text_color: ColorLike = (255, 255, 255, 255)
    hover_tint: ColorLike | None = (255, 255, 255, 36)
    pressed_tint: ColorLike | None = (0, 0, 0, 70)
    disabled_tint: ColorLike | None = (0, 0, 0, 110)


class Button(UIBase):
    def __init__(
        self,
        font: Font,
        text: str,
        *,
        image: Surface | None = None,
        width: int = 0,
        height: int = 0,
        style: ButtonStyle | None = None,
        enabled: bool = True,
        **overrides: Unpack[UIOptions],
    ) -> None:
        self.font = font
        self.text = text
        self.image = image
        self.style = style or ButtonStyle()
        self.enabled = enabled
        self.on_press: Signal[Button] = Signal("button_press")
        tw, th = font.size(text) if text else (0, 0)
        if image is not None:
            natural_w, natural_h = image.get_width(), image.get_height()
        else:
            natural_w, natural_h = 16 + tw, th + 10
        pad_x = overrides.get("padding_x", 0)
        pad_y = overrides.get("padding_y", 0)
        border = overrides.get("border_width", 0)
        if width <= 0:
            width = natural_w + 2 * (pad_x + border)
        if height <= 0:
            height = natural_h + 2 * (pad_y + border)
        options: UIOptions = {
            **{
                "width": width,
                "height": height,
                "border_radius": 6,
                "border_width": 0,
                "background": (20, 22, 28, 255),
            },
            **overrides,
        }
        super().__init__(options)
        self._armed = False
        self._hovered = False
        self._label: Surface | None = None
        self._tint: dict[str, Surface | None] = {"hover": None, "pressed": None, "disabled": None}
        self._origin = (0, 0)

    def set_text(self, text: str) -> None:
        self.text = text
        self.invalidate()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self._armed = False

    def invalidate(self) -> None:
        self._label = None
        self._tint = {"hover": None, "pressed": None, "disabled": None}

    def _ensure(self) -> None:
        if self._label is None and self.text:
            self._label = self.font.render(self.text, True, self.style.text_color)
        w = self.box_model["content_width"]
        h = self.box_model["content_height"]
        for key, color in (
            ("hover", self.style.hover_tint),
            ("pressed", self.style.pressed_tint),
            ("disabled", self.style.disabled_tint),
        ):
            if self._tint[key] is None and color is not None:
                surf = Surface((max(1, w), max(1, h)), SRCALPHA)
                surf.fill(color)
                self._tint[key] = surf

    def render(self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)) -> None:
        self.draw_base()
        self._ensure()
        pos = (
            self.box_model["offset_x"] + pos_offset[0],
            self.box_model["offset_y"] + pos_offset[1],
        )
        self._origin = pos
        base = (self.box_model["left"], self.box_model["top"])
        _, h = self.size
        if self.image is not None:
            self.local_surface.blit(self.image, base)
        x = base[0] + 8
        if self.image is not None and self._label is not None:
            x = base[0] + (self.size[0] - self._label.get_width()) // 2
        if self._label is not None:
            self.local_surface.blit(self._label, (x, base[1] + (h - self._label.get_height()) // 2))
        if not self.enabled:
            if self._tint["disabled"] is not None:
                self.local_surface.blit(self._tint["disabled"], base)
        elif self._armed:
            if self._tint["pressed"] is not None:
                self.local_surface.blit(self._tint["pressed"], base)
        elif self._hovered:
            if self._tint["hover"] is not None:
                self.local_surface.blit(self._tint["hover"], base)
        screen.blit(self.local_surface, pos)

    def contains(self, pos: tuple[int, int]) -> bool:
        w, h = self.size
        return pygame.Rect(self._origin[0], self._origin[1], w, h).collidepoint(pos)

    def press(self, pos: tuple[int, int]) -> bool:
        self._hovered = self.contains(pos)
        self._armed = self._hovered and self.enabled
        return self._armed

    def activate(self, pos: tuple[int, int]) -> bool:
        hit = self._armed and self.contains(pos) and self.enabled
        self._armed = False
        if hit:
            self.on_press.emit(self)
        return hit
