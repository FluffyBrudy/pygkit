"""Mode matrix: all nine x_mode/y_mode combinations in one grid.

Needs: pygkit[parallax]
Camera drifts on detuned sines so once-mode tiles slide out and back.
Q quit.
"""

import math

import pygame

from pygkit.parallax import ParallaxBackground, ParallaxLayer

CELL_W, CELL_H = 300, 170
COLS = 3
W, H = CELL_W * COLS + 20, CELL_H * 3 + 60


def tile(color):
    s = pygame.Surface((90, 60), pygame.SRCALPHA)
    s.fill(color)
    pygame.draw.rect(s, (255, 255, 255, 255), (0, 0, 90, 6))
    pygame.draw.rect(s, (255, 255, 255, 255), (0, 0, 6, 60))
    return s


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("parallax - mode matrix")
    clock = pygame.time.Clock()
    small = pygame.font.Font(None, 15)

    modes = ["tile", "clamp", "once"]
    cells = []
    for xm in modes:
        for ym in modes:
            cells.append(
                (
                    f"{xm}/{ym}",
                    ParallaxBackground(
                        [ParallaxLayer(tile((60, 90, 150, 255)), factor=(0.7, 0.5), x_mode=xm, y_mode=ym)]
                    ),
                )
            )
    running = True
    t = 0.0
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.05)
        t += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False
        screen.fill((12, 12, 20))
        cam_x = 65 + 65 * math.sin(t * 0.35)
        cam_y = 45 + 45 * math.sin(t * 0.27 + 1.0)
        for i, (label, bg) in enumerate(cells):
            cx = 10 + (i % COLS) * CELL_W
            cy = 40 + (i // COLS) * CELL_H
            view = screen.subsurface((cx, cy, CELL_W - 10, CELL_H - 10))
            view.fill((18, 18, 30))
            bg.render(view, cam_x, cam_y)
            screen.blit(small.render(label, True, (220, 220, 235)), (cx + 6, cy + 4))
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
