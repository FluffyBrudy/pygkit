"""
Effect components for color manipulation.

Includes color grading, tinting, and chromatic effects.
"""

import pygame
from pygame import Surface

from pygkit.utils.interpolation import smoothstep
from pygkit.effects.base import BlendMode, EffectComponent, EffectSurface


class ColorTint(EffectComponent):
    """
    Apply a color tint overlay with adjustable intensity.
    
    Useful for mood changes, damage effects, or scene tone shifts.
    """

    __slots__ = ("_color", "_target_intensity")

    def __init__(
        self,
        color: tuple[int, int, int] = (255, 0, 0),
        intensity: float = 0.5,
    ) -> None:
        super().__init__(color=color, intensity=intensity)
        self._color = color
        self._target_intensity = intensity

    def set_intensity(self, intensity: float) -> None:
        """Set target intensity (clamped 0-1)."""
        self._target_intensity = max(0.0, min(1.0, intensity))

    def update(self, dt: float) -> None:
        self._advance_time(dt)

        # Interpolate to target intensity
        current = self.get_param("intensity", 0.0)
        target = self._target_intensity
        t = self.progress

        if t < 1.0:
            new_intensity = current + (target - current) * smoothstep(t)
            self._params["intensity"] = new_intensity

    def render(self, target: EffectSurface) -> None:
        intensity = self.get_param("intensity", 0.5)
        if intensity <= 0:
            return

        r = int(self._color[0] * intensity)
        g = int(self._color[1] * intensity)
        b = int(self._color[2] * intensity)

        overlay = pygame.Surface(target.size, pygame.SRCALPHA)
        overlay.fill((r, g, b, int(255 * intensity)))

        target.composite(overlay, BlendMode.MULT)


class Grayscale(EffectComponent):
    """
    Desaturate the scene to grayscale with adjustable mix.
    
    Can be used for dramatic effects, flashbacks, or as a base for
    other color operations.
    """

    __slots__ = ("_weights",)

    def __init__(
        self,
        intensity: float = 1.0,
        weights: tuple[float, float, float] = (0.299, 0.587, 0.114),
    ) -> None:
        super().__init__(intensity=intensity, weights=weights)
        self._weights = weights  # Standard luminance weights

    def update(self, dt: float) -> None:
        self._advance_time(dt)

    def render(self, target: EffectSurface) -> None:
        intensity = self.get_param("intensity", 1.0)
        if intensity <= 0:
            return

        # Create grayscale conversion overlay
        # Note: True grayscale requires per-pixel operations
        # This is an approximation using blend modes
        overlay = pygame.Surface(target.size, pygame.SRCALPHA)

        # Use average gray as approximation
        gray_val = int(128 * intensity)
        overlay.fill((gray_val, gray_val, gray_val, 128))

        target.composite(overlay, BlendMode.MULT)


class ChromaticAberration(EffectComponent):
    """
    Simulated chromatic aberration effect.
    
    Creates color fringing by offsetting color channels.
    Note: True CA requires shader support; this is an approximation.
    """

    __slots__ = ("_offset", "_direction")

    def __init__(
        self,
        offset: int = 4,
        intensity: float = 1.0,
    ) -> None:
        super().__init__(offset=offset, intensity=intensity)
        self._offset = offset
        self._direction = 1  # Horizontal offset direction

    def update(self, dt: float) -> None:
        self._advance_time(dt)

    def render(self, target: EffectSurface) -> None:
        intensity = self.get_param("intensity", 1.0)
        if intensity <= 0:
            return

        offset = int(self._offset * intensity * self.progress)
        if offset <= 0:
            return

        # Create red/cyan shift approximation
        tw, th = target.size

        # Red channel shift
        red_shift = pygame.Surface((tw + offset, th), pygame.SRCALPHA)
        red_shift.fill((min(255, int(255 * self.progress)), 0, 0, 50))

        # Cyan channel shift (opposite direction)
        cyan_shift = pygame.Surface((tw + offset, th), pygame.SRCALPHA)
        cyan_shift.fill((0, min(255, int(255 * self.progress)), min(255, int(255 * self.progress)), 50))

        target.composite(red_shift, BlendMode.ADD)
        # In full implementation, would offset cyan in opposite direction


class Vignette(EffectComponent):
    """
    Darken edges of the screen for focus or mood.
    
    Classic vignette effect with adjustable darkness and roundness.
    """

    __slots__ = ("_darkness", "_roundness")

    def __init__(
        self,
        darkness: float = 0.6,
        roundness: float = 1.0,
        intensity: float = 1.0,
    ) -> None:
        super().__init__(darkness=darkness, roundness=roundness, intensity=intensity)
        self._darkness = darkness
        self._roundness = roundness

    def update(self, dt: float) -> None:
        self._advance_time(dt)

    def render(self, target: EffectSurface) -> None:
        intensity = self.get_param("intensity", 1.0) * self.progress
        if intensity <= 0:
            return

        darkness = self._darkness * intensity
        roundness = self._roundness

        # Create vignette mask
        size = max(target.width, target.height)
        center = size // 2

        # Generate radial gradient for vignette
        from pygkit.effects.generators import radial_gradient

        vignette = radial_gradient(
            size=size,
            center=(center, center),
            inner_color=(0, 0, 0, 0),
            outer_color=(0, 0, 0, int(255 * darkness)),
            exponent=roundness,
        )

        # Scale to target size
        vignette = pygame.transform.smoothscale(vignette, target.size)

        target.composite(vignette, BlendMode.ADD)


class ColorShift(EffectComponent):
    """
    Shift colors through hue rotation over time.
    
    Creates a rainbow-like cycling effect.
    """

    __slots__ = ("_speed", "_phase")

    def __init__(
        self,
        speed: float = 1.0,
        intensity: float = 0.5,
    ) -> None:
        super().__init__(speed=speed, intensity=intensity)
        self._speed = speed
        self._phase = 0.0

    def update(self, dt: float) -> None:
        self._advance_time(dt)

        # Advance phase based on speed
        self._phase += self._speed * dt

    def render(self, target: EffectSurface) -> None:
        intensity = self.get_param("intensity", 0.5)
        if intensity <= 0:
            return

        # Create color shift overlay based on phase
        import math

        r = int(128 + 127 * math.sin(self._phase) * intensity)
        g = int(128 + 127 * math.sin(self._phase + 2.094) * intensity)  # +120 degrees
        b = int(128 + 127 * math.sin(self._phase + 4.188) * intensity)  # +240 degrees

        overlay = pygame.Surface(target.size, pygame.SRCALPHA)
        overlay.fill((r, g, b, int(128 * intensity)))

        target.composite(overlay, BlendMode.MULT)
