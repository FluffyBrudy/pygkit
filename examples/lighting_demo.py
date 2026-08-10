"""
pygkit lighting demo - night scene with torch, campfire, spotlight.

Scene: a moonlit night, a flickering torch, a wind-reactive campfire, a
crate casting a negative light (shadow), an auto-orbiting player light and
a mouse-following spotlight.

Controls:
  B      cycle apply blend: MULT -> MAX -> ADD -> SUB
  P      toggle pixelated (chunky pixel-art lights)
  S      cycle light map scale: 0.25 -> 0.5 -> 1.0
  L      toggle spotlight
  T      toggle torch
  C      toggle campfire
  LEFT/RIGHT  rotate wind direction
  UP/DOWN     wind strength
  R      toggle dynamic regen (dancing flame wobble)
  M      toggle player light (auto-orbiting <-> mouse)
  Q/Esc  quit

Run headless for a smoke test:  python lighting_demo.py --frames 120
"""

import argparse
import math
import os
import random

import pygame
from pygame import Surface

from pygkit.lighting import DynamicLight, LightMap, PointLight, Spotlight
from pygkit.lighting.blend import RGB_ADD, RGB_MAX, RGB_MULT, RGB_SUB
from pygkit.lighting.sprites import glow_sprite

W, H = 960, 600
SKY_TOP = (18, 22, 48)
SKY_BOTTOM = (4, 5, 12)

BLEND_MODES = [
    ("MULT", RGB_MULT),
    ("MAX", RGB_MAX),
    ("ADD", RGB_ADD),
    ("SUB", RGB_SUB),
]
SCALES = (0.25, 0.5, 1.0)


