"""Side runner: X tile + Y clamp-bottom with a follow camera.

Needs: pygkit[parallax]
Arrows/A,D move - Space auto-run - Q quit.
"""

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent))

from _common import band, load
from pygkit.parallax import Camera2D, ParallaxBackground, ParallaxLayer

W, H = 640, 360


def strip(w, h, base, ridge):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(base)
    for x in range(0, w, 24):
        pygame.draw.rect(s, ridge, (x, 0, 10, h))
    return s


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("parallax - side runner")
    clock = pygame.time.Clock()
    small = pygame.font.Font(None, 16)

    art = [
        ("back.png", 1, (0.1, 0.0), lambda: strip(200, 200, (24, 20, 54, 255), (60, 50, 110, 255))),
        ("far.png", 1, (0.3, 0.0), lambda: strip(260, 240, (34, 60, 90, 255), (70, 110, 150, 255))),
        ("middle.png", 1, (0.6, 0.0), lambda: strip(320, 280, (40, 110, 90, 255), (80, 170, 130, 255))),
        ("tiledemo.png", 1, (1.0, 0.0), lambda: strip(400, 120, (90, 70, 50, 255), (140, 110, 70, 255))),
        ("props/palm.png", 2, (1.6, 0.0), lambda: band(160, 200, (150, 60, 60, 180), (200, 120, 120, 180))),
    ]
    bg = ParallaxBackground(
        [ParallaxLayer(load(name, scale, make)[0], factor=f) for name, scale, f, make in art]
    )
    cam = Camera2D(W, H)
    cam.lerp_speed = 5.0

    class Hero:
        def __init__(self):
            self.x = W / 2
            self.y = H - 60

    hero = Hero()
    cam.follow(hero)
    auto = True
    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
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
        hero.x += move * 260 * dt
        if auto and move == 0:
            hero.x += 90 * dt
        cam.update(dt)

        screen.fill((12, 10, 26))
        bg.render(screen, *cam.offset)
        pygame.draw.rect(screen, (240, 200, 120), (int(hero.x - cam.x) - 9, hero.y - 30, 18, 30))
        screen.blit(small.render("side runner: X tile, Y clamp", True, (220, 220, 235)), (10, 10))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
