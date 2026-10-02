"""Grotto runner: fixture art on ParallaxBackground + Camera2D follow.

Art: Super Grotto Escape pack by ansimuz (CC0).
Needs: pygkit[parallax]
A/D or arrows move - Space auto-run - Q quit.
"""

import math
import random
from pathlib import Path

import pygame

from pygkit.parallax import Camera2D, ParallaxBackground, ParallaxLayer

ASSETS = Path(__file__).parent.parent / "assets" / "grotto"
W, H = 960, 540
SCALE = 2
GROUND_Y = 442

LAYERS = [
    ("back.png", (0.08, 0.0)),
    ("far.png", (0.20, 0.05)),
    ("middle.png", (0.45, 0.10)),
    ("tiledemo.png", (1.0, 0.0)),
]

PROPS = [
    ("props/palm.png", 0.45, 260),
    ("props/plant-big.png", 0.45, 980),
    ("props/plant.png", 1.0, 480),
    ("props/plant-big.png", 1.0, 1150),
]


def load_scaled(path, scale=SCALE):
    img = pygame.image.load(str(path)).convert_alpha()
    w, h = img.get_size()
    if scale == 1:
        return img
    return pygame.transform.scale(img, (w * scale, h * scale))


def make_sky():
    top, bottom = (16, 14, 46), (86, 52, 110)
    sky = pygame.Surface((W, H - 240 * SCALE))
    for y in range(sky.get_height()):
        t = y / max(1, sky.get_height() - 1)
        sky.fill(tuple(int(a + (b - a) * t) for a, b in zip(top, bottom)), (0, y, W, 1))
    return sky


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("parallax - grotto runner")
    clock = pygame.time.Clock()
    small = pygame.font.Font(None, 16)

    bg = ParallaxBackground(
        [ParallaxLayer(load_scaled(ASSETS / name), factor=f) for name, f in LAYERS]
    )
    props = [
        (load_scaled(ASSETS / name), f, wx)
        for name, f, wx in PROPS
        if (ASSETS / name).exists()
    ]

    rng = random.Random(7)
    stars = [
        (rng.uniform(0, W), rng.uniform(2, 56), rng.uniform(1.5, 4.0), rng.uniform(0, math.tau))
        for _ in range(80)
    ]

    cam = Camera2D(W, H)
    cam.lerp_speed = 5.0

    class Hero:
        def __init__(self):
            self.x = 400.0
            self.y = GROUND_Y

    hero = Hero()
    cam.follow(hero)
    sky = make_sky()
    auto, t = True, 0.0
    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        t += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_SPACE:
                    auto = not auto
        keys = pygame.key.get_pressed()
        move = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
        hero.x += move * 300 * dt
        if auto and move == 0:
            hero.x += 60 * dt
        cam.update(dt)

        screen.blit(sky, (0, 0))
        for x, y, speed, phase in stars:
            c = int(200 * (0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * speed + phase)))) + 55
            screen.fill((c, c, min(255, c + 20)), (x, y, 1, 1))
        pygame.draw.circle(screen, (255, 214, 150), (830, 40), 15)

        bg.render(screen, *cam.offset)
        for img, f, wx in props:
            sx = int(wx - cam.x * f)
            if -img.get_width() < sx < W:
                screen.blit(img, (sx, GROUND_Y + 2 - img.get_height()))
        hx = int(hero.x - cam.x)
        pygame.draw.ellipse(screen, (10, 8, 24, 140), (hx - 12, GROUND_Y - 2, 24, 6))
        pygame.draw.rect(screen, (72, 209, 178), (hx - 9, GROUND_Y - 30, 18, 30), border_radius=6)
        screen.blit(small.render("grotto runner: fixture art + follow cam", True, (220, 220, 235)), (10, 10))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