def build_background() -> Surface:
    """Night backdrop: gradient sky, stars, moon, ground, wall, pillar."""
    bg = pygame.Surface((W, H))

    for y in range(H):
        t = y / H
        r = int(SKY_TOP[0] * (1 - t) + SKY_BOTTOM[0] * t)
        g = int(SKY_TOP[1] * (1 - t) + SKY_BOTTOM[1] * t)
        b = int(SKY_TOP[2] * (1 - t) + SKY_BOTTOM[2] * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (W, y))

    rng = random.Random(7)
    for _ in range(90):
        x = rng.randrange(0, W)
        y = rng.randrange(0, int(H * 0.55))
        v = rng.randrange(90, 200)
        bg.set_at((x, y), (v, v, v + 20))

    pygame.draw.circle(bg, (235, 240, 255), (W - 120, 90), 34)

    ground_y = int(H * 0.78)
    pygame.draw.rect(bg, (58, 52, 74), (0, ground_y, W, H - ground_y))
    for x in range(0, W, 40):
        shade = (x // 40) % 2
        c = (78, 70, 96) if shade else (64, 58, 80)
        pygame.draw.rect(bg, c, (x, ground_y, 40, 24))
    pygame.draw.line(bg, (104, 96, 124), (0, ground_y), (W, ground_y), 2)

    wall = pygame.Rect(0, 150, 70, ground_y - 150)
    pygame.draw.rect(bg, (86, 78, 104), wall)
    for y in range(150, ground_y, 24):
        for x in range(0, 70, 24):
            pygame.draw.rect(bg, (100, 92, 120), (x, y, 23, 23), 1)

    pillar_x = W - 190
    pygame.draw.rect(bg, (70, 64, 88), (pillar_x, 260, 60, ground_y - 260))
    pygame.draw.rect(bg, (94, 86, 112), (pillar_x, 260, 60, 14))

    return bg


def make_crate_shadow_sprite() -> Surface:
    """Soft dark blob used as a negative light (RGBA_SUB) under the crate."""
    return glow_sprite(radius=64, color=(255, 255, 255), falloff="sharp", exponent=2.0)


def build_scene_sprites() -> tuple[Surface, Surface]:
    torch = pygame.Surface((28, 44), pygame.SRCALPHA)
    pygame.draw.rect(torch, (66, 52, 30), (10, 24, 8, 20))
    pygame.draw.circle(torch, (120, 78, 30), (14, 18), 9)
    pygame.draw.circle(torch, (255, 180, 60), (14, 12), 6)
    pygame.draw.circle(torch, (255, 235, 160), (14, 9), 3)

    crate = pygame.Surface((46, 40), pygame.SRCALPHA)
    pygame.draw.rect(crate, (96, 72, 40), (0, 0, 46, 40))
    pygame.draw.rect(crate, (70, 52, 28), (0, 0, 46, 40), 3)
    pygame.draw.line(crate, (70, 52, 28), (0, 20), (46, 20), 2)
    pygame.draw.line(crate, (70, 52, 28), (23, 0), (23, 40), 2)

    return torch, crate


def build_campfire_pile() -> Surface:
    """Static wood pile + stones for the campfire."""
    pile = pygame.Surface((54, 30), pygame.SRCALPHA)
    pygame.draw.rect(pile, (88, 60, 30), (6, 6, 42, 9))
    pygame.draw.rect(pile, (70, 48, 24), (8, 12, 38, 8))
    pygame.draw.rect(pile, (56, 38, 18), (14, 18, 26, 7))
    for i in range(7):
        pygame.draw.circle(pile, (92, 92, 104), (4 + i * 8, 26), 4)
    return pile


FLAME_W, FLAME_H = 76, 84
FLAME_LAYERS = (
    (17, (255, 110, 20, 120), 0.0),   # outer glow
    (12, (255, 160, 50, 180), 0.7),   # mid flame
    (6, (255, 235, 150, 235), 1.4),   # hot core
)


def draw_flame(target: Surface, x: float, y: float, t: float, wind: tuple[float, float], mod: float) -> None:
    """
    Semi-transparent layered flame leaning with the wind vector.

    ``(x, y)`` is the fire base. The flame pivots around that base point:
    at rest every layer shares one vertical axis (concentric with the ember
    bed and the fuel below); under wind only the upper body displaces, so
    the stack stays rooted.
    """
    flame = pygame.Surface((FLAME_W, FLAME_H), pygame.SRCALPHA)
    cx = FLAME_W / 2
    base_y = FLAME_H - 18          # base point in surface coords
    vx, vy = wind
    pulse = 0.85 + 0.3 * mod       # flicker shrinks the whole flame together
    sway = math.sin(t * 11) * 2.5  # bending wobble, tip-to-base

    # each layer's center height above the base point; the lean of every
    # layer scales with it, so the flame bends while its root stays put
    layers = []
    for w, color, rise in FLAME_LAYERS:
        w_scaled = max(2, w * pulse)
        h = (30 + rise * 20) * pulse
        center_h = h / 2 + w_scaled * 0.15 + 4
        layers.append((w_scaled, color, h, center_h))
    top = max(layers, key=lambda layer: layer[3])[3]

    for w_scaled, color, h, center_h in layers:
        lean = vx * center_h * 0.35 + sway * center_h / top
        dy = vy * center_h * 0.06
        rect = (
            cx - w_scaled + lean,
            base_y - h - w_scaled * 0.5 + dy,
            w_scaled * 2,
            h + w_scaled * 0.7,  # tall enough to merge with the ember
        )
        pygame.draw.ellipse(flame, color, rect)

    # ember bed rooted on the base point - stays put while the flame leans
    pygame.draw.circle(flame, (255, 120, 30, 130), (int(cx), int(base_y + 4)), 12)
    pygame.draw.circle(flame, (255, 200, 110, 160), (int(cx), int(base_y + 2)), 7)
    target.blit(flame, (x - FLAME_W / 2, y - base_y))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=0, help="run N frames then quit (smoke test)")
    args = parser.parse_args()

    # headless smoke test: run without a video device
    if args.frames:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("pygkit lighting demo")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 22)
    small = pygame.font.Font(None, 18)

    bg = build_background()
    torch_spr, crate_spr = build_scene_sprites()
    pile_spr = build_campfire_pile()
    shadow_spr = make_crate_shadow_sprite()

    CAMP_X, CAMP_Y = 640, 458  # fire base: pile top surface
    scene = pygame.Surface((W, H))
    lightmap = LightMap((W, H), scale=0.5)
    lightmap.set_ambient((24, 30, 60), 0.16)

    moon = PointLight(radius=230, color=(200, 215, 255), intensity=0.55)
    torch = PointLight(radius=150, color=(255, 190, 120), intensity=1.1)
    torch.set_flicker(frequency=9.0, amplitude=0.22, jitter=0.08)
    camp = DynamicLight(radius=130, color=(255, 170, 90), intensity=1.15, seed=3)
    camp.set_flicker(frequency=7.0, amplitude=0.25, jitter=0.09)
    player_light = PointLight(radius=110, color=(150, 220, 255), intensity=0.9)
    spotlight = Spotlight(
        radius=270, cone=0.6, softness=0.18, color=(255, 240, 200), intensity=1.0
    )

    blend_idx = 0
    scale_idx = 1
    show_spot = True
    show_torch = True
    show_camp = True
    dyn_regen = False
    wind_angle = 270  # compass degrees: 0 right, 90 down, 270 up
    wind_strength = 0.6
    mouse_mode = False
    t = 0.0

    print("pygkit lighting demo")
    print("  B blend | P pixelated | S light map scale | L spot | T torch | C camp |")
    print("  LEFT/RIGHT wind dir | UP/DOWN wind strength | R dyn regen | M mouse | Q quit")

    frame = 0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        t += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_b:
                    blend_idx = (blend_idx + 1) % len(BLEND_MODES)
                elif event.key == pygame.K_p:
                    lightmap.pixelated = not lightmap.pixelated
                elif event.key == pygame.K_s:
                    scale_idx = (scale_idx + 1) % len(SCALES)
                    lightmap.set_scale(SCALES[scale_idx])
                elif event.key == pygame.K_l:
                    show_spot = not show_spot
                elif event.key == pygame.K_t:
                    show_torch = not show_torch
                elif event.key == pygame.K_c:
                    show_camp = not show_camp
                elif event.key == pygame.K_r:
                    dyn_regen = not dyn_regen
                    camp.set_regen_interval(5 if dyn_regen else 0)
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    wind_angle += 15 if event.key == pygame.K_RIGHT else -15
                    wind_angle %= 360
                elif event.key in (pygame.K_UP, pygame.K_DOWN):
                    wind_strength = max(
                        0.0, min(1.0, wind_strength + (0.1 if event.key == pygame.K_UP else -0.1))
                    )
                elif event.key == pygame.K_m:
                    mouse_mode = not mouse_mode

        scene.blit(bg, (0, 0))
        scene.blit(crate_spr, (352, 428))
        scene.blit(torch_spr, (136, 432))
        scene.blit(pile_spr, (CAMP_X - 27, CAMP_Y))

        lightmap.clear()
        moon.render(lightmap, W - 120, 90)

        if show_torch:
            torch.advance(dt)
            torch.render(lightmap, 150, 450)
            # crate blocks the torch: a negative light (SUB) darkens the
            # light map on the shadowed side of the crate
            lightmap.add_sprite(shadow_spr, 415, 452, RGB_SUB)

        if show_camp:
            camp.set_direction(wind_angle, wind_strength)
            camp.advance(dt)
            camp.render(lightmap, CAMP_X, CAMP_Y)
            # wind is radius-scaled (px/frame); normalize back to 0..1 for
            # the drawn flame
            wscale = max(1.0, camp.radius * 0.6)
            flow = (camp.wind[0] / wscale, camp.wind[1] / wscale)
            draw_flame(scene, CAMP_X, CAMP_Y, t, flow, camp.modulation())

        if mouse_mode:
            px, py = pygame.mouse.get_pos()
        else:
            px = W * 0.5 + math.sin(t * 0.7) * 220
            py = H * 0.55 + math.cos(t * 0.9) * 110
        player_light.render(lightmap, px, py)
        pygame.draw.circle(scene, (140, 210, 255), (int(px), int(py)), 9)
        pygame.draw.circle(scene, (230, 250, 255), (int(px), int(py)), 4)

        if show_spot:
            mx, my = pygame.mouse.get_pos()
            spotlight.set_direction(math.atan2(my - 70, mx - 60))
            spotlight.render(lightmap, 60, 70)

        blend_name, blend = BLEND_MODES[blend_idx]
        lightmap.apply(scene, blend=blend)

        screen.blit(scene, (0, 0))

        fps = clock.get_fps()
        lines = [
            f"FPS {fps:5.1f}",
            f"blend: {blend_name}",
            f"light map scale: {lightmap.scale:g}",
            f"pixelated: {lightmap.pixelated}",
            f"spot: {show_spot}  torch: {show_torch}  camp: {show_camp}",
            f"dir: {wind_angle:5.0f} deg  str: {wind_strength:.2f}  dyn: {'on' if dyn_regen else 'off'}",
        ]
        y = 8
        for i, line in enumerate(lines):
            c = (255, 255, 255) if i else (140, 255, 160)
            surf = small.render(line, True, c)
            surf.set_alpha(220)
            screen.blit(surf, (8, y))
            y += 16

        pygame.display.flip()

        frame += 1
        if args.frames and frame >= args.frames:
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()
