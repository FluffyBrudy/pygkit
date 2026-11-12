"""
Core effect system classes - EffectSurface with caching and EffectComponent base.
"""

import hashlib
import math
from abc import ABC, abstractmethod
from functools import wraps
from typing import Any, Callable, Protocol

import pygame
from pygame import Surface


class BlendMode:
    """Semantic blend mode constants for compositing."""

    ADD = pygame.BLEND_RGBA_ADD
    SUB = pygame.BLEND_RGBA_SUB
    MULT = pygame.BLEND_RGBA_MULT
    MIN = pygame.BLEND_RGBA_MIN
    MAX = pygame.BLEND_RGBA_MAX


def _hash_params(**kwargs) -> str:
    """Create a hash from parameters for cache key generation."""
    param_str = str(sorted(kwargs.items()))
    return hashlib.md5(param_str.encode(), usedforsecurity=False).hexdigest()[:12]


def cached_generator(func: Callable[..., Surface]) -> Callable[..., Surface]:
    """
    Decorator to cache generator function results based on parameters.
    
    Useful for expensive operations like pixel-by-pixel texture generation.
    Cache is keyed by function name and parameter values with LRU eviction.
    """
    cache: dict[str, Surface] = {}
    cache_order: list[str] = []
    max_size = 128

    @wraps(func)
    def wrapper(*args, **kwargs) -> Surface:
        # Build structured cache key with clear boundaries
        key_parts = [func.__name__]
        for arg in args:
            key_parts.append(f":{arg!s}")
        for k, v in sorted(kwargs.items()):
            key_parts.append(f";{k}={v!s}")
        key = "".join(key_parts)

        if key in cache:
            # Move to end (most recently used)
            cache_order.remove(key)
            cache_order.append(key)
            return cache[key].copy()
        
        # Evict oldest if at capacity
        if len(cache) >= max_size:
            oldest = cache_order.pop(0)
            del cache[oldest]
        
        cache[key] = func(*args, **kwargs)
        cache_order.append(key)
        return cache[key].copy()

    wrapper.cache_clear = lambda: (cache.clear(), cache_order.clear())  # type: ignore
    wrapper.cache_info = lambda: len(cache)  # type: ignore
    return wrapper


class EffectSurface:
    """
    Surface wrapper with automatic caching, resolution independence, and blend chaining.
    
    Provides a clean interface for effect rendering with built-in optimization
    through surface caching at multiple resolutions.
    """

    __slots__ = ("_surfaces", "_base_size", "_current_size", "_blend_modes")

    def __init__(self, base_size: tuple[int, int]) -> None:
        self._base_size = base_size
        self._current_size = base_size
        self._surfaces: dict[tuple[int, int], Surface] = {}
        self._blend_modes: list[tuple[Surface, int]] = []

        # Create base surface
        self._surfaces[base_size] = pygame.Surface(base_size, pygame.SRCALPHA)

    def _get_surface(self, size: tuple[int, int]) -> Surface:
        """Get or create a surface at the specified size."""
        if size not in self._surfaces:
            self._surfaces[size] = pygame.Surface(size, pygame.SRCALPHA)
        return self._surfaces[size]

    def clear(self, color: tuple[int, int, int, int] = (0, 0, 0, 0)) -> None:
        """Clear all surfaces with optional color."""
        for surf in self._surfaces.values():
            surf.fill(color)
        self._blend_modes.clear()

    def blit(
        self,
        source: Surface,
        dest: tuple[float, float] = (0, 0),
        area: pygame.Rect | None = None,
        blend_flags: int = 0,
    ) -> None:
        """Blit a source surface with optional blending."""
        base_surf = self._surfaces[self._current_size]
        base_surf.blit(source, dest, area, blend_flags)

    def composite(
        self, source: Surface, blend_mode: int = BlendMode.ADD
    ) -> "EffectSurface":
        """Add a surface to the blend chain with specified mode."""
        self._blend_modes.append((source, blend_mode))
        return self

    def render_chain(self) -> Surface:
        """Execute the blend chain and return the result."""
        if not self._blend_modes:
            return self._surfaces[self._current_size].copy()

        result = self._surfaces[self._current_size].copy()
        for source, mode in self._blend_modes:
            # Scale source if needed
            if source.get_size() != result.get_size():
                source = pygame.transform.smoothscale(source, result.get_size())
            result.blit(source, (0, 0), special_flags=mode)

        return result

    def get_surface(self) -> Surface:
        """Get the current size surface for direct manipulation."""
        return self._surfaces[self._current_size]

    def set_size(self, new_size: tuple[int, int]) -> None:
        """Change the working size (for resolution scaling)."""
        if new_size not in self._surfaces:
            old_surf = self._surfaces[self._base_size]
            new_surf = pygame.transform.smoothscale(old_surf, new_size)
            self._surfaces[new_size] = new_surf
        self._current_size = new_size

    @property
    def size(self) -> tuple[int, int]:
        return self._current_size

    @property
    def width(self) -> int:
        return self._current_size[0]

    @property
    def height(self) -> int:
        return self._current_size[1]


class EffectComponent(ABC):
    """
    Base class for stateful effect components.
    
    Components are the building blocks of effects - they maintain state,
    accept parameters, and provide update/render methods. They can be
    composed together to create complex effects.
    """

    __slots__ = ("_params", "_time", "_duration", "_done")

    def __init__(self, **params: Any) -> None:
        self._params = params
        self._time = 0.0
        self._duration = 0.0
        self._done = False

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update component state based on delta time."""
        pass

    @abstractmethod
    def render(self, target: EffectSurface) -> None:
        """Render the component effect to the target surface."""
        pass

    def start(self, duration: float) -> None:
        """Start the effect with given duration."""
        self._time = 0.0
        self._duration = duration
        self._done = False

    def reset(self) -> None:
        """Reset the component to initial state."""
        self._time = 0.0
        self._duration = 0.0
        self._done = False

    @property
    def done(self) -> bool:
        """Check if the effect has completed."""
        return self._done

    @property
    def progress(self) -> float:
        """Get normalized progress (0.0 to 1.0)."""
        if self._duration <= 0:
            return 1.0
        return min(1.0, self._time / self._duration)

    def _advance_time(self, dt: float) -> None:
        """Internal method to advance time and check completion."""
        self._time += dt
        if self._time >= self._duration:
            self._time = self._duration
            self._done = True

    def get_param(self, name: str, default: Any = None) -> Any:
        """Get a parameter value with optional default."""
        return self._params.get(name, default)
