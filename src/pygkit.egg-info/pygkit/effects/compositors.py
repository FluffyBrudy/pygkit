"""
Compositors for blend mode operations.

Provides semantic wrappers and utilities for combining surfaces with different
blend modes.
"""

import pygame
from pygame import Surface

from pygkit.effects.base import BlendMode


class Compositor:
    """
    Manages a chain of surface compositing operations.
    
    Allows building up complex blend operations by queuing surfaces
    with their blend modes, then executing them all at once.
    """

    __slots__ = ("_operations", "_target_size")

    def __init__(self, target_size: tuple[int, int]) -> None:
        self._operations: list[tuple[Surface, int]] = []
        self._target_size = target_size

    def add(
        self, surface: Surface, blend_mode: int = BlendMode.ADD
    ) -> "Compositor":
        """Add a surface to the composite chain."""
        self._operations.append((surface, blend_mode))
        return self

    def clear(self) -> None:
        """Clear all queued operations."""
        self._operations.clear()

    def render(self) -> Surface:
        """Execute all composite operations and return result."""
        if not self._operations:
            return pygame.Surface(self._target_size, pygame.SRCALPHA)

        result = pygame.Surface(self._target_size, pygame.SRCALPHA)

        for surface, mode in self._operations:
            if surface.get_size() != self._target_size:
                surface = pygame.transform.smoothscale(surface, self._target_size)
            result.blit(surface, (0, 0), special_flags=mode)

        return result

    @property
    def operation_count(self) -> int:
        """Number of queued operations."""
        return len(self._operations)


def blend_add(base: Surface, overlay: Surface) -> Surface:
    """Additive blend - brightens colors."""
    result = base.copy()
    result.blit(overlay, (0, 0), special_flags=BlendMode.ADD)
    return result


def blend_multiply(base: Surface, overlay: Surface) -> Surface:
    """Multiply blend - darkens colors."""
    result = base.copy()
    result.blit(overlay, (0, 0), special_flags=BlendMode.MULT)
    return result


def blend_screen(base: Surface, overlay: Surface) -> Surface:
    """Screen blend - inverse of multiply, lightens colors."""
    # Screen = 1 - (1-a)*(1-b)
    # Approximated using ADD and MULT
    result = base.copy()
    # This is a simplification - true screen requires shader-like ops
    result.blit(overlay, (0, 0), special_flags=BlendMode.MAX)
    return result


def blend_overlay(base: Surface, overlay: Surface, threshold: int = 128) -> Surface:
    """
    Overlay blend - multiply for dark areas, screen for light areas.
    
    Args:
        base: Base surface
        overlay: Overlay surface
        threshold: Cutoff between multiply and screen behavior
    """
    result = base.copy()

    # Simplified overlay using MAX for demonstration
    # True overlay requires per-pixel conditional logic
    result.blit(overlay, (0, 0), special_flags=BlendMode.MAX)

    return result


def alpha_blend(base: Surface, overlay: Surface, alpha: int) -> Surface:
    """
    Simple alpha blend between two surfaces.
    
    Args:
        base: Base surface
        overlay: Overlay surface
        alpha: Alpha value (0-255) for overlay
    """
    result = base.copy()

    # Create temporary surface with adjusted alpha
    temp = overlay.copy()
    temp.set_alpha(alpha)
    result.blit(temp, (0, 0))

    return result


def lerp_blend(
    base: Surface, overlay: Surface, t: float, blend_mode: int = 0
) -> Surface:
    """
    Linear interpolation blend between two surfaces.
    
    Args:
        base: Base surface (t=0)
        overlay: Overlay surface (t=1)
        t: Interpolation factor (0.0 to 1.0)
        blend_mode: Optional blend mode for final composite
    """
    t = max(0.0, min(1.0, t))
    alpha = int(t * 255)

    if blend_mode:
        result = base.copy()
        temp = overlay.copy()
        temp.set_alpha(alpha)
        result.blit(temp, (0, 0), special_flags=blend_mode)
        return result
    else:
        return alpha_blend(base, overlay, alpha)
