"""
Production-grade Dialog System for Pygame.

Features:
- Typewriter effect with customizable speeds
- Nine-patch style border rendering
- Semi-transparent background with configurable colors
- Speaker name highlighting
- Animated progress indicator
- Text outline/shadow for readability
- Word wrapping and multi-line support
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, List, Literal, Optional, Tuple, Union

import pygame
from pygame import Surface
from pygame.font import Font
from pygame.typing import ColorLike

from ..ui.base import UIBase, UIOptions
from ..utils.text import load_font, render_multiline, wrap
from ..utils.timer import Timer


class TypewriterSpeed(Enum):
    """Predefined typewriter speed constants."""

    EXTRA_FAST = 0.015
    FAST = 0.025
    MEDIUM = 0.04
    SLOW = 0.06
    EXTRA_SLOW = 0.1


@dataclass
class DialogColors:
    """
    Color configuration for the dialog system.

    All colors support RGBA tuples for transparency control.
    """

    box_background: ColorLike = (54, 68, 60, 200)
    box_border: ColorLike = (20, 25, 22, 255)

    speaker_name: ColorLike = (251, 224, 83, 255)
    dialog_text: ColorLike = (255, 255, 255, 255)

    text_outline: ColorLike = (20, 25, 22, 255)
    text_shadow_offset: Tuple[int, int] = (1, 1)

    indicator_color: ColorLike = (207, 228, 235, 255)

    def to_dict(self) -> dict[str, ColorLike]:
        """Convert to dictionary for easy iteration."""
        return {
            "box_background": self.box_background,
            "box_border": self.box_border,
            "speaker_name": self.speaker_name,
            "dialog_text": self.dialog_text,
            "text_outline": self.text_outline,
            "indicator_color": self.indicator_color,
        }


@dataclass
class DialogConfig:
    """
    Complete configuration for a DialogBox instance.

    Combines layout, typography, colors, and behavior settings.
    """

    width: int = 600
    height: int = 150
    padding_x: int = 20
    padding_y: int = 15
    border_radius: int = 8
    border_width: int = 2

    font_name: Optional[Union[str, Path]] = None
    font_size: int = 24
    name_font_size: int = 26
    line_spacing: int = 4
    text_align: Literal["left", "center", "right"] = "left"

    typewriter_speed: TypewriterSpeed = TypewriterSpeed.MEDIUM
    auto_advance_delay: float = 0.0

    colors: DialogColors = field(default_factory=DialogColors)

    show_indicator: bool = True
    indicator_blink_interval: int = 500
    indicator_size: int = 12


@dataclass
class DialogLine:
    """
    Represents a single line of dialog data.

    Attributes:
        speaker: Name of the character speaking (optional)
        text: The dialog text content
        callback: Optional callback when this line is displayed
    """

    speaker: Optional[str] = None
    text: str = ""
    callback: Optional[Callable[[], None]] = None


class DialogBox(UIBase):
    """
    A production-grade dialog box with typewriter effect and animations.

    Features:
    - Smooth typewriter text reveal with adjustable speeds
    - Semi-transparent background with nine-patch style borders
    - Speaker name highlighting with distinct color
    - Animated progress indicator (blinking arrow)
    - Full color customization via DialogColors
    - Text outline/shadow for readability over any background
    - Word wrapping and multi-line support

    Usage:
        config = DialogConfig(
            width=600,
            height=150,
            typewriter_speed=TypewriterSpeed.FAST,
        )
        config.colors.speaker_name = (255, 200, 50, 255)

        dialog = DialogBox(config)
        dialog.set_dialog("Kryn", "What a strange thing this is.")

        while running:
            dialog.update(dt)
            dialog.render(screen, (x, y))
    """

    def __init__(self, config: Optional[DialogConfig] = None) -> None:
        """
        Initialize the DialogBox.

        Args:
            config: Configuration object. Uses defaults if not provided.
        """
        self.config = config or DialogConfig()

        options: UIOptions = {
            "width": self.config.width,
            "height": self.config.height,
            "padding_x": self.config.padding_x,
            "padding_y": self.config.padding_y,
            "border_radius": self.config.border_radius,
            "border_width": self.config.border_width,
            "background": self.config.colors.box_background,
            "border_color": self.config.colors.box_border,
        }

        super().__init__(options)

        self.font = load_font(
            self.config.font_name or "",
            self.config.font_size,
            default_size=self.config.font_size,
        )
        self.name_font = load_font(
            self.config.font_name or "",
            self.config.name_font_size,
            default_size=self.config.name_font_size,
        )

        self._current_line: Optional[DialogLine] = None
        self._displayed_text: str = ""
        self._char_index: int = 0
        self._typewriter_timer: Timer = Timer(0, stale_init=True)
        self._is_complete: bool = False
        self._auto_advance_timer: Timer = Timer(0, stale_init=True)
        self._indicator_blink_timer: Timer = Timer(self.config.indicator_blink_interval, stale_init=True)
        self._indicator_visible: bool = True

        self._content_rect = pygame.Rect(
            self.box_model["left"],
            self.box_model["top"],
            self.box_model["content_width"],
            self.box_model["content_height"],
        )

        self._name_surface: Optional[Surface] = None
        self._text_surfaces: List[Surface] = []
        self._needs_rebuild: bool = False

    def set_dialog(self, speaker: Optional[str], text: str, callback: Optional[Callable[[], None]] = None) -> None:
        """
        Set new dialog content and start typewriter effect.

        Args:
            speaker: Name of the character (displayed in highlight color)
            text: The dialog text content
            callback: Optional callback when line display completes
        """
        self._current_line = DialogLine(speaker=speaker, text=text, callback=callback)
        self._displayed_text = ""
        self._char_index = 0
        self._is_complete = False

        char_interval = self.config.typewriter_speed.value * 1000
        self._typewriter_timer = Timer(char_interval, stale_init=False)

        if self.config.auto_advance_delay > 0:
            self._auto_advance_timer = Timer(int(self.config.auto_advance_delay * 1000), stale_init=True)

        if speaker:
            self._name_surface = self._render_text_with_outline(
                f"{speaker}:",
                self.name_font,
                self.config.colors.speaker_name,
            )
        else:
            self._name_surface = None

        self._text_surfaces = []
        self._needs_rebuild = True

        self._indicator_visible = False

    def skip_to_end(self) -> bool:
        """
        Immediately complete the typewriter effect.

        Returns:
            True if text was completed (wasn't already done), False otherwise
        """
        if not self._is_complete and self._current_line:
            self._displayed_text = self._current_line.text
            self._char_index = len(self._displayed_text)
            self._is_complete = True
            self._indicator_visible = self.config.show_indicator
            self._rebuild_text_surfaces()

            if self._current_line.callback:
                self._current_line.callback()

            return True
        return False

    def advance(self) -> bool:
        """
        Advance to next state (complete text or signal ready for next line).

        Returns:
            True if dialog is ready to advance to next line, False otherwise
        """
        if not self._is_complete:
            return self.skip_to_end()
        return True

    def update(self, dt: Optional[float] = None) -> None:
        """
        Update dialog state (typewriter effect, animations).

        Args:
            dt: Delta time in seconds. If None, uses clock tick.
        """
        if not self._current_line:
            return

        if not self._is_complete:
            self._typewriter_timer.reset()

            chars_to_add = 0
            elapsed = self._typewriter_timer.elapsed()
            interval = self._typewriter_timer.interval

            if interval > 0:
                chars_to_add = max(1, int(elapsed / interval))

            text_len = len(self._current_line.text)
            if self._char_index < text_len:
                old_index = self._char_index
                self._char_index = min(text_len, self._char_index + chars_to_add)
                self._displayed_text = self._current_line.text[: self._char_index]

                if self._char_index != old_index:
                    self._needs_rebuild = True

                if self._char_index < text_len:
                    self._typewriter_timer.reset()

            if self._char_index >= text_len:
                self._is_complete = True
                self._indicator_visible = self.config.show_indicator
                self._rebuild_text_surfaces()

                if self._current_line.callback:
                    self._current_line.callback()

                if self.config.auto_advance_delay > 0:
                    self._auto_advance_timer.reset()

        elif self.config.auto_advance_delay > 0:
            if self._auto_advance_timer.reached():
                pass

        if self._is_complete and self.config.show_indicator:
            self._indicator_blink_timer.reset()
            if self._indicator_blink_timer.reached():
                self._indicator_visible = not self._indicator_visible
                self._indicator_blink_timer.reset()

    def _render_text_with_outline(
        self,
        text: str,
        font: Font,
        color: ColorLike,
    ) -> Surface:
        """Render text with outline/shadow effect for readability."""
        outline_color = self.config.colors.text_outline
        offset = self.config.colors.text_shadow_offset

        base_surf = font.render(text, True, color)

        w = base_surf.get_width() + abs(offset[0]) * 2
        h = base_surf.get_height() + abs(offset[1]) * 2
        result = Surface((w, h), pygame.SRCALPHA)
        result.fill((0, 0, 0, 0))

        for dx in range(-abs(offset[0]), abs(offset[0]) + 1):
            for dy in range(-abs(offset[1]), abs(offset[1]) + 1):
                if dx == 0 and dy == 0:
                    continue
                outline_surf = font.render(text, True, outline_color)
                result.blit(outline_surf, (abs(offset[0]) + dx, abs(offset[1]) + dy))

        result.blit(base_surf, (abs(offset[0]), abs(offset[1])))

        return result

    def _rebuild_text_surfaces(self) -> None:
        """Rebuild rendered text surfaces for current displayed text."""
        if not self._displayed_text:
            self._text_surfaces = []
            return

        available_width = self._content_rect.width
        if self._name_surface:
            available_width -= self._name_surface.get_width() + 10

        lines = wrap(self.font, self._displayed_text, available_width)

        self._text_surfaces = [
            self._render_text_with_outline(
                line,
                self.font,
                self.config.colors.dialog_text,
            )
            for line in lines
        ]
        self._needs_rebuild = False

    def _get_rendered_text_height(self) -> int:
        """Calculate total height of rendered text lines."""
        if not self._text_surfaces:
            return 0
        line_h = self.font.get_linesize()
        return len(self._text_surfaces) * line_h + (len(self._text_surfaces) - 1) * self.config.line_spacing

    def _draw_indicator(self, surf: Surface, pos: Tuple[int, int]) -> None:
        """Draw the animated progress indicator (downward arrow)."""
        if not self._indicator_visible:
            return

        size = self.config.indicator_size
        color = self.config.colors.indicator_color

        half = size // 2
        points = [
            (pos[0], pos[1]),
            (pos[0] + size, pos[1]),
            (pos[0] + half, pos[1] + half),
        ]

        pygame.draw.polygon(surf, color, points)

    def render(self, screen: Surface, pos_offset: Tuple[int, int] = (0, 0)) -> None:
        """
        Render the dialog box to the screen.

        Args:
            screen: Target surface to render to
            pos_offset: Position offset (x, y) on the screen
        """

        if self._needs_rebuild and self._is_complete:
            self._rebuild_text_surfaces()

        self.draw_base()

        local_surf = self.local_surface

        text_start_x = self._content_rect.x
        text_start_y = self._content_rect.y

        text_height = self._get_rendered_text_height()
        name_height = self._name_surface.get_height() if self._name_surface else 0
        total_content_height = max(text_height, name_height)

        if total_content_height < self._content_rect.height:
            text_start_y += (self._content_rect.height - total_content_height) // 2

        name_x = text_start_x
        name_y = text_start_y
        if self._name_surface:
            local_surf.blit(self._name_surface, (name_x, name_y))

        text_x = text_start_x
        text_y = text_start_y
        if self._name_surface:
            text_x = name_x + self._name_surface.get_width() + 10

        line_h = self.font.get_linesize()
        for i, text_surf in enumerate(self._text_surfaces):
            y = text_y + i * (line_h + self.config.line_spacing)

            local_surf.blit(text_surf, (text_x, y))

        if self._is_complete and self.config.show_indicator:
            indicator_x = self._content_rect.centerx - self.config.indicator_size // 2
            indicator_y = self._content_rect.bottom - self.config.indicator_size - 5
            self._draw_indicator(local_surf, (indicator_x, indicator_y))

        pos = (
            self.box_model["offset_x"] + pos_offset[0],
            self.box_model["offset_y"] + pos_offset[1],
        )
        screen.blit(local_surf, pos)

    @property
    def is_complete(self) -> bool:
        """Check if typewriter effect has completed."""
        return self._is_complete

    @property
    def current_text(self) -> str:
        """Get currently displayed text (partial during typewriter)."""
        return self._displayed_text

    @property
    def full_text(self) -> str:
        """Get the full dialog text (if a line is set)."""
        return self._current_line.text if self._current_line else ""

    def set_typewriter_speed(self, speed: TypewriterSpeed) -> None:
        """
        Change typewriter speed dynamically.

        Useful for dramatic pauses or fast-forward effects.
        """
        self.config.typewriter_speed = speed

        if not self._is_complete:
            char_interval = speed.value * 1000
            self._typewriter_timer.interval = int(char_interval)

    def clear(self) -> None:
        """Clear current dialog and reset state."""
        self._current_line = None
        self._displayed_text = ""
        self._char_index = 0
        self._is_complete = False
        self._name_surface = None
        self._text_surfaces = []
        self._indicator_visible = False


__all__ = [
    "DialogBox",
    "DialogConfig",
    "DialogColors",
    "DialogLine",
    "TypewriterSpeed",
]
