"""
Precomputed light sprite generators.

Light sprites are generated once per unique parameter set and cached, so
rendering a light costs a single small blit per frame. Generation is a
per-pixel loop; it only runs on the first use of a given parameter set, so
reuse sprites (or keep radii modest) in hot paths.

The generated sprites are fully opaque with color falloff, matching the
classic 2D light map approach: an additive blit of black (0, 0, 0) adds
nothing, and white (255, 255, 255) adds maximum brightness.
"""

from __future__ import annotations

import math
from typing import Any

import pygame
from pygame import Surface

_cache: dict[tuple[Any, ...], Surface] = {}
_CACHE_MAX = 128  # bound memory when callers vary parameters (e.g. radii)


def _store(key: tuple[Any, ...], surf: Surface) -> Surface:
    """Cache ``surf`` under ``key``, evicting the oldest entry when full."""
    if len(_cache) >= _CACHE_MAX:
        _cache.pop(next(iter(_cache)))
    _cache[key] = surf
    return surf


def clear_sprite_cache() -> None:
    """Drop all cached sprites (mainly useful for tests)."""
    _cache.clear()


def _falloff(n: float, kind: str, exponent: float) -> float:
    """Distance falloff factor for normalized distance ``n`` in [0, 1)."""
    if kind == "exp":
        return math.exp(-exponent * n * n)
    if kind == "linear":
        return 1.0 - n
    if kind == "smooth":
        t = 1.0 - n * n
        return t * t
    if kind == "sharp":
        return (1.0 - n) ** exponent
    raise ValueError(f"unknown falloff {kind!r} (expected exp/linear/smooth/sharp)")


def glow_sprite(
    radius: int,
    color: tuple[int, int, int] = (255, 255, 255),
    falloff: str = "exp",
    exponent: float = 4.0,
) -> Surface:
    """
    Circular radial glow sprite of ``2 * radius`` pixels.

    The center keeps the requested color at full value and falls off to
    black at the edge. ``exponent=4.0`` gives the classic
    ``e ** (-4 * n * n)`` falloff (a soft, wide glow); higher exponents
    tighten the core into a hot spot.

    The returned surface is shared between callers - do not mutate it.
    Use ``.copy()`` when a light needs per-light alpha or color tweaks.
    """
    key = ("glow", radius, color, falloff, exponent)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    size = max(2, radius * 2)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = radius
    r2 = radius * radius
    r, g, b = color

    for y in range(size):
        dy = y - cy
        dy2 = dy * dy
        for x in range(size):
            dx = x - cx
            d2 = dx * dx + dy2
            if d2 >= r2:
                continue
            n = math.sqrt(d2) / radius
            v = _falloff(n, falloff, exponent)
            surf.set_at((x, y), (int(r * v), int(g * v), int(b * v), 255))

    return _store(key, surf)


def dynamic_glow_sprite(    radius: int,
    color: tuple[int, int, int] = (255, 255, 255),
    wind: tuple[float, float] = (0.0, 0.0),
    stretch: float = 1.8,
    core_shift: float = 0.35,
    exponent: float = 4.0,
    seed: int = 0,
) -> Surface:
    """
    Wind-reactive glow sprite of ``2 * radius`` pixels, generated on demand.

    Unlike :func:`glow_sprite` the falloff is anisotropic: the glow
    elongates along the ``wind`` axis (``stretch``) and its hot core shifts
    against the wind (``core_shift`` as a fraction of ``radius``), so the
    light leans the same way a flame pushed by the wind would.

    The function is deterministic - identical arguments always produce
    identical pixels, so it can be cached per wind vector. Pass ``seed`` to
    vary the subtle directional wobble between lights.

    With negligible wind this falls back to the shared :func:`glow_sprite`
    cache entry - copy it before mutating (``set_alpha``, ``fill``, ...).

    Generate it at light map resolution for dynamic lights (see
    ``pygkit.lighting.DynamicLight``): a radius-120 light at ``scale=0.25``
    is a 60 px sprite and regenerates in well under a millisecond.
    """
    size = max(2, radius * 2)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = radius
    r, g, b = color

    vx, vy = wind
    wlen = math.hypot(vx, vy)
    s = 0.0
    if wlen > 1e-6:
        s = min(1.0, wlen / max(1.0, radius * 0.6))
        ux, uy = vx / wlen, vy / wlen
    else:
        ux, uy = 1.0, 0.0

    if s <= 1e-4:
        # no wind: fall back to the plain isotropic glow. Note this
        # returns the shared glow_sprite cache entry - copy it before
        # mutating (set_alpha, fill, ...), just like glow_sprite.
        return glow_sprite(radius, color, "exp", exponent)

    a_axis = 1.0 + (stretch - 1.0) * s  # elongate along the wind
    b_axis = 1.0 / a_axis  # keep area roughly constant
    shift = core_shift * radius * s  # hot core displaced against the wind
    wob = 0.08 * radius * s  # subtle seeded waviness
    phase = seed * 0.61803398875
    r2 = radius * radius

    for y in range(size):
        dy = y - cy
        for x in range(size):
            dx = x - cx
            along = dx * ux + dy * uy + shift + math.sin(dy * 0.18 + phase) * wob
            perp = dx * -uy + dy * ux
            n2 = ((along / a_axis) ** 2 + (perp / b_axis) ** 2) / r2
            if n2 >= 1.0:
                continue
            v = math.exp(-exponent * n2)
            if v < 1.0 / 255.0:
                continue
            surf.set_at((x, y), (int(r * v), int(g * v), int(b * v), 255))

    return surf


def spotlight_sprite(
    radius: int,
    color: tuple[int, int, int] = (255, 255, 255),
    cone: float = math.pi / 4,
    softness: float = 0.15,
    falloff: str = "exp",
    exponent: float = 4.0,
) -> Surface:
    """
    Cone-shaped light sprite of ``2 * radius`` pixels pointing right (+x).

    ``cone`` is the half-angle of the cone in radians, ``softness`` the
    angular feather width in radians over which the edge fades to black.
    Rotate the result (``pygame.transform.rotate``) to aim it elsewhere.

    The returned surface is shared between callers - do not mutate it.
    """
    key = (
        "spot",
        radius,
        color,
        round(cone, 6),
        round(softness, 6),
        falloff,
        exponent,
    )
    cached = _cache.get(key)
    if cached is not None:
        return cached

    size = max(2, radius * 2)
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = cy = radius
    r2 = radius * radius
    r, g, b = color
    half = cone
    feather = softness if softness > 0 else 0.0

    for y in range(size):
        dy = y - cy
        for x in range(size):
            dx = x - cx
            d2 = dx * dx + dy * dy
            if d2 >= r2:
                continue
            n = math.sqrt(d2) / radius
            a = abs(math.atan2(dy, dx))
            if a > half + feather:
                continue
            if a > half:
                am = 1.0 - (a - half) / feather
            else:
                am = 1.0
            v = _falloff(n, falloff, exponent) * am
            surf.set_at((x, y), (int(r * v), int(g * v), int(b * v), 255))

    return _store(key, surf)


__all__ = ["glow_sprite", "spotlight_sprite", "dynamic_glow_sprite", "clear_sprite_cache"]
