from dataclasses import dataclass
from typing import Any, Callable, ClassVar, List, TypedDict

import pygame
from pygame import SRCALPHA, Surface

from .theming import (
    ColorLike,
    ResolvedStyle,
    STATE_KEYS,
    StateKey,
    UIStyle,
    resolve_style,
    select_state_key,
    validate_style,
)


class BoxModel(TypedDict, total=False):
    """Geometry contract: the only size/affecting knobs, shared by all widgets."""

    margin_x: int
    margin_y: int
    padding_x: int
    padding_y: int
    width: int
    height: int
    border_width: int


class BoxModelResult(TypedDict, total=True):
    left: int
    top: int
    offset_x: int
    offset_y: int
    full_width: int
    full_height: int
    content_width: int
    content_height: int


class UIOptions(BoxModel, total=False):
    """Geometry options accepted by every widget constructor.

    Pure geometry: style stays in :class:`pygkit.ui.UIStyle` (appearance
    only, never sizes) and positioning in the layout that applies it.
    ``border_width`` lives here — not in style — because it insets the
    content box (a layout fact), not only a paint fact.
    """


_GEOMETRY_KEYS = frozenset(BoxModel.__annotations__)


def generate_box_model(model: BoxModel) -> BoxModelResult:
    width = model.get("width", 0)
    height = model.get("height", 0)
    padding_x = model.get("padding_x", 0)
    padding_y = model.get("padding_y", 0)
    margin_x = model.get("margin_x", 0)
    margin_y = model.get("margin_y", 0)
    border_width = model.get("border_width", 0)

    inner_x = 2 * (padding_x + border_width)
    inner_y = 2 * (padding_y + border_width)

    return {
        "left": padding_x + border_width,
        "top": padding_y + border_width,
        "offset_x": margin_x,
        "offset_y": margin_y,
        "full_width": max(0, width),
        "full_height": max(0, height),
        "content_width": max(0, width - inner_x),
        "content_height": max(0, height - inner_y),
    }


