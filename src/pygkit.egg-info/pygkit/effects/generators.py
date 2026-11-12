"""
Generator functions for creating textures and patterns.

All generators are pure functions that can be decorated with @cached_generator
for automatic caching of expensive operations.
"""

import math
import random
from typing import Callable

import pygame
from pygame import Surface

from pygkit.effects.base import BlendMode, cached_generator


@cached_generator
def radial_gradient(
    size: int,
    center: tuple[int, int] | None = None,
    inner_color: tuple[int, int, int, int] = (255, 255, 255, 255),
    outer_color: tuple[int, int, int, int] = (0, 0, 0, 0),
    exponent: float = 1.0,
) -> Surface:
    """
    Generate a radial gradient texture.
    
    Args:
        size: Diameter of the gradient circle
        center: Center point (defaults to image center)
        inner_color: Color at center
        outer_color: Color at edge
        exponent: Controls falloff (1=linear, >1=sharper, <1=softer)
    
    Returns:
        Surface with radial gradient
    """
    if center is None:
        center = (size // 2, size // 2)

    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = center
    radius = size / 2

    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            if dist >= radius:
                continue

            t = dist / radius
            t = pow(t, exponent)  # Apply exponent for falloff control

            r = int(inner_color[0] * (1 - t) + outer_color[0] * t)
            g = int(inner_color[1] * (1 - t) + outer_color[1] * t)
            b = int(inner_color[2] * (1 - t) + outer_color[2] * t)
            a = int(inner_color[3] * (1 - t) + outer_color[3] * t)

            surface.set_at((x, y), (r, g, b, a))

    return surface


@cached_generator
def linear_gradient(
    width: int,
    height: int,
    start_color: tuple[int, int, int, int],
    end_color: tuple[int, int, int, int],
    angle: float = 0.0,
) -> Surface:
    """
    Generate a linear gradient texture.
    
    Args:
        width: Width of gradient surface
        height: Height of gradient surface
        start_color: Color at start of gradient
        end_color: Color at end of gradient
        angle: Angle in radians (0=left to right)
    
    Returns:
        Surface with linear gradient
    """
    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    # Calculate gradient direction
    dir_x = math.cos(angle)
    dir_y = math.sin(angle)

    # Find max distance for normalization
    max_dist = abs(width * dir_x) + abs(height * dir_y)
    if max_dist == 0:
        max_dist = 1

    for y in range(height):
        for x in range(width):
            # Project position onto gradient direction
            dist = x * dir_x + y * dir_y
            t = (dist + max_dist) / (2 * max_dist)
            t = max(0, min(1, t))

            r = int(start_color[0] * (1 - t) + end_color[0] * t)
            g = int(start_color[1] * (1 - t) + end_color[1] * t)
            b = int(start_color[2] * (1 - t) + end_color[2] * t)
            a = int(start_color[3] * (1 - t) + end_color[3] * t)

            surface.set_at((x, y), (r, g, b, a))

    return surface


@cached_generator
def noise_texture(
    width: int,
    height: int,
    scale: int = 1,
    seed: int | None = None,
    threshold: float | None = None,
) -> Surface:
    """
    Generate a noise texture.
    
    Args:
        width: Width of noise surface
        height: Height of noise surface
        scale: Pixel scale (1=full resolution, 2=half, etc.)
        seed: Random seed for reproducibility
        threshold: If set, binarize noise (values < threshold become black)
    
    Returns:
        Surface with noise pattern
    """
    # Use local RNG to avoid modifying global state
    rng = random.Random(seed) if seed is not None else random
    
    scaled_w = width // scale
    scaled_h = height // scale

    # Generate at lower resolution if scaled
    surface = pygame.Surface((scaled_w, scaled_h), pygame.SRCALPHA)

    for y in range(scaled_h):
        for x in range(scaled_w):
            v = rng.randint(0, 255)

            if threshold is not None:
                v = 255 if v / 255.0 >= threshold else 0

            surface.set_at((x, y), (v, v, v, 255))

    # Scale up if needed
    if scale > 1:
        surface = pygame.transform.scale(surface, (width, height))

    return surface


@cached_generator
def checker_pattern(
    size: int,
    tile_size: int = 16,
    color1: tuple[int, int, int, int] = (255, 255, 255, 255),
    color2: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Surface:
    """
    Generate a checkerboard pattern.
    
    Args:
        size: Size of square pattern surface
        tile_size: Size of each checker tile
        color1: First color
        color2: Second color
    
    Returns:
        Surface with checkerboard pattern
    """
    surface = pygame.Surface((size, size), pygame.SRCALPHA)

    for y in range(size):
        for x in range(size):
            tile_x = x // tile_size
            tile_y = y // tile_size

            if (tile_x + tile_y) % 2 == 0:
                surface.set_at((x, y), color1)
            else:
                surface.set_at((x, y), color2)

    return surface


@cached_generator
def distance_field_circle(
    size: int,
    center: tuple[int, int] | None = None,
    radius: int | None = None,
    inside_value: int = 255,
    outside_value: int = 0,
) -> Surface:
    """
    Generate a signed distance field for a circle.
    
    Args:
        size: Size of square surface
        center: Circle center (defaults to image center)
        radius: Circle radius (defaults to size/2)
        inside_value: Value for points inside circle
        outside_value: Value for points outside circle
    
    Returns:
        Grayscale surface representing distance field
    """
    if center is None:
        center = (size // 2, size // 2)
    if radius is None:
        radius = size // 2

    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = center

    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)

            # Signed distance: negative inside, positive outside
            signed_dist = dist - radius

            # Map to 0-255 range (clamp at ±127 from center)
            value = int(127 - signed_dist)
            value = max(0, min(255, value))

            surface.set_at((x, y), (value, value, value, 255))

    return surface


@cached_generator
def distance_field_rect(
    width: int,
    height: int,
    rect: pygame.Rect | None = None,
    inside_value: int = 255,
    outside_value: int = 0,
) -> Surface:
    """
    Generate a signed distance field for a rectangle.
    
    Args:
        width: Surface width
        height: Surface height
        rect: Rectangle definition (defaults to full surface)
        inside_value: Value for points inside rectangle
        outside_value: Value for points outside rectangle
    
    Returns:
        Grayscale surface representing distance field
    """
    if rect is None:
        rect = pygame.Rect(0, 0, width, height)

    surface = pygame.Surface((width, height), pygame.SRCALPHA)

    for y in range(height):
        for x in range(width):
            # Find closest point on rect
            closest_x = max(rect.left, min(x, rect.right - 1))
            closest_y = max(rect.top, min(y, rect.bottom - 1))

            dx = x - closest_x
            dy = y - closest_y
            dist = math.sqrt(dx * dx + dy * dy)

            # Determine if inside or outside
            inside = rect.collidepoint(x, y)

            if inside:
                value = int(127 + dist)
            else:
                value = int(127 - dist)

            value = max(0, min(255, value))
            surface.set_at((x, y), (value, value, value, 255))

    return surface


def composite(
    sources: list[tuple[Surface, int]],
    target_size: tuple[int, int],
) -> Surface:
    """
    Composite multiple surfaces with blend modes.
    
    Args:
        sources: List of (surface, blend_mode) tuples
        target_size: Size of output surface
    
    Returns:
        Composited surface
    """
    if not sources:
        return pygame.Surface(target_size, pygame.SRCALPHA)

    result = pygame.Surface(target_size, pygame.SRCALPHA)

    for source, mode in sources:
        if source.get_size() != target_size:
            source = pygame.transform.smoothscale(source, target_size)
        result.blit(source, (0, 0), special_flags=mode)

    return result
