"""Sky climb: Y tile + X clamp with bounded camera.

Needs: pygkit[parallax]
Up/Down climb - Q quit.
"""

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent))

from _common import load
from pygkit.parallax import Camera2D, ParallaxBackground, ParallaxLayer

W, H = 480, 640


def strip(w, h, base, puff):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((0, 0, 0, 0))
    for i, y in enumerate(range(0, h, 60)):
        pygame.draw.ellipse(s, puff, ((i * 53) % (w - 90), y, 90, 34))
    pygame.draw.rect(s, base, (0, 0, w, h), 1)
    return s


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("parallax - sky climb")
    clock = pygame.time.Clock()
    small = pygame.font.Font(None, 16)

    art = [
        ("back.png", (0.0, 0.1), lambda: strip(480, 160, (20, 20, 50, 255), (50, 50, 110, 255))),
        ("far.png", (0.0, 0.35), lambda: strip(480, 220, (30, 40, 90, 255), (70, 90, 150, 255))),
        ("middle.png", (0.0, 0.7), lambda: strip(480, 300, (40, 80, 120, 255), (90, 140, 180, 255))),
    ]
    bg = ParallaxBackground(
        [ParallaxLayer(load(name, 2, make)[0], factor=f, x_mode="clamp", y_mode="tile") for name, f, make in art]
    )
    cam = Camera2D(W, H)
    cam.lerp_speed = 4.0
    cam.set_bounds(0, -4000, W, 0)

    class Balloon:
        def __init__(self):
            self.x = W / 2
            self.y = -320

    balloon = Balloon()
    cam.follow(balloon)
    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False
        keys = pygame.key.get_pressed()
        move = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) or (keys[pygame.K_s] - keys[pygame.K_w])
        balloon.y += move * 300 * dt
        cam.update(dt)

        screen.fill((10, 12, 30))
        bg.render(screen, *cam.offset)
        bx, by = int(balloon.x - cam.x), int(balloon.y - cam.y)
        pygame.draw.ellipse(screen, (220, 120, 120), (bx - 16, by - 40, 32, 40))
        pygame.draw.rect(screen, (120, 90, 70), (bx - 8, by + 4, 16, 10))
        screen.blit(small.render("climb: Y tile, X clamp, bounded", True, (220, 220, 235)), (10, 10))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
