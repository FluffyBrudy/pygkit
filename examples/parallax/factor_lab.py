"""Factor lab: zero, overdrive and reverse factors; top/center/bottom anchors.

Needs: pygkit[parallax]
1/2/3 anchor top/center/bottom - F cycle factor set - Q quit.
"""

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).parent))

from _common import band, load
from pygkit.parallax import ParallaxBackground, ParallaxLayer

W, H = 640, 360


def band(w, h, base, mark):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(base)
    for x in range(0, w, 32):
        pygame.draw.rect(s, mark, (x, h // 2 - 6, 16, 12))
    return s


SETS = [
    ("cruise", [(0.0, 0), (0.5, 0), (1.0, 0)]),
    ("overdrive + reverse", [(1.6, 0), (0.5, 0), (-0.4, 0)]),
    ("vertical drift", [(0.2, 0.3), (0.5, 0.0), (1.0, 0.6)]),
]


def build(anchor, preset):
    name, factors = SETS[preset]
    art = [
        ("back.png", lambda: band(220, 120, (30, 24, 64, 255), (90, 80, 160, 255))),
        ("far.png", lambda: band(300, 160, (30, 70, 90, 255), (80, 150, 170, 255))),
        ("middle.png", lambda: band(360, 100, (110, 80, 50, 255), (170, 130, 80, 255))),
    ]
    return (
        name,
        ParallaxBackground(
            [
                ParallaxLayer(load(n, 1, make)[0], factor=f, y_mode="tile", anchor=anchor)
                for (n, make), f in zip(art, factors)
            ]
        ),
    )


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("parallax - factor lab")
    clock = pygame.time.Clock()
    small = pygame.font.Font(None, 16)

    anchor, preset = "bottom", 0
    name, bg = build(anchor, preset)
    cam_x, cam_y, t = 0.0, 0.0, 0.0
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
                elif event.key == pygame.K_1:
                    anchor = "top"
                elif event.key == pygame.K_2:
                    anchor = "center"
                elif event.key == pygame.K_3:
                    anchor = "bottom"
                elif event.key == pygame.K_f:
                    preset = (preset + 1) % len(SETS)
                name, bg = build(anchor, preset)
        cam_x += 120 * dt
        cam_y = 60 + 40 * t % 120

        screen.fill((10, 10, 22))
        bg.render(screen, cam_x, cam_y)
        screen.blit(small.render(f"{name} - anchor {anchor} (1/2/3, F cycle)", True, (220, 220, 235)), (10, 10))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
