"""
Interactive audio demo.
1-6 play, S stop all, M mute/unmute sfx, -/+ sfx volume, F fade main, Q quit.

Needs: pygkit[audio]
"""
from pathlib import Path

import pygame

from pygkit.audio import SFX_CHANNELS, SoundManager

ASSETS = Path(__file__).parent / "assets" / "sounds"

pygame.init()
pygame.mixer.init()
pygame.display.set_mode((400, 300))
pygame.display.set_caption("pygkit Audio Demo")

sm = SoundManager()
sm.add_sound(ASSETS / "Shoot.wav", "shoot", "sfx")
sm.add_sound(ASSETS / "Jump.wav", "jump", "sfx")
sm.add_sound(ASSETS / "Hit.wav", "hit", "sfx")
sm.add_sound(ASSETS / "Powerup.wav", "powerup", "sfx")
sm.add_sound(ASSETS / "Nextlevel.wav", "next_level", "main")
sm.add_sound(ASSETS / "enemy_death.wav", "death", "sfx")

KEY_MAP = {
    pygame.K_1: ("shoot", "sfx"),
    pygame.K_2: ("jump", "sfx"),
    pygame.K_3: ("hit", "sfx"),
    pygame.K_4: ("powerup", "sfx"),
    pygame.K_5: ("next_level", "main"),
    pygame.K_6: ("death", "sfx"),
}

font = pygame.font.Font(None, 28)
small = pygame.font.Font(None, 20)

clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            elif event.key in KEY_MAP:
                key, kind = KEY_MAP[event.key]
                sm.play(key, kind)
            elif event.key == pygame.K_s:
                sm.stop_all()
            elif event.key == pygame.K_m:
                muted = sm.get_volume(kind="sfx") > 0.0
                sm.set_volume(0.0 if muted else 1.0, kind="sfx")
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                sm.set_volume(sm.get_volume(kind="sfx") - 0.1, kind="sfx")
            elif event.key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
                sm.set_volume(sm.get_volume(kind="sfx") + 0.1, kind="sfx")
            elif event.key == pygame.K_f:
                sm.fadeout(800, kind="main")

    screen = pygame.display.get_surface()
    screen.fill((20, 20, 30))

    y = 20
    screen.blit(font.render("pygkit Audio Demo", True, (200, 200, 255)), (20, y))
    y += 40
    screen.blit(small.render("1-6: Play  |  S: stop all  |  M: mute sfx  |  -/+: sfx vol  |  F: fade main  |  Q: Quit", True, (180, 180, 180)), (20, y))
    y += 30

    for i, (k, (name, kind)) in enumerate(KEY_MAP.items()):
        loop_hint = " (loops)" if kind == "main" else ""
        label = f"{i + 1}: {name} ({kind}{loop_hint})"
        screen.blit(small.render(label, True, (220, 220, 220)), (40, y))
        y += 22

    y += 10
    screen.blit(
        small.render(f"sfx vol: {sm.get_volume(kind='sfx'):.2f}  |  SFX_CHANNELS: {SFX_CHANNELS}", True, (150, 200, 150)),
        (20, y),
    )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
