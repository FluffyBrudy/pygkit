from __future__ import annotations

from typing import Unpack

import pygame
from pygame import SRCALPHA, Surface
from pygame.font import Font
from pygame.mask import Mask

from ..signals import Signal
from .base import UIBase, UIOptions, generate_box_model
from .theming import SKIN_STATE_KEYS as STATE_KEYS, Skin, UIStyle
from .theming import StateKey, UIStyle


class Button(UIBase):
    """Styled interactive button.

    Chrome (background/gradient/border/shadow/label color) comes from one
    shared :class:`pygkit.ui.UIStyle`; per-state behavior lives in the
    style's ``hover``/``pressed``/``disabled`` partials (gradient swaps
    replace tint overlays; ``offset_y`` reproduces pack-art label motion).
    ``selected`` is a separate application-controlled persistent state for
    tabs, toggles, and menu items; clicks never change it automatically.
    Foundation chrome painting lives in the shared engine — this widget
    only adds state resolution, the label, and the optional icon.

    Widget-extension data (not chrome): ``background_image`` (clipped art
    beneath content), ``image`` (foreground icon left of the label),
    ``images`` (per-state skin frames), and ``hit_masks``.
    """

    DEFAULT_STYLE: UIStyle = {
        "fg": (255, 255, 255, 255),
        "gradient": ((44, 48, 60, 255), (26, 28, 36, 255)),
        "radius": 9,
        "hover": {"gradient": ((56, 60, 74, 255), (31, 33, 42, 255))},
        "pressed": {"gradient": ((30, 32, 42, 255), (17, 18, 23, 255))},
        "disabled": {"gradient": ((24, 26, 34, 255), (15, 16, 21, 255))},
    }

    def __init__(
        self,
        font: Font,
        text: str,
        *,
        image: Surface | None = None,
        background_image: Surface | None = None,
        images: Skin | None = None,
        hit_masks: "dict[str, Mask] | None" = None,
        style: UIStyle | None = None,
        icon_gap: int = 8,
        enabled: bool = True,
        selected: bool = False,
        **overrides: Unpack[UIOptions],
    ) -> None:
        self.font = font
        self.text = text
        self.image = image
        self.images = images
        self.hit_masks = hit_masks
        self.icon_gap = max(0, icon_gap)
        self.enabled = enabled
        if not isinstance(selected, bool):
            raise TypeError(f"selected must be bool, got {type(selected).__name__}")
        self._selected = selected
        self.on_press: Signal[Button] = Signal("button_press")

        self._pad_x = overrides.get("padding_x", 0)
        self._pad_y = overrides.get("padding_y", 0)
        self._border_w = overrides.get("border_width", 0)
        self._auto_w = overrides.get("width", 0) <= 0
        self._auto_h = overrides.get("height", 0) <= 0
        tw, th = font.size(text) if text else (0, 0)
        if image is not None:
            natural_w = image.get_width() + (self.icon_gap if text else 0) + tw
            natural_h = max(image.get_height(), th)
        else:
            natural_w, natural_h = 16 + tw, th + 10
        options: UIOptions = {
            "width": overrides.get("width", 0),
            "height": overrides.get("height", 0),
            **{
                k: v for k, v in overrides.items() if k not in ("width", "height")
            },
        }
        if self._auto_w:
            options["width"] = natural_w + 2 * (self._pad_x + self._border_w)
        if self._auto_h:
            options["height"] = natural_h + 2 * (self._pad_y + self._border_w)
        self._options = dict(options)
        super().__init__(options, style=style, background_image=background_image)

        self._armed = False
        self._hovered = False
        self._labels: dict[StateKey, Surface] = {}
        self._skin: dict[str, Surface] | None = None
        self._origin = (0, 0)
        self._origin_valid = False


    def set_text(self, text: str) -> None:
        """Set the label text and re-flow auto-sized axes.

        Width/height recompute exactly as in ``__init__`` for axes that
        were not explicitly sized; explicitly passed sizes are kept.
        Cached surfaces and (via dirty checks) container positions follow
        automatically.
        """
        self.text = text
        self.invalidate()
        self._reflow()

    def _reflow(self) -> None:
        """Recompute natural size and rebuild the box model for auto axes."""
        if not (self._auto_w or self._auto_h):
            return
        tw, th = self.font.size(self.text) if self.text else (0, 0)
        if self.image is not None:
            natural_w = self.image.get_width() + (self.icon_gap if self.text else 0) + tw
            natural_h = max(self.image.get_height(), th)
        else:
            natural_w, natural_h = 16 + tw, th + 10
        if self._auto_w:
            self._options["width"] = natural_w + 2 * (self._pad_x + self._border_w)
        if self._auto_h:
            self._options["height"] = natural_h + 2 * (self._pad_y + self._border_w)
        self.box_model = generate_box_model(self._options)
        self.local_surface = Surface(
            (self.box_model["full_width"], self.box_model["full_height"]), SRCALPHA
        )
        self.invalidate()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self._armed = False

    @property
    def selected(self) -> bool:
        """Whether this Button has application-controlled persistent selection."""
        return self._selected

    def set_selected(self, selected: bool) -> None:
        """Select or deselect this Button without changing click behavior.

        A selected Button remains selected after clicks. The owner is
        responsible for implementing a toggle, tab group, or menu model and
        calling this method when its application state changes.
        """
        if not isinstance(selected, bool):
            raise TypeError(f"selected must be bool, got {type(selected).__name__}")
        self._selected = selected

    def invalidate(self) -> None:
        self._labels.clear()
        self._skin = None
        super().invalidate()


    def _skin_state(self) -> StateKey:
        """Current state-skin key from button state."""
        return self._state_key(
            enabled=self.enabled,
            armed=self._armed,
            hovered=self._hovered,
            selected=self._selected,
        )

    def _ensure_skin(self) -> None:
        """Validate/complete the state skin once; whole-box art, no chrome."""
        skin = self.images
        if skin is None or self._skin is not None:
            return
        missing = [k for k in STATE_KEYS if skin.get(k) is None]
        if missing:
            raise ValueError(f"button skin misses states: {missing!r}")
        frames: dict[StateKey, Surface] = {}
        for k in STATE_KEYS:
            try:
                frames[k] = skin[k].convert_alpha()
            except pygame.error:
                frames[k] = skin[k].copy()
        self._skin = frames


    def render(self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)) -> None:
        pos = (
            self.box_model["offset_x"] + pos_offset[0],
            self.box_model["offset_y"] + pos_offset[1],
        )
        self._origin = pos
        self._origin_valid = True
        self._ensure_skin()
        state = self._skin_state()
        resolved = self._resolved_style(state)

        self.draw_shadow(screen, pos, state)

        self.local_surface.fill((0, 0, 0, 0))
        if self._skin is None:
            self.draw_base(state)
        else:
            self.draw_background_image(state)
        if self._skin is not None:
            skin_state = state if state in STATE_KEYS else "normal"
            self.local_surface.blit(self._skin[skin_state], (0, 0))
        base = (self.box_model["left"], self.box_model["top"])
        if self.image is not None:
            self.local_surface.blit(self.image, base)
        label = self._label_for(state)
        if label is not None:
            y_off = resolved.offset_y
            if self.image is not None:
                self.local_surface.blit(
                    label,
                    (
                        base[0] + self.image.get_width() + self.icon_gap,
                        base[1]
                        + (self.box_model["content_height"] - label.get_height()) // 2
                        + y_off,
                    ),
                )
            else:
                self.local_surface.blit(
                    label,
                    (
                        max(0, (self.size[0] - label.get_width()) // 2),
                        max(0, (self.size[1] - label.get_height()) // 2 + y_off),
                    ),
                )
        screen.blit(self.local_surface, pos)

    def _label_for(self, state: StateKey) -> Surface | None:
        if not self.text:
            return None
        label = self._labels.get(state)
        if label is None:
            fg = self._resolved_style(state).fg or (255, 255, 255, 255)
            label = self.font.render(self.text, True, fg)
            self._labels[state] = label
        return label


    def handle_event(self, event: pygame.event.Event) -> bool:
        """Lightweight per-widget event handling: hover on MOUSEMOTION."""
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.contains(event.pos)
            return self._hovered
        return False

    def clear_hover(self) -> None:
        """Clear transient pointer-over paint when an ancestor occludes us."""
        self._hovered = False

    def contains(self, pos: tuple[int, int]) -> bool:
        if not self._origin_valid:
            return False
        masks = self.hit_masks
        if masks is not None and self._origin_valid:
            state = self._skin_state()
            mask = masks.get(state)
            if mask is None:
                mask = masks.get("normal")
            if mask is not None:
                lx = pos[0] - self._origin[0]
                ly = pos[1] - self._origin[1]
                mw, mh = mask.get_size()
                if 0 <= lx < mw and 0 <= ly < mh:
                    return bool(mask.get_at((lx, ly)))
                return False
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
