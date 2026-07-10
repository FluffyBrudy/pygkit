"""
Asset caching and procedural generation for the Inventory System.

Provides optimized caching of static UI elements and procedural
generation of item icons to avoid runtime overhead.
"""

from __future__ import annotations

from typing import Optional

import pygame
from pygame import SRCALPHA, Surface
from pygame.typing import ColorLike


class AssetCache:
    """
    Singleton-style cache for static UI assets.

    Caches procedurally generated surfaces to avoid redundant creation.
    Automatically handles different sizes and colors.
    """

    _instance: Optional[AssetCache] = None

    def __new__(cls) -> AssetCache:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True

        self._slot_surfaces: dict[tuple[int, int, str], Surface] = {}
        self._icon_surfaces: dict[tuple[str, tuple[int, int], ColorLike], Surface] = {}
        self._background_surfaces: dict[tuple[int, int, int, ColorLike], Surface] = {}

    def clear(self) -> None:
        """Clear all cached surfaces."""
        self._slot_surfaces.clear()
        self._icon_surfaces.clear()
        self._background_surfaces.clear()

    def get_slot_surface(
        self,
        size: int | tuple[int, int],
        border_radius: int = 4,
        style: str = "default",
    ) -> Surface:
        """
        Get or create a cached slot background surface.

        Args:
            size: Slot size (width, height) or single int for square
            border_radius: Corner radius for rounded slots
            style: Style variant ("default", "highlighted", "invalid")

        Returns:
            Cached surface for the slot
        """
        if isinstance(size, int):
            size = (size, size)

        key = (*size, style)

        if key not in self._slot_surfaces:
            self._slot_surfaces[key] = self._create_slot_surface(size, border_radius, style)

        return self._slot_surfaces[key].copy()

    def _create_slot_surface(
        self,
        size: tuple[int, int],
        border_radius: int,
        style: str,
    ) -> Surface:
        """Create a new slot surface (internal use)."""
        surf = Surface(size, SRCALPHA)
        surf.fill((0, 0, 0, 0))

        if style == "default":
            color = (60, 60, 70, 200)
        elif style == "highlighted":
            color = (100, 150, 200, 180)
        elif style == "invalid":
            color = (200, 80, 80, 180)
        else:
            color = (60, 60, 70, 200)

        w, h = int(size[0]), int(size[1])
        pygame.draw.rect(surf, color, (0, 0, w, h), border_radius=border_radius)

        inner_rect = pygame.Rect(2, 2, size[0] - 4, size[1] - 4)
        pygame.draw.rect(surf, (80, 80, 90, 150), inner_rect, width=1, border_radius=max(0, border_radius - 1))

        return surf

    def get_icon_surface(
        self,
        shape: str,
        size: int | tuple[int, int],
        color: ColorLike,
    ) -> Surface:
        """
        Get or create a cached item icon surface.

        Args:
            shape: Icon shape ("circle", "square", "diamond", "cross", "star")
            size: Icon size (width, height) or single int for square
            color: RGBA color for the icon

        Returns:
            Cached surface with the icon rendered
        """
        if isinstance(size, int):
            size = (size, size)

        color_tuple = tuple(color) if not isinstance(color, tuple) else color

        key = (shape, size, color_tuple)

        if key not in self._icon_surfaces:
            self._icon_surfaces[key] = self._create_icon_surface(shape, size, color)

        return self._icon_surfaces[key].copy()

    def _create_icon_surface(
        self,
        shape: str,
        size: tuple[int, int],
        color: ColorLike,
    ) -> Surface:
        """Create a new icon surface (internal use)."""
        surf = Surface(size, SRCALPHA)
        surf.fill((0, 0, 0, 0))

        center_x = size[0] // 2
        center_y = size[1] // 2
        radius = min(size[0], size[1]) // 2 - 4

        if shape == "circle":
            pygame.draw.circle(surf, color, (center_x, center_y), radius)

        elif shape == "square":
            rect = pygame.Rect(
                center_x - radius,
                center_y - radius,
                radius * 2,
                radius * 2,
            )
            pygame.draw.rect(surf, color, rect, border_radius=4)

        elif shape == "diamond":
            points = [
                (center_x, center_y - radius),
                (center_x + radius, center_y),
                (center_x, center_y + radius),
                (center_x - radius, center_y),
            ]
            pygame.draw.polygon(surf, color, points)

        elif shape == "cross":
            arm_width = radius // 3

            pygame.draw.rect(surf, color, (center_x - arm_width, center_y - radius, arm_width * 2, radius * 2))

            pygame.draw.rect(surf, color, (center_x - radius, center_y - arm_width, radius * 2, arm_width * 2))

        elif shape == "star":
            outer_r = radius
            inner_r = radius // 2
            points = []
            import math

            for i in range(8):
                r = outer_r if i % 2 == 0 else inner_r
                rad = math.radians(i * 45)
                x = center_x + r * math.cos(rad)
                y = center_y + r * math.sin(rad)
                points.append((x, y))
            pygame.draw.polygon(surf, color, points)

        else:
            pygame.draw.circle(surf, color, (center_x, center_y), radius)

        return surf

    def get_background_surface(
        self,
        width: int,
        height: int,
        border_radius: int,
        color: ColorLike,
    ) -> Surface:
        """
        Get or create a cached background panel surface.

        Args:
            width: Panel width
            height: Panel height
            border_radius: Corner radius
            color: Background color (RGBA)

        Returns:
            Cached background surface
        """
        color_tuple = tuple(color) if not isinstance(color, tuple) else color
        key = (width, height, border_radius, color_tuple)

        if key not in self._background_surfaces:
            self._background_surfaces[key] = self._create_background_surface(width, height, border_radius, color)

        return self._background_surfaces[key].copy()

    def _create_background_surface(
        self,
        width: int,
        height: int,
        border_radius: int,
        color: ColorLike,
    ) -> Surface:
        """Create a new background surface (internal use)."""
        surf = Surface((width, height), SRCALPHA)
        surf.fill((0, 0, 0, 0))

        pygame.draw.rect(surf, color, (0, 0, width, height), border_radius=border_radius)

        return surf


