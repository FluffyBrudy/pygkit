"""
Effect components for distortion and mask-based effects.

Includes noise masks, displacement effects, and threshold operations.
"""

import math
import random
from typing import Any

import pygame
from pygame import Surface

from pygkit.utils.interpolation import smoothstep
from pygkit.effects.base import BlendMode, EffectComponent, EffectSurface
from pygkit.effects.generators import noise_texture


class NoiseMask(EffectComponent):
    """
    Animated noise mask that can be used for reveals or distortions.
    
    The noise pattern scrolls over time and can be thresholded to create
    binary masks for transitions.
    """

    __slots__ = (
        "_scroll_x",
        "_scroll_y",
        "_seed",
        "_scale",
        "_threshold",
        "_noise_cache",
    )

    def __init__(
        self,
        scale: int = 4,
        seed: int | None = None,
        scroll_speed: tuple[float, float] = (10.0, 10.0),
        threshold: float = 0.5,
    ) -> None:
        super().__init__(
            scale=scale,
            seed=seed,
            scroll_speed=scroll_speed,
            threshold=threshold,
        )
        self._scroll_x = 0.0
        self._scroll_y = 0.0
        self._seed = seed if seed is not None else random.randint(0, 2**31)
        self._scale = scale
        self._threshold = threshold
        self._noise_cache: Surface | None = None

    def _generate_noise(self, width: int, height: int) -> Surface:
        """Generate or retrieve cached noise texture."""
        if self._noise_cache is None:
            self._noise_cache = noise_texture(
                width=width * 2,
                height=height * 2,
                scale=self._scale,
                seed=self._seed,
            )
        return self._noise_cache

    def update(self, dt: float) -> None:
        self._advance_time(dt)

        # Scroll noise based on speed
        speed = self.get_param("scroll_speed", (10.0, 10.0))
        self._scroll_x += speed[0] * dt
        self._scroll_y += speed[1] * dt

    def render(self, target: EffectSurface) -> None:
        tw, th = target.width, target.height

        # Get noise texture
        noise = self._generate_noise(tw, th)

        # Create offset for scrolling effect
        offset_x = int(self._scroll_x) % (noise.get_width() // 2)
        offset_y = int(self._scroll_y) % (noise.get_height() // 2)

        # Extract region from noise
        crop_rect = pygame.Rect(offset_x, offset_y, tw, th)
        cropped = noise.subsurface(crop_rect).copy()

        # Apply threshold if specified
        threshold = self.get_param("threshold", 0.5)
        if threshold is not None and 0 < threshold < 1:
            # Convert to binary mask
            thresh_val = int(threshold * 255)
            for y in range(cropped.get_height()):
                for x in range(cropped.get_width()):
                    pixel = cropped.get_at((x, y))
                    val = 255 if pixel.r >= thresh_val else 0
                    cropped.set_at((x, y), (val, val, val, 255))

        # Use as mask - blend with ADD to reveal
        target.composite(cropped, BlendMode.ADD)

    def reset(self) -> None:
        super().reset()
        self._scroll_x = 0.0
        self._scroll_y = 0.0


class ShatterMask(EffectComponent):
    """
    Shatter effect using Voronoi-like cell patterns.
    
    Creates a fragmentation effect suitable for transition reveals or
    destruction effects.
    """

    __slots__ = ("_cells", "_cell_size", "_growth_rate")

    def __init__(
        self,
        cell_size: int = 32,
        growth_rate: float = 2.0,
        seed: int | None = None,
    ) -> None:
        super().__init__(
            cell_size=cell_size,
            growth_rate=growth_rate,
            seed=seed,
        )
        self._cells: list[tuple[int, int, float]] = []  # (x, y, start_time)
        self._cell_size = cell_size
        self._growth_rate = growth_rate

    def _generate_cells(self, width: int, height: int) -> None:
        """Generate random cell centers."""
        self._cells.clear()

        cols = max(1, width // self._cell_size)
        rows = max(1, height // self._cell_size)

        seed = self.get_param("seed")
        # Use local RNG to avoid modifying global state
        rng = random.Random(seed) if seed is not None else random

        for row in range(rows):
            for col in range(cols):
                # Add some randomness to cell positions
                cx = col * self._cell_size + rng.randint(0, self._cell_size)
                cy = row * self._cell_size + rng.randint(0, self._cell_size)
                start_t = rng.uniform(0, 0.3)  # Stagger start times
                self._cells.append((cx, cy, start_t))

    def update(self, dt: float) -> None:
        self._advance_time(dt)

    def render(self, target: EffectSurface) -> None:
        if not self._cells:
            self._generate_cells(target.width, target.height)

        # Create shatter mask
        mask = pygame.Surface(target.size, pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))

        growth_rate = self.get_param("growth_rate", 2.0)
        progress = self.progress

        for cx, cy, start_t in self._cells:
            # Calculate cell radius based on progress and staggered start
            effective_t = max(0, progress - start_t)
            radius = effective_t * growth_rate * self._cell_size

            if radius <= 0:
                continue

            # Draw cell fragment
            color_val = min(255, int(effective_t * 255))
            pygame.draw.circle(mask, (color_val, color_val, color_val, 255), (cx, cy), int(radius))

        target.composite(mask, BlendMode.ADD)

    def reset(self) -> None:
        super().reset()
        self._cells.clear()


class ThresholdReveal(EffectComponent):
    """
    Reveal effect using a moving threshold line/plane.
    
    Can sweep horizontally, vertically, or radially to reveal content.
    """

    __slots__ = ("_direction", "_start_pos", "_end_pos")

    DIRECTION_LEFT = "left"
    DIRECTION_RIGHT = "right"
    DIRECTION_TOP = "top"
    DIRECTION_BOTTOM = "bottom"
    DIRECTION_CENTER = "center"

    def __init__(
        self,
        direction: str = DIRECTION_LEFT,
        softness: float = 0.1,
    ) -> None:
        super().__init__(direction=direction, softness=softness)
        self._direction = direction
        self._start_pos = 0.0
        self._end_pos = 1.0

    def update(self, dt: float) -> None:
        self._advance_time(dt)

    def render(self, target: EffectSurface) -> None:
        progress = smoothstep(self.progress)
        softness = self.get_param("softness", 0.1)

        mask = pygame.Surface(target.size, pygame.SRCALPHA)

        if self._direction == self.DIRECTION_LEFT:
            reveal_x = int(progress * target.width)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, reveal_x, target.height))
        elif self._direction == self.DIRECTION_RIGHT:
            reveal_x = int((1 - progress) * target.width)
            pygame.draw.rect(mask, (255, 255, 255, 255), (reveal_x, 0, target.width - reveal_x, target.height))
        elif self._direction == self.DIRECTION_TOP:
            reveal_y = int(progress * target.height)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, target.width, reveal_y))
        elif self._direction == self.DIRECTION_BOTTOM:
            reveal_y = int((1 - progress) * target.height)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, reveal_y, target.width, target.height - reveal_y))
        elif self._direction == self.DIRECTION_CENTER:
            reveal_radius = int(progress * max(target.width, target.height) / 2)
            center = (target.width // 2, target.height // 2)
            pygame.draw.circle(mask, (255, 255, 255, 255), center, reveal_radius)

        target.composite(mask, BlendMode.MULT)


class DisplacementMap(EffectComponent):
    """
    Simulated displacement effect using offset layers.
    
    Note: True displacement requires shader support. This creates an
    approximation by rendering offset copies with reduced alpha.
    """

    __slots__ = ("_amplitude", "_offsets")

    def __init__(
        self,
        amplitude: int = 8,
        samples: int = 4,
    ) -> None:
        super().__init__(amplitude=amplitude, samples=samples)
        self._amplitude = amplitude
        self._offsets: list[tuple[int, int]] = []

    def _generate_offsets(self, samples: int) -> None:
        """Generate random offset vectors."""
        self._offsets.clear()
        amp = self._amplitude

        for i in range(samples):
            angle = (i / samples) * math.pi * 2
            ox = int(math.cos(angle) * amp * 0.5)
            oy = int(math.sin(angle) * amp * 0.5)
            self._offsets.append((ox, oy))

    def update(self, dt: float) -> None:
        self._advance_time(dt)

    def render(self, target: EffectSurface) -> None:
        samples = self.get_param("samples", 4)
        if not self._offsets:
            self._generate_offsets(samples)

        # Create displacement overlay
        progress = smoothstep(self.progress)
        alpha = int(progress * 64)  # Max alpha for displacement

        for ox, oy in self._offsets:
            # In actual use, this would sample from a source surface
            # Here we create a visual representation of the effect
            overlay = pygame.Surface(target.size, pygame.SRCALPHA)
            overlay.fill((alpha, alpha, alpha, alpha // 2))
            target.composite(overlay, BlendMode.ADD)
