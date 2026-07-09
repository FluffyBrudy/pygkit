"""
pygkit Showcase — clean all-in-one demo combining audio, UI, transitions, and utils.
"""

import math
from pathlib import Path

import pygame

from pygkit.audio import SoundManager
from pygkit.transitions import (
    Crossfade,
    FadeFromBlack,
    FadeToBlack,
    TransitionRunner,
)
from pygkit.ui import CooldownOverlay, ProgressBarUI
from pygkit.utils import Timer
from pygkit.utils.text import outline, render_multiline, shadow

W, H = 640, 480

pygame.init()
pygame.mixer.init()
pygame.display.set_mode((W, H))
pygame.display.set_caption("pygkit Showcase")
font = pygame.font.Font(None, 26)
small = pygame.font.Font(None, 17)

clock = pygame.time.Clock()
running = True

ASSETS = Path(__file__).parent / "assets" / "sounds"

# Audio
sm = SoundManager()
if ASSETS.exists():
    sm.add_sound(ASSETS / "Shoot.wav", "shoot", "sfx")
    sm.add_sound(ASSETS / "Powerup.wav", "powerup", "sfx")
    sm.add_sound(ASSETS / "Nextlevel.wav", "next_level", "main")

# HUD
hp_bar = ProgressBarUI(width=300, height=18, fill_color=(200, 60, 60), background=(50, 15, 15))
mana_bar = ProgressBarUI(width=300, height=12, fill_color=(60, 130, 230), background=(12, 25, 50))
exp_bar = ProgressBarUI(width=300, height=10, fill_color=(100, 210, 100), background=(15, 40, 15))
hp_bar.set_progress(0.65)
mana_bar.set_progress(0.30)
exp_bar.set_progress(0.0)

# Cooldowns
dash_timer = Timer(3000, stale_init=True)
shield_timer = Timer(5000, stale_init=True)
dash_cd = CooldownOverlay(dash_timer, 40, overlay_color=(0, 0, 0, 80), border_color=(80, 200, 255), border_width=2, border_radius=4)

shield_cd = CooldownOverlay(shield_timer, 40, overlay_color=(255, 255, 255, 80), border_color=(255, 200, 60), border_width=2, border_radius=4)
# Transition
runner = TransitionRunner(FadeToBlack(), FadeFromBlack())
scene_color = 0
transitioning = False

# A simple player dot
player_x, player_y = W // 2, H // 2
player_vx, player_vy = 0, 0
score = 0

# Particles (simple decoration)
particles = []

def add_particles(x, y, count=12):
    for _ in range(count):
        angle = math.radians(pygame.time.get_ticks() % 360)
        speed = 1 + 3
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "life": 1.0,
        })

while running:
    dt = clock.tick(60) / 1000.0
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and not transitioning:
                running = False
            elif event.key == pygame.K_t and not transitioning:
                transitioning = True
                runner.start_out(0.5)
            elif event.key == pygame.K_d:
                dash_timer.reset()
                sm.play("powerup", "sfx")
                add_particles(player_x, player_y)
            elif event.key == pygame.K_s:
                shield_timer.reset()
                sm.play("shoot", "sfx")
                add_particles(player_x, player_y)

    if not transitioning:
        # Player movement
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]: dx -= 1
        if keys[pygame.K_RIGHT]: dx += 1
        if keys[pygame.K_UP]: dy -= 1
        if keys[pygame.K_DOWN]: dy += 1
        if dx or dy:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length
            player_vx = player_vx * 0.8 + dx * 200 * dt
            player_vy = player_vy * 0.8 + dy * 200 * dt
        else:
            player_vx *= 0.9
            player_vy *= 0.9
        player_x += player_vx * dt
        player_y += player_vy * dt
        player_x = max(20, min(W - 20, player_x))
        player_y = max(20, min(H - 20, player_y))

        # Score / EXP
        score += 0.1
        exp_val = min(1.0, (score % 100) / 100)
        exp_bar.set_progress(exp_val)
        mana_bar.set_progress(max(0, mana_bar.get_progress() - 0.002))

    # Update particles
    for p in particles[:]:
        p["x"] += p["vx"]
        p["y"] += p["vy"]
        p["vx"] *= 0.96
        p["vy"] *= 0.96
        p["life"] -= dt * 1.5
        if p["life"] <= 0:
            particles.remove(p)

    # Update HUD
    hp_bar.update()
    mana_bar.update()
    exp_bar.update()
    dash_cd.update()
    shield_cd.update()

    screen = pygame.display.get_surface()
    screen.fill((20, 22, 30))

    # Draw scene
    if transitioning:
        scene_a = pygame.Surface((W, H))
        scene_a.fill((20, 22, 30))
        scene_b = pygame.Surface((W, H))
        scene_b.fill((35, 25, 35))

        runner.update(dt)
        if runner.done_out:
            scene_color = (scene_color + 1) % 2
            runner.start_in(0.5)
        runner.render(screen, scene_a, scene_b)
        if runner.done:
            transitioning = False
            runner.reset()
    else:
        # Floor grid
        for y in range(0, H, 40):
            for x in range(0, W, 40):
                shade = 30 + ((x + y) // 40) % 2 * 8
                pygame.draw.rect(screen, (shade, shade + 2, shade + 5), (x, y, 40, 40), 1)

        # Particles
        for p in particles:
            alpha = int(p["life"] * 255)
            c = (200, 150, int(p["life"] * 200))
            pygame.draw.circle(screen, c, (int(p["x"]), int(p["y"])), int(3 * p["life"] + 1))

        # Player
        pygame.draw.circle(screen, (100, 200, 255), (int(player_x), int(player_y)), 12)
        pygame.draw.circle(screen, (180, 230, 255), (int(player_x), int(player_y)), 10)

    # HUD (rendered on top even during transitions)
    hp_bar.render(screen, (20, 15))
    mana_bar.render(screen, (20, 40))
    exp_bar.render(screen, (20, 58))

    dash_cd.render(screen, (20, 85))
    shield_cd.render(screen, (68, 85))

    # Styled text (outline + shadow + multiline)
    title_surf = outline(font, "pygkit Showcase", (220, 220, 255), (30, 30, 50), 2)
    screen.blit(title_surf, (W // 2 - title_surf.get_width() // 2, H - 70))

    score_surf = shadow(small, f"Score: {int(score)}", (180, 220, 180), (20, 30, 20), (1, 1))
    screen.blit(score_surf, (W - 150, 15))

    fps_surf = shadow(small, f"FPS: {clock.get_fps():.0f}", (140, 140, 160), (10, 10, 15), (1, 1))
    screen.blit(fps_surf, (W - 150, 32))

    instr_surf = render_multiline(
        small, "Arrows: move | D/S: cooldowns | T: transition | Q: quit",
        (130, 130, 150), max_width=600, align="center",
    )
    screen.blit(instr_surf, (20, H - 22))

    pygame.display.flip()

pygame.quit()