_cache: Optional[AssetCache] = None


def get_cache() -> AssetCache:
    """Get the global asset cache instance."""
    global _cache
    if _cache is None:
        _cache = AssetCache()
    return _cache


def generate_procedural_icon(
    shape: str,
    size: int = 32,
    color: ColorLike = (200, 200, 200, 255),
) -> Surface:
    """
    Generate a procedural item icon.

    Convenience function that uses the global cache.

    Args:
        shape: Icon shape ("circle", "square", "diamond", "cross", "star")
        size: Icon size in pixels
        color: RGBA color

    Returns:
        Surface with the rendered icon
    """
    return get_cache().get_icon_surface(shape, size, color)


def render_quantity_text(
    quantity: int,
    font: pygame.font.Font,
    color: ColorLike = (255, 255, 255, 255),
    outline_color: ColorLike = (0, 0, 0, 255),
) -> Surface:
    """
    Render quantity text with outline for readability.

    Args:
        quantity: Number to display
        font: Font to use
        color: Text color
        outline_color: Outline color

    Returns:
        Surface with rendered text
    """
    if quantity <= 1:
        return Surface((1, 1), SRCALPHA)

    text = str(quantity)

    base_surf = font.render(text, True, color)

    thickness = 1
    w = base_surf.get_width() + thickness * 2
    h = base_surf.get_height() + thickness * 2
    result = Surface((w, h), SRCALPHA)
    result.fill((0, 0, 0, 0))

    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx == 0 and dy == 0:
                continue
            outline = font.render(text, True, outline_color)
            result.blit(outline, (thickness + dx, thickness + dy))

    result.blit(base_surf, (thickness, thickness))

    return result
