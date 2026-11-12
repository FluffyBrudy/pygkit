"""
Effect components for lighting effects.

Includes light sources, glow effects, and ambient lighting components.
"""

import math
from typing import Any

import pygame
from pygame import Surface

from pygkit.utils.interpolation import smoothstep
from pygkit.effects.base import BlendMode, EffectComponent, EffectSurface
from pygkit.effects.generators import radial_gradient


class LightSource(EffectComponent):
    """
    Radial light source with configurable intensity and falloff.
    
    Can be used for dynamic lighting, spotlights, or as a mask for transitions.
    """

    __slots__ = (
        "_position",
        "_gradient_cache",
        "_last_params",
    )

    def __init__(
        self,
        radius: int = 100,
        intensity: float = 1.0,
        color: tuple[int, int, int] = (255, 255, 255),
        exponent: float = 1.0,
    ) -> None:
        super().__init__(
            radius=radius,
            intensity=intensity,
            color=color,
            exponent=exponent,
        )
        self._position = (0.0, 0.0)
        self._gradient_cache: Surface | None = None
        self._last_params: dict[str, Any] = {}

    def set_position(self, x: float, y: float) -> None:
        """Set light source position."""
        self._position = (x, y)

    def _get_gradient(self, size: int) -> Surface:
        """Get or create cached gradient texture."""
        params = {
            "size": size,
            "radius": self.get_param("radius", 100),
            "color": self.get_param("color", (255, 255, 255)),
            "exponent": self.get_param("exponent", 1.0),
        }

        # Check if we need to regenerate
        if self._gradient_cache is None or params != self._last_params:
            radius = params["radius"]
            color = params["color"]
            exponent = params["exponent"]

            inner_color = (*color, 255)
            outer_color = (0, 0, 0, 0)

            self._gradient_cache = radial_gradient(
                size=size * 2,
                center=(size, size),
                inner_color=inner_color,
                outer_color=outer_color,
                exponent=exponent,
            )
            self._last_params = params.copy()

        return self._gradient_cache

    def update(self, dt: float) -> None:
        self._advance_time(dt)

    def render(self, target: EffectSurface) -> None:
        intensity = self.get_param("intensity", 1.0)
        if self.progress < 1.0:
            intensity *= smoothstep(self.progress)

        radius = self.get_param("radius", 100)
        gradient = self._get_gradient(radius)

        # Scale gradient by intensity
        scaled_gradient = gradient.copy()
        alpha = int(255 * intensity)
        scaled_gradient.set_alpha(alpha)

        # Calculate position on target surface
        px, py = self._position
        
        # Create a full-size transparent layer for proper positioning
        tw, th = target.size
        light_layer = pygame.Surface((tw, th), pygame.SRCALPHA)
        
        # Blit gradient at offset position
        offset_x = px - radius
        offset_y = py - radius
        light_layer.blit(scaled_gradient, (offset_x, offset_y))
        
        # Composite the layer with additive blending
        target.composite(light_layer, BlendMode.ADD)


class AmbientLight(EffectComponent):
    """
    Uniform ambient lighting across the entire surface.
    
    Useful for base illumination levels or fade effects.
    """

    __slots__ = ("_color", "_target_intensity")

    def __init__(
        self,
        intensity: float = 0.0,
        color: tuple[int, int, int] = (255, 255, 255),
    ) -> None:
        super().__init__(intensity=intensity, color=color)
        self._color = color
        self._target_intensity = intensity

    def set_intensity(self, intensity: float) -> None:
        """Set target intensity (clamped 0-1)."""
        self._target_intensity = max(0.0, min(1.0, intensity))

    def update(self, dt: float) -> None:
        self._advance_time(dt)

        # Smoothly interpolate intensity if animating
        current = self.get_param("intensity", 0.0)
        target = self._target_intensity
        t = self.progress

        if t < 1.0:
            new_intensity = current + (target - current) * smoothstep(t)
            self._params["intensity"] = new_intensity

    def render(self, target: EffectSurface) -> None:
        intensity = self.get_param("intensity", 0.0)
        if intensity <= 0:
            return

        color = self._color
        r = int(color[0] * intensity)
        g = int(color[1] * intensity)
        b = int(color[2] * intensity)

        # Create ambient overlay
        ambient = pygame.Surface(target.size, pygame.SRCALPHA)
        ambient.fill((r, g, b, 255))

        target.composite(ambient, BlendMode.ADD)


class GlowPulse(EffectComponent):
    """
    Pulsing glow effect with configurable frequency and amplitude.
    
    Can be layered on top of LightSource for dynamic effects.
    """

    __slots__ = ("_phase",)

    def __init__(
        self,
        frequency: float = 2.0,
        amplitude: float = 0.3,
        base_intensity: float = 0.7,
    ) -> None:
        super().__init__(
            frequency=frequency,
            amplitude=amplitude,
            base_intensity=base_intensity,
        )
        self._phase = 0.0

    def update(self, dt: float) -> None:
        self._advance_time(dt)

        # Update phase based on frequency
        freq = self.get_param("frequency", 2.0)
        self._phase += dt * freq * math.pi * 2

        # Calculate pulsed intensity
        amp = self.get_param("amplitude", 0.3)
        base = self.get_param("base_intensity", 0.7)

        pulse = math.sin(self._phase) * amp + base
        pulse = max(0.0, min(1.0, pulse))

        self._params["current_intensity"] = pulse

    def render(self, target: EffectSurface) -> None:
        intensity = self._params.get("current_intensity", 0.7)

        # Render as semi-transparent overlay
        overlay = pygame.Surface(target.size, pygame.SRCALPHA)
        alpha = int(intensity * 255)
        overlay.fill((alpha, alpha, alpha, alpha))

        target.composite(overlay, BlendMode.ADD)


class Flash(EffectComponent):
    """
    Quick flash effect that peaks and fades.
    
    Useful for explosions, impacts, or transition accents.
    """

    __slots__ = ("_color", "_peak_time")

    def __init__(
        self,
        color: tuple[int, int, int] = (255, 255, 255),
        peak_time: float = 0.1,
    ) -> None:
        super().__init__(color=color, peak_time=peak_time)
        self._color = color
        self._peak_time = peak_time

    def update(self, dt: float) -> None:
        self._advance_time(dt)

    def render(self, target: EffectSurface) -> None:
        color = self._color
        t = self.progress
        peak_t = self._peak_time / self._duration if self._duration > 0 else 0.5

        # Rise quickly to peak, then fade
        if t < peak_t:
            intensity = t / peak_t
        else:
            remaining = 1.0 - peak_t
            if remaining > 0:
                intensity = 1.0 - (t - peak_t) / remaining
            else:
                intensity = 0.0

        intensity = max(0.0, min(1.0, intensity))

        if intensity <= 0:
            return

        r = int(color[0] * intensity)
        g = int(color[1] * intensity)
        b = int(color[2] * intensity)

        overlay = pygame.Surface(target.size, pygame.SRCALPHA)
        overlay.fill((r, g, b, int(255 * intensity)))

        target.composite(overlay, BlendMode.ADD)
