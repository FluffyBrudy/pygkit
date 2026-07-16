"""
Signal system demo — interactively demonstrates Signal, SignalBus, and the signal descriptor.
"""

import pygame
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pygkit.signals import SignalBus, signal


class Player:
    on_hit = signal()
    on_heal = signal()
    on_level_up = signal()

    def __init__(self):
        self.hp = 100
        self.max_hp = 100
        self.level = 1
        self.exp = 0

    def hit(self, damage):
        self.hp = max(0, self.hp - damage)
        self.on_hit(self.hp, damage)

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)
        self.on_heal(self.hp, amount)

    def gain_exp(self, amount):
        self.exp += amount
        if self.exp >= self.level * 50:
            self.exp = 0
            self.level += 1
            self.on_level_up(self.level)


def main():
    pygame.init()
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Signal Demo")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)

    player = Player()
    bus = SignalBus()
    game_over_sig = bus.create_signal("game_over")
    score_sig = bus.create_signal("score_changed")
    score = 0

    log = []

    def log_msg(msg):
        log.append(msg)
        if len(log) > 10:
            log.pop(0)

    player.on_hit += lambda hp, dmg: log_msg(f"Hit for {dmg}! HP: {hp}")
    player.on_heal += lambda hp, amt: log_msg(f"Healed {amt}! HP: {hp}")
    player.on_level_up += lambda lv: log_msg(f"Level up! Now level {lv}")

    score_sig.connect(lambda pts: log_msg(f"Score: {pts}"))
    game_over_sig.connect(lambda: log_msg("GAME OVER"))

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    player.hit(10 + player.level * 5)
                elif event.key == pygame.K_j:
                    player.heal(15)
                elif event.key == pygame.K_k:
                    player.gain_exp(30)
                elif event.key == pygame.K_s:
                    score += 100
                    bus.emit("score_changed", score)
                elif event.key == pygame.K_g:
                    bus.emit("game_over")
                elif event.key == pygame.K_c:
                    log.clear()
                elif event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((20, 20, 30))

        title = font.render("Signal Demo", True, (255, 255, 255))
        screen.blit(title, (20, 15))

        controls = [
            "H - hit player",
            "J - heal player",
            "K - gain exp / level up",
            "S - add score",
            "G - game over",
            "C - clear log",
            "ESC - quit",
        ]
        for i, line in enumerate(controls):
            surf = small_font.render(line, True, (160, 160, 180))
            screen.blit(surf, (20, 55 + i * 22))

        bar_x, bar_y, bar_w, bar_h = 20, 220, 400, 22
        hp_ratio = player.hp / player.max_hp
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        bar_color = (200, 40, 40) if hp_ratio > 0.3 else (255, 200, 0) if hp_ratio > 0.15 else (255, 50, 50)
        pygame.draw.rect(screen, bar_color, (bar_x, bar_y, int(bar_w * hp_ratio), bar_h))

        exp_ratio = player.exp / (player.level * 50)
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y + 28, bar_w, 8))
        pygame.draw.rect(screen, (100, 180, 255), (bar_x, bar_y + 28, int(bar_w * exp_ratio), 8))

        stats = small_font.render(
            f"HP: {player.hp}/{player.max_hp}   Lv.{player.level}   EXP: {player.exp}/{player.level * 50}   Score: {score}",
            True, (200, 200, 220),
        )
        screen.blit(stats, (bar_x, bar_y + bar_h + 6))

        for i, msg in enumerate(reversed(log)):
            surf = small_font.render(msg, True, (100, 200, 255))
            screen.blit(surf, (20, 290 + i * 22))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
