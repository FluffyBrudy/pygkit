"""
Light map - the core of the 2D lighting pipeline.

The classic 2D approach, generalized: render all lights into a small
grayscale/colored surface (the light map), then multiply the scene by it.
Every frame costs one fill, a few small sprite blits, one scaled blit and
one multiply - no full-screen allocations, so it stays at 60 FPS.

Frame usage::

    lightmap = LightMap((800, 600), scale=0.5)
    lightmap.set_ambient((20, 25, 40), 0.15)

    # per frame:
    lightmap.clear()            # reset to ambient
    torch.render(lightmap, tx, ty)
    spotlight.render(lightmap, sx, sy)
    lightmap.apply(scene)       # scene gets darkened + lit in place
"""

from __future__ import annotations

import pygame
from pygame import Surface

from pygkit.lighting.blend import LIGHT_ADD, SCENE_MULT

__all__ = ["LightMap"]


class LightMap:
    """
    Low-resolution light map that composites lights and applies them to a
    scene surface with a configurable blend mode.
    """

    __slots__ = (
        "_size",
        "_scale",
        "_lightmap",
        "_scaled",
        "_ambient_color",
        "_ambient_intensity",
        "_pixelated",
    )

    def __init__(
        self,
        size: tuple[int, int],
        scale: float = 0.5,
        pixelated: bool = False,
    ) -> None:
        """
        Args:
            size: scene size in pixels the light map will be applied to
            scale: light map resolution as a fraction of ``size``
                (0.25 - 0.5 is a good range; lower is faster)
            pixelated: use nearest-neighbor scaling instead of smoothing
                for a chunky pixel-art light look
        """
        self._size = size
        self._scale = scale
        self._pixelated = pixelated
        self._ambient_color = (0, 0, 0)
        self._ambient_intensity = 0.0

        lw = max(1, round(size[0] * scale))
        lh = max(1, round(size[1] * scale))
        self._lightmap = pygame.Surface((lw, lh), pygame.SRCALPHA)
        self._scaled = pygame.Surface(size, pygame.SRCALPHA)

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def scale(self) -> float:
        return self._scale

    @property
    def pixelated(self) -> bool:
        return self._pixelated

    @pixelated.setter
    def pixelated(self, value: bool) -> None:
        self._pixelated = bool(value)

    @property
    def lightmap_size(self) -> tuple[int, int]:
        return self._lightmap.get_size()

    def set_scale(self, scale: float) -> None:
        """Recreate the light map at a new resolution fraction of ``size``."""
        self._scale = scale
        lw = max(1, round(self._size[0] * scale))
        lh = max(1, round(self._size[1] * scale))
        self._lightmap = pygame.Surface((lw, lh), pygame.SRCALPHA)

    def set_ambient(
        self, color: tuple[int, int, int] = (0, 0, 0), intensity: float = 0.0
    ) -> None:
        """Set the base darkness color and how much of it shows (0-1)."""
        self._ambient_color = color
        self._ambient_intensity = max(0.0, min(1.0, intensity))

    def clear(self) -> None:
        """Reset the light map to the ambient color. Call once per frame."""
        r, g, b = self._ambient_color
        i = self._ambient_intensity
        self._lightmap.fill(
            (int(r * i), int(g * i), int(b * i), 255)
        )

    def add_sprite(
        self,
        sprite: Surface,
        x: float,
        y: float,
        blend: int = LIGHT_ADD,
        lightmap_coords: bool = False,
    ) -> None:
        """
        Blit a light sprite centered at ``(x, y)``.

        By default ``(x, y)`` are scene coordinates and get scaled by the
        light map's resolution factor. Pass ``lightmap_coords=True`` when
        the sprite was generated directly at light map resolution (see
        ``pygkit.lighting.DynamicLight``); the coordinates are then used
        as-is.

        ``blend`` defaults to additive (LIGHT_ADD = RGB_ADD); pass RGB_SUB /
        RGBA_SUB for negative lights / shadows.
        """
        if lightmap_coords:
            lx, ly = x, y
        else:
            s = self._scale
            lx, ly = x * s, y * s
        sw, sh = sprite.get_size()
        self._lightmap.blit(
            sprite,
            (round(lx - sw / 2), round(ly - sh / 2)),
            special_flags=blend,
        )

    def apply(self, surface: Surface, blend: int = SCENE_MULT) -> Surface:
        """
        Apply the light map to ``surface`` in place and return it.

        The default blend (SCENE_MULT = RGB_MULT) darkens unlit areas and
        reveals the scene in lit ones. Pass RGB_ADD / RGB_SUB / RGB_MAX / ...
        compositing styles.
        """
        tw, th = surface.get_size()
        if self._scaled.get_size() != (tw, th):
            self._scaled = pygame.Surface((tw, th), pygame.SRCALPHA)

        if self._pixelated:
            pygame.transform.scale(self._lightmap, (tw, th), self._scaled)
        else:
            pygame.transform.smoothscale(self._lightmap, (tw, th), self._scaled)

        surface.blit(self._scaled, (0, 0), special_flags=blend)
        return surface
