"""
Blend mode constants for lighting compositing.

Both RGB (alpha-ignoring) and RGBA (alpha-aware) variants are provided,
mirroring pygame's native ``special_flags``. The RGB family is what you
usually want when lighting an opaque scene surface: it operates on the
color channels only and leaves the destination alpha untouched.

Semantics for a scene-surface with a lightmap overlay (values 0..255):
- MULT: ``dst * src / 255`` - darkens, this is the classic 2D light map pass
- ADD:  ``dst + src`` - brightens without clipping until 255
- SUB:  ``dst - src`` - darkens, useful for shadows and negative lights
- MIN:  ``min(dst, src)`` - keep only the darker of the two
- MAX:  ``max(dst, src)`` - keep only the brighter of the two
"""

import pygame

RGB_ADD = pygame.BLEND_RGB_ADD
RGB_SUB = pygame.BLEND_RGB_SUB
RGB_MULT = pygame.BLEND_RGB_MULT
RGB_MIN = pygame.BLEND_RGB_MIN
RGB_MAX = pygame.BLEND_RGB_MAX

RGBA_ADD = pygame.BLEND_RGBA_ADD
RGBA_SUB = pygame.BLEND_RGBA_SUB
RGBA_MULT = pygame.BLEND_RGBA_MULT
RGBA_MIN = pygame.BLEND_RGBA_MIN
RGBA_MAX = pygame.BLEND_RGBA_MAX

LIGHT_ADD = RGB_ADD
SCENE_MULT = RGB_MULT

__all__ = [
    "RGB_ADD",
    "RGB_SUB",
    "RGB_MULT",
    "RGB_MIN",
    "RGB_MAX",
    "RGBA_ADD",
    "RGBA_SUB",
    "RGBA_MULT",
    "RGBA_MIN",
    "RGBA_MAX",
    "LIGHT_ADD",
    "SCENE_MULT",
]
