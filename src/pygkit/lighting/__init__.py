"""
pygkit lighting - generic 2D lighting for games.

A light map pipeline (ambient darkness + additive light sprites + multiply
the scene) with game-agnostic lights. Straight imports, no game wiring::

    from pygkit.lighting import LightMap, PointLight, Spotlight, RGBA_MULT

    lightmap = LightMap((800, 600), scale=0.5)
    lightmap.set_ambient((20, 25, 40), 0.15)

    torch = PointLight(radius=140, color=(255, 190, 120))
    torch.set_flicker(frequency=8.0, amplitude=0.2)

    while running:
        lightmap.clear()
        torch.render(lightmap, torch_x, torch_y)
        lightmap.apply(scene, blend=RGBA_MULT)
"""

from pygkit.lighting.blend import (
    LIGHT_ADD,
    RGB_ADD,
    RGB_MAX,
    RGB_MIN,
    RGB_MULT,
    RGB_SUB,
    RGBA_ADD,
    RGBA_MAX,
    RGBA_MIN,
    RGBA_MULT,
    RGBA_SUB,
    SCENE_MULT,
)
from pygkit.lighting.lightmap import LightMap
from pygkit.lighting.lights import DynamicLight, PointLight, Spotlight
from pygkit.lighting.sprites import (
    clear_sprite_cache,
    dynamic_glow_sprite,
    glow_sprite,
    spotlight_sprite,
)

__all__ = [
    "LightMap",
    "PointLight",
    "Spotlight",
    "DynamicLight",
    "glow_sprite",
    "spotlight_sprite",
    "dynamic_glow_sprite",
    "clear_sprite_cache",
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
