"""
Light objects - game-agnostic, position is set by the caller each frame.

Nothing here knows about colliders, cameras or the game world. A light
renders itself onto a LightMap in a single small blit::

    torch = PointLight(radius=140, color=(255, 190, 120))
    torch.set_flicker(frequency=8.0, amplitude=0.2)
    torch.render(lightmap, player.x, player.y)
"""

from __future__ import annotations

import math
import random

import pygame
from pygame import Surface

from pygkit.lighting.blend import LIGHT_ADD
from pygkit.lighting.lightmap import LightMap
from pygkit.lighting.sprites import dynamic_glow_sprite, glow_sprite, spotlight_sprite

__all__ = ["PointLight", "Spotlight", "DynamicLight"]


def _dimmed(sprite: Surface, factor: int) -> Surface:
    """
    Return a copy of ``sprite`` with every pixel's color scaled by
    ``factor`` / 255 (``factor == 255`` returns the sprite unchanged).

    Special-flag blits (RGBA_ADD etc.) ignore per-surface alpha, so
    brightness/intensity has to be baked into the pixel colors instead.
    Never mutates the input - callers may pass cached/shared sprites.
    """
    if factor >= 255:
        return sprite
    dimmed = sprite.copy()
    dimmed.fill((factor, factor, factor), special_flags=pygame.BLEND_RGB_MULT)
    return dimmed


def flicker_value(frequency: float, amplitude: float, jitter: float, t: float) -> float:
    """
    Flame-like modulation in [0, 1]: two detuned sines plus per-call
    random jitter. ``frequency <= 0`` (or ``amplitude <= 0``) returns 1.0.
    """
    if frequency <= 0 or amplitude <= 0:
        return 1.0
    f = frequency
    v = (
        1.0
        - amplitude
        + amplitude * 0.6 * math.sin(2 * math.pi * f * t)
        + amplitude * 0.4 * math.sin(2 * math.pi * f * 2.4 * t + 1.3)
    )
    if jitter > 0:
        v += jitter * random.uniform(-1.0, 1.0)
    return max(0.0, min(1.0, v))


class PointLight:
    """
    Radial light with a cached glow sprite and optional organic flicker.

    The sprite (and its per-light copy) is generated once; per frame the
    cost is one ``set_alpha`` and one small blit.
    """

    __slots__ = (
        "radius",
        "color",
        "intensity",
        "falloff",
        "exponent",
        "_freq",
        "_amp",
        "_jitter",
        "_time",
        "_sprite",
    )

    def __init__(
        self,
        radius: int = 100,
        color: tuple[int, int, int] = (255, 255, 255),
        intensity: float = 1.0,
        falloff: str = "exp",
        exponent: float = 4.0,
    ) -> None:
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.falloff = falloff
        self.exponent = exponent
        self._freq = 0.0
        self._amp = 0.0
        self._jitter = 0.0
        self._time = 0.0
        self._sprite: Surface | None = None

    def set_flicker(
        self,
        frequency: float = 8.0,
        amplitude: float = 0.15,
        jitter: float = 0.05,
    ) -> None:
        """
        Enable a flame-like flicker. ``frequency <= 0`` disables it.

        The modulation is two detuned sine waves (irregular, organic) plus
        a per-frame random jitter; advance time with :meth:`advance`.
        """
        self._freq = frequency
        self._amp = max(0.0, min(0.9, amplitude))
        self._jitter = max(0.0, jitter)

    def advance(self, dt: float) -> None:
        """Advance flicker time by ``dt`` seconds."""
        self._time += dt

    def sprite(self) -> Surface:
        """The light's private glow sprite (do not mutate externally)."""
        if self._sprite is None:
            self._sprite = glow_sprite(
                self.radius, self.color, self.falloff, self.exponent
            ).copy()
        return self._sprite

    def modulation(self) -> float:
        """Current flicker multiplier in [0, 1]."""
        return flicker_value(self._freq, self._amp, self._jitter, self._time)

    def render(
        self, lightmap: LightMap, x: float, y: float, blend: int = LIGHT_ADD
    ) -> None:
        """Blit the light centered at scene coordinates ``(x, y)``."""
        alpha = int(255 * self.intensity * self.modulation())
        if alpha <= 0:
            return
        sprite = _dimmed(self.sprite(), alpha)
        lightmap.add_sprite(sprite, x, y, blend)


