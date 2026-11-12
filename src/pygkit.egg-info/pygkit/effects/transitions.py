"""
Transition adapters that bridge effect components with the Transition protocol.

Allows using effect components as scene transitions.
"""

from typing import Any

import pygame
from pygame import Surface

from pygkit.transitions.base import Transition


class EffectTransition(Transition):
    """
    Adapter that wraps effect components to work as transitions.
    
    Takes one or more EffectComponents and runs them as a transition
    between source and target surfaces.
    """

    __slots__ = (
        "_components",
        "_duration",
        "_elapsed",
        "_done",
        "_effect_surface",
        "_blend_mode",
    )

    def __init__(
        self,
        *components: Any,
        blend_mode: int = pygame.BLEND_RGBA_ADD,
    ) -> None:
        """
        Initialize with effect component instances.
        
        Args:
            *components: EffectComponent instances to run during transition
            blend_mode: Blend mode for compositing effect onto screen
        """
        self._components = list(components)
        self._blend_mode = blend_mode
        self._duration = 0.0
        self._elapsed = 0.0
        self._done = False
        self._effect_surface = None

    def start(self, duration: float) -> None:
        self._duration = duration
        self._elapsed = 0.0
        self._done = False

        # Start all components
        for comp in self._components:
            if hasattr(comp, 'start'):
                comp.start(duration)

    def update(self, dt: float) -> None:
        self._elapsed += dt

        # Update all components
        for comp in self._components:
            if hasattr(comp, 'update'):
                comp.update(dt)

        # Check if done
        if self._elapsed >= self._duration:
            self._done = True

    def render(
        self,
        screen: Surface,
        source: Surface | None = None,
        target: Surface | None = None,
    ) -> None:
        # Determine which surface to use as base
        base = source if source is not None else screen
        if base is None:
            return

        # Create effect surface if needed
        if self._effect_surface is None or self._effect_surface.size != base.get_size():
            from pygkit.effects.base import EffectSurface
            self._effect_surface = EffectSurface(base.get_size())

        # Clear effect surface
        self._effect_surface.clear()

        # Calculate progress-based alpha for blending
        progress = min(1.0, self._elapsed / self._duration) if self._duration > 0 else 1.0

        # Render all components
        for comp in self._components:
            if hasattr(comp, 'render'):
                comp.render(self._effect_surface)

        # Composite effect onto screen
        if target is not None and progress > 0:
            # Blend between source and target based on progress
            result = screen.copy()
            result.blit(target, (0, 0))

            # Get effect overlay
            effect = self._effect_surface.render_chain()
            effect.set_alpha(int(255 * progress))

            # Apply effect as mask/overlay
            result.blit(effect, (0, 0), special_flags=self._blend_mode)

            screen.blit(result, (0, 0))
        elif source is not None:
            screen.blit(source, (0, 0))

    @property
    def done(self) -> bool:
        return self._done

    def reset(self) -> None:
        self._duration = 0.0
        self._elapsed = 0.0
        self._done = False
        self._effect_surface = None

        for comp in self._components:
            if hasattr(comp, 'reset'):
                comp.reset()


class ShatterBlastTransition(EffectTransition):
    """
    Pre-configured shatter blast transition.
    
    Combines ShatterMask with Flash for an explosive reveal effect.
    """

    def __init__(self) -> None:
        from pygkit.effects.components import ShatterMask, Flash

        shatter = ShatterMask(cell_size=40, growth_rate=3.0)
        flash = Flash(color=(255, 255, 200), peak_time=0.15)

        super().__init__(shatter, flash, blend_mode=pygame.BLEND_RGBA_ADD)


class NoiseDissolveTransition(EffectTransition):
    """
    Pre-configured noise dissolve transition.
    
    Uses scrolling noise threshold to dissolve between scenes.
    """

    def __init__(self, scale: int = 8, scroll_speed: tuple[float, float] = (20.0, 20.0)) -> None:
        from pygkit.effects.components import NoiseMask

        noise = NoiseMask(scale=scale, scroll_speed=scroll_speed, threshold=0.5)

        super().__init__(noise, blend_mode=pygame.BLEND_RGBA_MULT)


class LightSweepTransition(EffectTransition):
    """
    Pre-configured light sweep transition.
    
    A bright light sweeps across revealing the new scene.
    """

    def __init__(self) -> None:
        from pygkit.effects.components import LightSource, AmbientLight

        light = LightSource(radius=150, intensity=1.5, exponent=0.5)
        ambient = AmbientLight(intensity=0.3)

        super().__init__(light, ambient, blend_mode=pygame.BLEND_RGBA_ADD)

    def start(self, duration: float) -> None:
        super().start(duration)

        # Set initial light position off-screen
        if self._components:
            self._components[0].set_position(-100, -100)

    def update(self, dt: float) -> None:
        super().update(dt)

        # Move light across screen
        if self._components and hasattr(self._components[0], 'set_position'):
            progress = self._elapsed / self._duration if self._duration > 0 else 1.0
            # Diagonal sweep
            x = int(progress * 1000) - 100
            y = int(progress * 800) - 100
            self._components[0].set_position(x, y)
