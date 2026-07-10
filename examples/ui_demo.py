"""
Interactive UI demo.
Shows ProgressBarUI, CooldownOverlay, and Container in a game-like HUD.
Keys: 1-3 cooldowns, D toggle disabled, SPACE toggle HP, R reset.
"""

from typing import cast

import pygame

from pygkit.ui import Container, CooldownOverlay, ProgressBarUI
from pygkit.utils import Timer

pygame.init()
pygame.display.set_mode((640, 400))
pygame.display.set_caption("pygkit UI Demo")
font = pygame.font.Font(None, 22)
small = pygame.font.Font(None, 16)

clock = pygame.time.Clock()
running = True


hp_bar = ProgressBarUI(width=300, height=20, fill_color=(220, 60, 60), background=(60, 20, 20))
mana_bar = ProgressBarUI(width=300, height=14, fill_color=(60, 120, 220), background=(15, 30, 60))
hp_bar.set_progress(0.75)
mana_bar.set_progress(0.45)


dash_timer = Timer(3000, stale_init=True)
dash_cd = CooldownOverlay(dash_timer, 48, border_color=(100, 200, 255), border_width=2, border_radius=4)

shield_timer = Timer(5000, stale_init=True)
shield_cd = CooldownOverlay(shield_timer, 48, border_color=(255, 220, 60), border_width=2, border_radius=4)

ult_timer = Timer(8000, stale_init=True)
ult_cd = CooldownOverlay(ult_timer, 48, border_color=(255, 80, 120), border_width=2, border_radius=4)


skills = Container()
skills.add(dash_cd, (20, 80))
skills.add(shield_cd, (80, 80))
skills.add(ult_cd, (140, 80))

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            elif event.key == pygame.K_SPACE:
                hp_bar.set_progress(1.0 if hp_bar.get_progress() < 0.1 else 0.0)
            elif event.key == pygame.K_r:
                hp_bar.set_progress(0.75)
                mana_bar.set_progress(0.45)
            elif event.key == pygame.K_d:
                dash_cd.disabled = not dash_cd.disabled
                shield_cd.disabled = not shield_cd.disabled
                ult_cd.disabled = not ult_cd.disabled
            elif event.key == pygame.K_1:
                dash_timer.reset()
            elif event.key == pygame.K_2:
                shield_timer.reset()
            elif event.key == pygame.K_3:
                ult_timer.reset()

    mana = mana_bar.get_progress()
    mana_bar.set_progress(max(0, mana - 0.001))

    hp_bar.update()
    mana_bar.update()
    skills.update()

    screen = cast(pygame.Surface, pygame.display.get_surface())
    screen.fill((25, 25, 35))

    offset_x = 20
    hp_bar.render(screen, (offset_x, 15))
    mana_bar.render(screen, (offset_x, 42))

    skills.render(screen)

    y = 150
    for line in [
        "SPACE: toggle HP  |  D: toggle disabled  |  R: reset",
        "1: dash CD  |  2: shield CD  |  3: ult CD",
        "Q: quit",
    ]:
        screen.blit(small.render(line, True, (160, 160, 180)), (20, y))
        y += 20

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
