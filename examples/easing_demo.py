"""
Interactive easing curve visualizer.
Press 1-5 to switch easing functions.
"""

import math

import pygame

from pygkit.utils.interpolation import ease_in, ease_in_out, ease_out, smoothstep

EASINGS = {
    pygame.K_1: ("smoothstep", smoothstep),
    pygame.K_2: ("ease_in (quad)", ease_in),
    pygame.K_3: ("ease_out (quad)", ease_out),
    pygame.K_4: ("ease_in_out", ease_in_out),
}

pygame.init()
pygame.display.set_mode((600, 400))
pygame.display.set_caption("pygkit Easing Curves")
font = pygame.font.Font(None, 24)
small = pygame.font.Font(None, 18)

clock = pygame.time.Clock()
running = True

current_name = "smoothstep"
current_fn = smoothstep

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in EASINGS:
                current_name, current_fn = EASINGS[event.key]

    screen = pygame.display.get_surface()
    w, h = screen.get_size()
    screen.fill((15, 15, 25))

    margin = 60
    gw = w - margin * 2
    gh = h - margin * 2

    # draw grid
    for i in range(11):
        x = margin + int(gw * i / 10)
        pygame.draw.line(screen, (40, 40, 55), (x, margin), (x, margin + gh))
        y = margin + int(gh * i / 10)
        pygame.draw.line(screen, (40, 40, 55), (margin, y), (margin + gw, y))

    # draw curve
    prev = None
    for px in range(gw):
        t = px / gw
        v = current_fn(t)
        x = margin + px
        y = margin + gh - int(v * gh)
        if prev is not None:
            pygame.draw.line(screen, (100, 200, 255), prev, (x, y), 3)
        prev = (x, y)

    # axis labels
    screen.blit(font.render(current_name, True, (200, 200, 255)), (margin, 15))
    screen.blit(small.render("1-4: switch easing  |  Q: quit", True, (140, 140, 160)), (margin, h - 20))

    y = 35
    for k, (name, _) in EASINGS.items():
        highlight = (200, 200, 255) if name == current_name else (140, 140, 160)
        screen.blit(small.render(f"{chr(k)}: {name}", True, highlight), (margin + 200, y))
        y += 18

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