class Spotlight:
    """
    Cone light with configurable spread and soft edge.

    The base cone sprite points right (+x); :meth:`set_direction` rotates
    it. Rotation results are cached in small angle buckets (default 4
    degrees), so following the mouse only costs a cached lookup.
    """

    __slots__ = (
        "radius",
        "color",
        "intensity",
        "cone",
        "softness",
        "falloff",
        "exponent",
        "direction",
        "rotation_step",
        "_base",
        "_rotations",
    )

    def __init__(
        self,
        radius: int = 200,
        color: tuple[int, int, int] = (255, 255, 255),
        intensity: float = 1.0,
        cone: float = math.pi / 4,
        softness: float = 0.15,
        falloff: str = "exp",
        exponent: float = 4.0,
        rotation_step: float = 4.0,
    ) -> None:
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.cone = cone
        self.softness = softness
        self.falloff = falloff
        self.exponent = exponent
        self.direction = 0.0
        self.rotation_step = rotation_step
        self._base: Surface | None = None
        self._rotations: dict[float, Surface] = {}

    def set_direction(self, angle: float) -> None:
        """
        Aim the cone at ``angle`` radians (pygame convention: 0 = right,
        pi/2 = down, matching ``math.atan2(dy, dx)`` for screen coords).
        """
        self.direction = angle

    def _base_sprite(self) -> Surface:
        if self._base is None:
            self._base = spotlight_sprite(
                self.radius,
                self.color,
                self.cone,
                self.softness,
                self.falloff,
                self.exponent,
            ).copy()
        return self._base

    def sprite(self) -> Surface:
        """Rotated sprite for the current direction (cached by angle bucket)."""
        if self.rotation_step <= 0:
            return self._base_sprite()

        step = math.radians(self.rotation_step)
        key = round(self.direction / step) * step
        key %= 2 * math.pi

        cached = self._rotations.get(key)
        if cached is not None:
            return cached

        rotated = pygame.transform.rotate(self._base_sprite(), -math.degrees(key))
        self._rotations[key] = rotated
        capacity = math.ceil(360.0 / max(self.rotation_step, 1e-3))
        if len(self._rotations) > capacity:
            self._rotations.pop(next(iter(self._rotations)))
        return rotated

    def render(
        self, lightmap: LightMap, x: float, y: float, blend: int = LIGHT_ADD
    ) -> None:
        """Blit the cone centered at scene coordinates ``(x, y)``."""
        alpha = int(255 * self.intensity)
        if alpha <= 0:
            return
        sprite = _dimmed(self.sprite(), alpha)
        lightmap.add_sprite(sprite, x, y, blend)


_WIND_DIRS = 16
_WIND_LEVELS = 3


def _wind_strength(vx: float, vy: float, radius: int) -> float:
    """Normalize a wind vector to 0..1 relative to the light's radius."""
    return min(1.0, math.hypot(vx, vy) / max(1.0, radius * 0.6))


def _wind_bucket(vx: float, vy: float, radius: int) -> int:
    """
    Quantize a wind vector to a coarse bucket (16 directions x 3 levels,
    0 = no wind). Sprite regeneration only happens when the bucket changes.
    """
    s = _wind_strength(vx, vy, radius)
    if s < 0.05:
        return 0
    level = 2 if s >= 0.75 else (1 if s >= 0.35 else 0)
    if level == 0:
        return 0
    angle = math.atan2(vy, vx) % (2 * math.pi)
    direction = round(angle / (2 * math.pi / _WIND_DIRS)) % _WIND_DIRS
    return (level - 1) * _WIND_DIRS + direction + 1


