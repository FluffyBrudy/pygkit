"""Set-piece arena: once-mode props on a tiled field, deadzone camera, shake.

Needs: pygkit[parallax]
Arrows move - Space shake - Q quit.
"""

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent))

from _common import load
from pygkit.parallax import Camera2D, ParallaxBackground, ParallaxLayer

W, H = 640, 360


def field():
    s = pygame.Surface((160, 160), pygame.SRCALPHA)
    s.fill((36, 52, 40, 255))
    for x in range(0, 160, 16):
        for y in range(0, 160, 16):
            if (x + y) % 32 == 0:
                s.fill((44, 62, 48, 255), (x, y, 16, 16))
    return s


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("parallax - setpiece arena")
    clock = pygame.time.Clock()
    small = pygame.font.Font(None, 16)

    def prop(size, color):
        s = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (size, size), size)
        pygame.draw.circle(s, (70, 70, 85), (size, size), size, 4)
        return s

    bg = ParallaxBackground(
        [
            ParallaxLayer(field(), factor=(1.0, 1.0), y_mode="tile"),
            ParallaxLayer(load("props/palm.png", 2, lambda: prop(40, (110, 110, 125)))[0],
                          factor=(1.0, 1.0), x_mode="once", y_mode="once", offset=(800, 460)),
            ParallaxLayer(load("props/plant-big.png", 2, lambda: prop(24, (110, 110, 125)))[0],
                          factor=(1.0, 1.0), x_mode="once", y_mode="once", offset=(1500, 900)),
            ParallaxLayer(load("props/plant.png", 2, lambda: prop(60, (90, 90, 105)))[0],
                          factor=(0.5, 0.5), x_mode="once", y_mode="once", offset=(400, 200)),
        ]
    )
    cam = Camera2D(W, H, mode="deadzone")

    class Hero:
        def __init__(self):
            self.x = 900.0
            self.y = 600.0

    hero = Hero()
    cam.follow(hero)
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
                    cam.shake(0.3, 7.0)
        keys = pygame.key.get_pressed()
        hero.x += ((keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])) * 260 * dt
        hero.y += ((keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])) * 260 * dt
        cam.update(dt)

        screen.fill((12, 14, 12))
        bg.render(screen, *cam.offset)
        pygame.draw.circle(screen, (240, 200, 120), (int(hero.x - cam.x), int(hero.y - cam.y)), 10)
        screen.blit(small.render("once set-pieces + deadzone + shake", True, (220, 220, 235)), (10, 10))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
