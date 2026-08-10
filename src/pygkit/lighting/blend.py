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

# RGB variants (alpha channel of the source is ignored)
RGB_ADD = pygame.BLEND_RGB_ADD
RGB_SUB = pygame.BLEND_RGB_SUB
RGB_MULT = pygame.BLEND_RGB_MULT
RGB_MIN = pygame.BLEND_RGB_MIN
RGB_MAX = pygame.BLEND_RGB_MAX

# RGBA variants (alpha channel of the source is taken into account)
RGBA_ADD = pygame.BLEND_RGBA_ADD
RGBA_SUB = pygame.BLEND_RGBA_SUB
RGBA_MULT = pygame.BLEND_RGBA_MULT
RGBA_MIN = pygame.BLEND_RGBA_MIN
RGBA_MAX = pygame.BLEND_RGBA_MAX

# Sensible defaults for the two common jobs. The RGB family is what the
# module docstring recommends for lighting opaque scene surfaces (color
# channels only, destination alpha untouched), so these are the RGB
# variants - the light map pipeline keeps its alpha channel at 255 anyway.
LIGHT_ADD = RGB_ADD  # adding a light sprite onto the light map
SCENE_MULT = RGB_MULT  # multiplying the scene by the light map

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