class DynamicLight:
    """
    Direction-reactive light for flames and other flowing glows.

    The glow elongates along the flow direction and its hot core shifts
    against it, like a flame pushed by the wind. The sprite shape is
    regenerated at light map resolution only when the direction crosses a
    coarse direction/strength bucket, so most frames cost the same single
    blit as a static light. Regenerating a radius-120 light at
    ``scale=0.25`` (a 60 px sprite) takes well under a millisecond.

    Direction uses the particle-system convention: compass degrees,
    ``0`` = right, ``90`` = down, ``180`` = left, ``270`` = up (screen
    coordinates). Feed it the same direction your particle presets use so
    the glow and the particles stay visually consistent::

        fire = DynamicLight(radius=130, color=(255, 160, 90))
        fire.set_direction(270, 0.6)   # upward flow, like a campfire
        fire.render(lightmap, fire_x, fire_y)
    """

    __slots__ = (
        "radius",
        "color",
        "intensity",
        "exponent",
        "stretch",
        "core_shift",
        "seed",
        "wind",
        "_freq",
        "_amp",
        "_jitter",
        "_time",
        "_sprite",
        "_bucket",
        "_bake_scale",
        "_regen_interval",
        "_regen_counter",
    )

    def __init__(
        self,
        radius: int = 120,
        color: tuple[int, int, int] = (255, 170, 90),
        intensity: float = 1.0,
        exponent: float = 4.0,
        stretch: float = 1.8,
        core_shift: float = 0.35,
        seed: int = 0,
        direction: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.exponent = exponent
        self.stretch = stretch
        self.core_shift = core_shift
        self.seed = seed
        self.wind = direction
        self._freq = 0.0
        self._amp = 0.0
        self._jitter = 0.0
        self._time = 0.0
        self._sprite: Surface | None = None
        self._bucket: int | None = None
        self._bake_scale = 0.0
        self._regen_interval = 0
        self._regen_counter = 0

    def set_wind(self, vx: float, vy: float) -> None:
        """Set the flow vector directly (scene units, e.g. px per frame)."""
        self.wind = (vx, vy)

    def set_direction(self, direction: float, strength: float = 1.0) -> None:
        """
        Set the flow direction from compass degrees (0 = right, 90 = down,
        180 = left, 270 = up) and a strength in 0..1 - the same convention
        particle systems use for their ``direction`` presets.

        The strength is normalized to the light's radius, so 1.0 produces
        the full elongation/lean (the same scale ``set_wind`` expresses in
        px per frame, where ``radius * 0.6`` px/frame is full strength).
        """
        angle = math.radians(direction)
        scale = strength * max(1.0, self.radius * 0.6)
        self.wind = (math.cos(angle) * scale, math.sin(angle) * scale)

    def set_flicker(
        self,
        frequency: float = 8.0,
        amplitude: float = 0.2,
        jitter: float = 0.06,
    ) -> None:
        """Enable flame-like brightness flicker (``frequency <= 0`` off)."""
        self._freq = frequency
        self._amp = max(0.0, min(0.9, amplitude))
        self._jitter = max(0.0, jitter)

    def set_regen_interval(self, frames: int) -> None:
        """
        Force a sprite regeneration every ``frames`` rendered frames (0 =
        off). Re-bakes the glow with a slightly different wobble phase for
        a dancing flame at the cost of one small regeneration per interval.
        """
        self._regen_interval = max(0, frames)

    def advance(self, dt: float) -> None:
        """Advance flicker time by ``dt`` seconds."""
        self._time += dt

    def modulation(self) -> float:
        """Current flicker multiplier in [0, 1]."""
        return flicker_value(self._freq, self._amp, self._jitter, self._time)

    def _bake(self, lightmap: LightMap) -> Surface:
        lm_radius = max(2, round(self.radius * lightmap.scale))
        phase = self.seed + (self._regen_counter % 97)
        sprite = dynamic_glow_sprite(
            lm_radius,
            self.color,
            self.wind,
            self.stretch,
            self.core_shift,
            self.exponent,
            phase,
        )
        self._bake_scale = lightmap.scale
        # never share the generator cache: per-light alpha and wobble
        # changes must not leak across lights
        return sprite.copy()

    def sprite(self, lightmap: LightMap) -> Surface:
        """
        Current sprite at light map resolution; regenerates when the wind
        bucket changes, the light map scale changes (or a regen interval
        is set and due).
        """
        bucket = _wind_bucket(self.wind[0], self.wind[1], self.radius)
        self._regen_counter += 1
        force = self._regen_interval > 0 and self._regen_counter % self._regen_interval == 0
        scale_changed = lightmap.scale != self._bake_scale
        if self._sprite is None or bucket != self._bucket or force or scale_changed:
            self._bucket = bucket
            self._sprite = self._bake(lightmap)
        return self._sprite

    def render(
        self, lightmap: LightMap, x: float, y: float, blend: int = LIGHT_ADD
    ) -> None:
        """Blit the light centered at scene coordinates ``(x, y)``."""
        alpha = int(255 * self.intensity * self.modulation())
        if alpha <= 0:
            return
        sprite = _dimmed(self.sprite(lightmap), alpha)
        s = lightmap.scale
        lightmap.add_sprite(sprite, x * s, y * s, blend, lightmap_coords=True)
