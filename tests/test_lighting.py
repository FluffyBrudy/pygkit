"""Tests for pygkit.lighting - light map pipeline and lights."""

import math
import time

import pygame

from pygkit.lighting import (
    DynamicLight,
    LightMap,
    PointLight,
    Spotlight,
    clear_sprite_cache,
    dynamic_glow_sprite,
    glow_sprite,
    spotlight_sprite,
)
from pygkit.lighting.blend import (
    RGB_ADD,
    RGB_MAX,
    RGB_SUB,
    RGBA_MULT,
)


def _solid(size, color):
    surf = pygame.Surface(size)
    surf.fill(color)
    return surf


# ---------------------------------------------------------------- sprites


def test_glow_sprite_center_brighter_than_edge():
    sprite = glow_sprite(radius=32)
    w = sprite.get_width()
    center = sprite.get_at((w // 2, w // 2))
    edge = sprite.get_at((w - 2, w // 2))
    assert center.r > 200
    assert edge.r < 50


def test_glow_sprite_shared_cache_and_clear():
    a = glow_sprite(radius=16)
    b = glow_sprite(radius=16)
    assert a is b
    clear_sprite_cache()
    c = glow_sprite(radius=16)
    assert c is not a


def test_spotlight_sprite_is_cone_shaped():
    sprite = spotlight_sprite(radius=64, cone=0.5, softness=0.1)
    w = sprite.get_width()
    cx = cy = w // 2
    # inside the cone, right of center: bright
    inside = sprite.get_at((cx + 30, cy))
    # far outside the cone, straight above center: dark
    outside = sprite.get_at((cx, cy - 30))
    assert inside.r > outside.r + 100


# --------------------------------------------------------------- lightmap


def test_ambient_mult_darkens_scene():
    scene = _solid((100, 100), (200, 200, 200))
    lm = LightMap((100, 100), scale=0.5)
    lm.set_ambient((255, 255, 255), 0.5)  # half-brightness ambient
    lm.clear()
    lm.apply(scene, blend=RGBA_MULT)
    assert scene.get_at((50, 50))[:3] == (100, 100, 100)  # 200 * 127 / 255 (SDL rounds)


def test_light_reveals_lit_area():
    scene = _solid((120, 120), (200, 200, 200))
    lm = LightMap((120, 120), scale=0.5)
    lm.clear()  # ambient black: only the light is visible
    light = PointLight(radius=30, color=(255, 255, 255), intensity=1.0)
    light.render(lm, 60, 60)
    lm.apply(scene, blend=RGBA_MULT)
    assert scene.get_at((60, 60)).r > 150  # lit center
    assert scene.get_at((5, 5)).r < 50  # unlit corner stays dark


def test_apply_mutates_and_returns_surface():
    scene = _solid((64, 64), (128, 128, 128))
    lm = LightMap((64, 64), scale=0.5)
    lm.clear()
    result = lm.apply(scene)
    assert result is scene


def test_sub_blend_darkens():
    scene = _solid((64, 64), (200, 200, 200))
    lm = LightMap((64, 64), scale=0.5)
    lm.set_ambient((255, 255, 255), 1.0)  # full-brightness light map
    lm.clear()
    lm.apply(scene, blend=RGB_SUB)
    assert scene.get_at((32, 32))[:3] == (0, 0, 0)


def test_max_blend_keeps_brightest():
    scene = _solid((64, 64), (50, 50, 50))
    lm = LightMap((64, 64), scale=0.5)
    lm.set_ambient((255, 255, 255), 1.0)
    lm.clear()
    lm.apply(scene, blend=RGB_MAX)
    assert scene.get_at((32, 32))[:3] == (255, 255, 255)


def test_add_blend_brightens():
    scene = _solid((64, 64), (100, 100, 100))
    lm = LightMap((64, 64), scale=0.5)
    lm.set_ambient((100, 100, 100), 1.0)
    lm.clear()
    lm.apply(scene, blend=RGB_ADD)
    assert scene.get_at((32, 32)).r == 200


def test_pixelated_apply_uses_nearest():
    scene = _solid((64, 64), (100, 100, 100))
    lm = LightMap((64, 64), scale=0.5, pixelated=True)
    lm.set_ambient((255, 255, 255), 1.0)
    lm.clear()
    # hard edge: left half of the light map bright, right half black
    lm._lightmap.fill((0, 0, 0, 255), pygame.Rect(16, 0, 16, 32))
    lm.apply(scene)
    # nearest scaling keeps the edge pixel-exact (smoothscale would gray it)
    assert scene.get_at((31, 0))[:3] == (100, 100, 100)
    assert scene.get_at((32, 0))[:3] == (0, 0, 0)


def test_set_scale_resizes_lightmap():
    lm = LightMap((100, 100), scale=0.5)
    assert lm.lightmap_size == (50, 50)
    lm.set_scale(0.25)
    assert lm.lightmap_size == (25, 25)


def test_add_sprite_custom_position_and_blend():
    lm = LightMap((100, 100), scale=1.0)
    lm.clear()
    sprite = glow_sprite(radius=10)
    lm.add_sprite(sprite, 50, 50, blend=RGB_ADD)
    # sprite was centered at (50, 50) in a 100x100 light map
    assert lm._lightmap.get_at((50, 50)).r > 200


# ----------------------------------------------------------------- lights


def test_point_light_owns_private_sprite():
    a = PointLight(radius=24)
    b = PointLight(radius=24)
    assert a.sprite() is not b.sprite()


def test_point_light_flicker_bounded_and_deterministic_off():
    light = PointLight(radius=24)
    assert light.modulation() == 1.0  # no flicker configured
    light.set_flicker(frequency=8.0, amplitude=0.2, jitter=0.0)
    for _ in range(200):
        light.advance(1 / 60)
        assert 0.0 <= light.modulation() <= 1.0


def test_spotlight_direction_points_down_at_pi_over_2():
    light = Spotlight(radius=32, cone=0.5, softness=0.1)
    light.set_direction(math.pi / 2)  # down on screen
    sprite = light.sprite()
    rect = sprite.get_rect()
    center = rect.center
    below = sprite.get_at((center[0], center[1] + 12))
    above = sprite.get_at((center[0], center[1] - 12))
    assert below.r > above.r + 100


def test_spotlight_rotation_cache():
    light = Spotlight(radius=32)
    light.set_direction(0.5)
    a = light.sprite()
    light.set_direction(0.5)
    b = light.sprite()
    assert a is b  # same angle bucket, cached


def test_spotlight_buckets_share_rotations():
    light = Spotlight(radius=32, rotation_step=4.0)
    light.set_direction(0.0)
    s0 = light.sprite()
    light.set_direction(0.02)  # 1.1 deg, same 4-deg bucket
    assert light.sprite() is s0


# ---------------------------------------------------------- dynamic light


def _tostring(surf):
    return pygame.image.tobytes(surf, "RGBA")


def test_dynamic_sprite_deterministic():
    a = dynamic_glow_sprite(radius=32, wind=(1.0, 0.5), seed=5)
    b = dynamic_glow_sprite(radius=32, wind=(1.0, 0.5), seed=5)
    assert _tostring(a) == _tostring(b)


def test_dynamic_sprite_wind_changes_shape():
    still = dynamic_glow_sprite(radius=32, wind=(0.0, 0.0), seed=1)
    blown = dynamic_glow_sprite(radius=32, wind=(2.0, 0.0), seed=1)
    assert _tostring(still) != _tostring(blown)


def test_dynamic_sprite_anisotropic():
    sprite = dynamic_glow_sprite(radius=48, wind=(40.0, 0.0), seed=0)
    cx = cy = 48
    windward = sprite.get_at((cx - 24, cy))  # against the wind
    leeward = sprite.get_at((cx + 24, cy))  # downwind
    perp = sprite.get_at((cx, cy - 24))
    # hot core shifts against the wind: upwind side brighter at same distance
    assert windward.r > leeward.r
    # glow elongates downwind: brighter along the axis than across it
    assert leeward.r > perp.r


def test_dynamic_light_bucket_caching():
    lm = LightMap((200, 200), scale=0.5)
    light = DynamicLight(radius=60)
    light.render(lm, 100, 100)
    first = light._sprite
    # sub-threshold wind stays in the no-wind bucket
    light.set_wind(2.0, 0.0)
    light.render(lm, 100, 100)
    assert light._sprite is first
    # strong wind crosses into a new bucket -> rebake
    light.set_wind(30.0, 0.0)
    light.render(lm, 100, 100)
    assert light._sprite is not first
    # same bucket again -> cached
    light.render(lm, 100, 100)
    second = light._sprite
    light.set_wind(30.0, 1.0)  # tiny perpendicular tilt, same bucket
    light.render(lm, 100, 100)
    assert light._sprite is second


def test_dynamic_sprite_matches_lightmap_scale():
    lm = LightMap((200, 200), scale=0.25)
    light = DynamicLight(radius=120)
    light.render(lm, 100, 100)
    assert light._sprite.get_size() == (60, 60)  # 2 * round(120 * 0.25)


def test_dynamic_light_rebakes_when_scale_changes():
    lm = LightMap((200, 200), scale=0.25)
    light = DynamicLight(radius=120)
    light.render(lm, 100, 100)
    assert light._sprite.get_size() == (60, 60)
    lm.set_scale(0.5)  # light map resized -> cached sprite is stale
    light.render(lm, 100, 100)
    assert light._sprite.get_size() == (120, 120)  # 2 * round(120 * 0.5)
    light.render(lm, 100, 100)  # same scale again -> cached
    first = light._sprite
    light.render(lm, 100, 100)
    assert light._sprite is first


def test_regen_interval_forces_rebake():
    lm = LightMap((100, 100), scale=0.5)
    light = DynamicLight(radius=30)
    light.set_regen_interval(2)
    light.render(lm, 50, 50)
    a = light._sprite
    light.render(lm, 50, 50)  # 2nd render: interval due -> rebake
    b = light._sprite
    assert b is not a
    light.render(lm, 50, 50)  # 3rd render: not due -> cached
    assert light._sprite is b


def test_set_direction_matches_vector():
    lm = LightMap((100, 100), scale=0.5)
    a = DynamicLight(radius=40)
    a.set_direction(30, 0.8)  # compass degrees: 0 right, 90 down, 270 up
    b = DynamicLight(radius=40)
    # strength 0..1 is normalized to radius * 0.6 px/frame (full range)
    mag = 0.8 * max(1.0, 40 * 0.6)
    b.set_wind(math.cos(math.radians(30)) * mag, math.sin(math.radians(30)) * mag)
    a.render(lm, 50, 50)
    b.render(lm, 50, 50)
    assert _tostring(a._sprite) == _tostring(b._sprite)


def test_direction_compass_up_is_negative_y():
    lm = LightMap((100, 100), scale=0.5)
    up = DynamicLight(radius=40)
    up.set_direction(270, 0.8)  # 270 = up in screen coords
    assert abs(up.wind[0]) < 1e-9
    assert up.wind[1] < 0


def test_dynamic_regen_perf_budget():
    # generous bound: nominal cost is ~5-20 ms, but CI machines vary a lot
    t0 = time.perf_counter()
    for _ in range(10):
        dynamic_glow_sprite(radius=30, wind=(1.0, 0.5))
    elapsed = time.perf_counter() - t0
    assert elapsed < 1.0  # still catches pathological regressions