class UIBase:
    """Box + chrome engine shared by every widget.

    Chrome (background/gradient/border/shadow) is painted by exactly one
    engine: :meth:`draw_base` resolves the widget's :class:`UIStyle` for
    the active state and paints from cached surfaces (built lazily,
    keyed by resolved values and geometry, invalidated by
    :meth:`set_style` / :meth:`invalidate` / reflow). Widgets own their
    content and special geometry; they never reimplement chrome painting.
    """

    DEFAULT_STYLE: ClassVar[UIStyle] = {}

    def __init__(
        self,
        options: UIOptions,
        style: UIStyle | None = None,
        *,
        background_image: Surface | None = None,
    ) -> None:
        unknown = set(options).difference(_GEOMETRY_KEYS)
        if unknown:
            names = ", ".join(repr(key) for key in sorted(unknown))
            raise TypeError(f"UIOptions only accepts geometry keys; got {names}")
        self._style = dict(style or {})
        validate_style(self._style)
        self._resolved_cache: "dict[StateKey, ResolvedStyle]" = {}
        self._gradient_cache: "dict[tuple, Surface]" = {}
        self._shadow_cache: "dict[tuple, Surface | None]" = {}
        self._background_image_cache: "dict[tuple, Surface]" = {}
        self._background_image = self._validate_background_image(background_image)

        self.box_model = generate_box_model(options)
        self._border_width = options.get("border_width", 0)

        local_size = self.box_model["full_width"], self.box_model["full_height"]
        self.local_surface = Surface(local_size, SRCALPHA)

        self.renderable_plugins: List[Callable[[Surface], Any]] = []


    @property
    def style(self) -> UIStyle:
        """The user style dict handed to this widget (unmutated)."""
        return self._style

    def set_style(self, style: UIStyle) -> None:
        """Replace the style and invalidate all cached chrome."""
        validate_style(style)
        self._style = dict(style)
        self.invalidate()

    @staticmethod
    def _validate_background_image(image: Surface | None) -> Surface | None:
        if image is not None and not isinstance(image, Surface):
            raise TypeError(
                "background_image must be a pygame.Surface or None, "
                f"got {type(image).__name__}"
            )
        return image

    @property
    def background_image(self) -> Surface | None:
        """Optional content-layer art, clipped by the shared chrome engine."""
        return self._background_image

    def set_background_image(self, image: Surface | None) -> None:
        """Replace background art without invalidating unrelated chrome caches."""
        self._background_image = self._validate_background_image(image)
        self._background_image_cache.clear()

    @property
    def border_width(self) -> int:
        return self._border_width

    def _resolved_style(self, state: StateKey = "normal") -> ResolvedStyle:
        cached = self._resolved_cache.get(state)
        if cached is None:
            cached = resolve_style(self._style, state, self.DEFAULT_STYLE)
            self._resolved_cache[state] = cached
        return cached

    def _state_key(
        self,
        *,
        enabled: bool = True,
        armed: bool = False,
        hovered: bool = False,
        selected: bool = False,
        state: StateKey = "normal",
    ) -> StateKey:
        return select_state_key(
            state,
            enabled=enabled,
            armed=armed,
            hovered=hovered,
            selected=selected,
        )


    def _gradient_surface(
        self,
        state: StateKey,
        width: int,
        height: int,
        radius: int,
    ) -> Surface | None:
        """Vertical gradient for a state, built once per (colors, geometry)."""
        resolved = self._resolved_style(state)
        if resolved.gradient is None:
            return None
        key = (*resolved.gradient, width, height, radius)
        cached = self._gradient_cache.get(key)
        if cached is None:
            cached = self._build_gradient(
                resolved.gradient[0], resolved.gradient[1], width, height, radius
            )
            self._gradient_cache[key] = cached
        return cached

    @staticmethod
    def _build_gradient(
        top: tuple[int, int, int, int],
        bottom: tuple[int, int, int, int],
        width: int,
        height: int,
        radius: int,
    ) -> Surface:
        """Vertical gradient with rounded corners (cached, build-time only)."""
        w, h = max(1, width), max(1, height)
        surface = Surface((w, h), SRCALPHA)
        surface.fill((0, 0, 0, 0))
        radius = max(0, min(radius, w // 2, h // 2))
        for y in range(h):
            t = y / (h - 1) if h > 1 else 0.0
            color = (
                round(top[0] + (bottom[0] - top[0]) * t),
                round(top[1] + (bottom[1] - top[1]) * t),
                round(top[2] + (bottom[2] - top[2]) * t),
                round(top[3] + (bottom[3] - top[3]) * t),
            )
            if radius <= 0 or (y >= radius and y < h - radius):
                pygame.draw.line(surface, color, (0, y), (w - 1, y))
            else:
                dy = radius - y - 1 if y < radius else y - (h - radius)
                dx = int((radius * radius - dy * dy) ** 0.5)
                x0 = radius - dx
                x1 = w - radius + dx - 1
                if x1 >= x0:
                    pygame.draw.line(surface, color, (x0, y), (x1, y))
        if w > 2 * radius + 2 and h > 3:
            pygame.draw.line(surface, (255, 255, 255, 22), (radius, 1), (w - radius - 1, 1))
        return surface

    def shadow_surface(self, state: StateKey = "normal") -> Surface | None:
        """Shadow sprite for a state, built once per (offsets, colors, geometry).

        Opt-in via the style's ``shadow`` key. Blit it to the real target
        surface at the widget position + ``(dx, dy)`` before the widget's
        own local surface — the widget bounds clip nothing here.
        """
        resolved = self._resolved_style(state)
        if resolved.shadow is None:
            return None
        w, h = self.box_model["full_width"], self.box_model["full_height"]
        key = (resolved.shadow, w, h, resolved.radius)
        cached = self._shadow_cache.get(key)
        if cached is None:
            surface = Surface((max(1, w), max(1, h)), SRCALPHA)
            surface.fill((0, 0, 0, 0))
            pygame.draw.rect(
                surface,
                resolved.shadow[2],
                (0, 0, max(1, w), max(1, h)),
                border_radius=max(0, resolved.radius),
            )
            cached = surface
            self._shadow_cache[key] = cached
        return cached

    def draw_shadow(
        self, screen: Surface, pos: tuple[int, int], state: StateKey = "normal"
    ) -> None:
        """Draw the resolved state shadow behind a widget at ``pos``."""
        resolved = self._resolved_style(state)
        shadow = self.shadow_surface(state)
        if shadow is not None and resolved.shadow is not None:
            screen.blit(shadow, (pos[0] + resolved.shadow[0], pos[1] + resolved.shadow[1]))

    def draw_base(self, state: StateKey = "normal") -> None:
        """Paint chrome (background/gradient/border) into the local surface.

        Flat background when no gradient is configured; nothing at all
        when the style carries neither (transparent chrome). The border
        strokes the full box at ``style.radius`` using
        :attr:`border_width`.
        """
        local_surf = self.local_surface
        local_surf.fill((0, 0, 0, 0))
        resolved = self._resolved_style(state)

        width = self.box_model["full_width"]
        height = self.box_model["full_height"]
        bw = self._border_width

        if resolved.gradient is not None and width > 0 and height > 0:
            gradient = self._gradient_surface(state, width, height, resolved.radius)
            if gradient is not None:
                local_surf.blit(gradient, (0, 0))
        elif resolved.bg is not None and width > 0 and height > 0:
            pygame.draw.rect(
                local_surf,
                resolved.bg,
                (0, 0, width, height),
                border_radius=resolved.radius,
            )

        self.draw_background_image(state)

        if resolved.border is not None and bw > 0 and self.box_model["full_width"] > 0:
            pygame.draw.rect(
                local_surf,
                resolved.border,
                (0, 0, *local_surf.get_size()),
                width=bw,
                border_radius=resolved.radius,
            )

    def _background_content_rect(self) -> pygame.Rect:
        """Local bounds for generic background art, inside padding and border."""
        return pygame.Rect(
            self.box_model["left"],
            self.box_model["top"],
            self.box_model["content_width"],
            self.box_model["content_height"],
        )

    @staticmethod
    def _cover_scale(image: Surface, width: int, height: int) -> Surface:
        """Nearest-neighbour, aspect-preserving cover scale for game art."""
        source_w, source_h = image.get_size()
        if source_w <= 0 or source_h <= 0 or width <= 0 or height <= 0:
            return Surface((max(1, width), max(1, height)), SRCALPHA)
        scale = max(width / source_w, height / source_h)
        scaled_size = (
            max(1, round(source_w * scale)),
            max(1, round(source_h * scale)),
        )
        if scaled_size == image.get_size():
            return image.copy()
        return pygame.transform.scale(image, scaled_size)

    def _background_image_surface(
        self,
        state: StateKey,
        content_rect: pygame.Rect,
        clip_mask: Surface | None = None,
        clip_key: object | None = None,
    ) -> Surface | None:
        """Build/cache one cover-scaled, shape-clipped content image."""
        image = self._background_image
        if image is None or content_rect.width <= 0 or content_rect.height <= 0:
            return None
        resolved = self._resolved_style(state)
        inner_radius = max(0, resolved.radius - self.border_width)
        if clip_mask is not None and clip_key is None:
            return self._build_background_image_surface(state, content_rect, inner_radius, clip_mask)
        key = (
            id(image),
            image.get_size(),
            tuple(content_rect),
            inner_radius,
            clip_key,
        )
        cached = self._background_image_cache.get(key)
        if cached is not None:
            return cached

        built = self._build_background_image_surface(state, content_rect, inner_radius, clip_mask)
        self._background_image_cache[key] = built
        return built

    def _build_background_image_surface(
        self,
        state: StateKey,
        content_rect: pygame.Rect,
        inner_radius: int,
        clip_mask: Surface | None,
    ) -> Surface:
        image = self._background_image
        assert image is not None
        width, height = content_rect.size
        scaled = self._cover_scale(image, width, height)
        cached = Surface((width, height), SRCALPHA)
        cached.fill((0, 0, 0, 0))
        cached.blit(
            scaled,
            ((width - scaled.get_width()) // 2, (height - scaled.get_height()) // 2),
        )

        if clip_mask is None:
            clip_mask = Surface((width, height), SRCALPHA)
            clip_mask.fill((0, 0, 0, 0))
            pygame.draw.rect(
                clip_mask,
                (255, 255, 255, 255),
                (0, 0, width, height),
                border_radius=min(inner_radius, width // 2, height // 2),
            )
        cached.blit(clip_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        return cached

    def draw_background_image(
        self,
        state: StateKey = "normal",
        *,
        content_rect: pygame.Rect | None = None,
        clip_mask: Surface | None = None,
        clip_key: object | None = None,
    ) -> None:
        """Paint shared background art beneath borders and widget content."""
        rect = content_rect.copy() if content_rect is not None else self._background_content_rect()
        rect = rect.clip(self.rect)
        image = self._background_image_surface(state, rect, clip_mask, clip_key)
        if image is not None:
            self.local_surface.blit(image, rect.topleft)

    def draw_polygon(
        self,
        points: list[tuple[int, int]],
        state: StateKey = "normal",
        *,
        outline_width: int | None = None,
        content_rect: pygame.Rect | None = None,
    ) -> None:
        """Paint a polygon through the shared style engine.

        Polygons are widget geometry, but the paint rules still belong to
        :class:`UIBase`: resolved flat fills, gradients, borders, and their
        validation/caching semantics are identical to rounded rectangles.
        """
        self.local_surface.fill((0, 0, 0, 0))
        if len(points) < 3:
            return

        resolved = self._resolved_style(state)
        width, height = self.size
        mask = Surface((max(1, width), max(1, height)), SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.polygon(mask, (255, 255, 255, 255), points)

        if resolved.gradient is not None:
            painted = self._gradient_surface(state, width, height, 0)
            if painted is not None:
                painted = painted.copy()
                painted.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
                self.local_surface.blit(painted, (0, 0))
        elif resolved.bg is not None:
            pygame.draw.polygon(self.local_surface, resolved.bg, points)

        rect = content_rect.copy() if content_rect is not None else self._background_content_rect()
        rect = rect.clip(self.rect)
        if rect.width > 0 and rect.height > 0:
            mask = Surface(rect.size, SRCALPHA)
            mask.fill((0, 0, 0, 0))
            translated = [(x - rect.x, y - rect.y) for x, y in points]
            pygame.draw.polygon(mask, (255, 255, 255, 255), translated)
            self.draw_background_image(
                state,
                content_rect=rect,
                clip_mask=mask,
                clip_key=("polygon", tuple(points), tuple(rect)),
            )

        if resolved.border is not None:
            width_to_draw = self._border_width if outline_width is None else outline_width
            if width_to_draw > 0:
                pygame.draw.polygon(
                    self.local_surface,
                    resolved.border,
                    points,
                    width_to_draw,
                )


    @property
    def size(self) -> tuple[int, int]:
        return (self.box_model["full_width"], self.box_model["full_height"])

    @property
    def rect(self) -> "pygame.Rect":
        return pygame.Rect(0, 0, self.box_model["full_width"], self.box_model["full_height"])

    def add_plugin(self, cb: Callable[[Surface], Any]) -> None:
        self.renderable_plugins.append(cb)

    def invalidate(self) -> None:
        """Drop every cached chrome artifact; rebuilt lazily on next render."""
        self._resolved_cache.clear()
        self._gradient_cache.clear()
        self._shadow_cache.clear()
        self._background_image_cache.clear()

    def render(self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)) -> None:
        pos = (
            self.box_model["offset_x"] + pos_offset[0],
            self.box_model["offset_y"] + pos_offset[1],
        )
        self.draw_shadow(screen, pos)
        self.draw_base()
        for plugin in self.renderable_plugins:
            plugin(self.local_surface)
        screen.blit(self.local_surface, pos)

    def update(self, dt: float = 0.0) -> None:
        pass


__all__ = [
    "BoxModel",
    "BoxModelResult",
    "UIOptions",
    "UIBase",
    "ColorLike",
    "UIStyle",
    "ResolvedStyle",
    "StateKey",
    "STATE_KEYS",
]
