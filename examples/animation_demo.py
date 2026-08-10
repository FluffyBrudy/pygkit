"""
pygkit animation demo — one player, two differently sized spritesheets.

Each state owns its own sheet: "idle" uses 32px cells, "run" uses 48px cells,
and both sheets are procedurally generated at startup (no asset files needed).
The sprite is anchored bottom-center so mixed cell sizes stay grounded.

Controls:
  LEFT/RIGHT or A/D   switch idle <-> run
  SPACE               pause/resume
  R                   reset current state
  Q/Esc               quit

Run headless for a smoke test:  python animation_demo.py --frames 120
"""

import argparse
import math
import os
import tempfile

import pygame

from pygkit.animation import AnimationPlayer, AnimationSheet

W, H = 480, 360
GROUND_Y = 300


def build_idle_sheet() -> str:
    """4 frames of a breathing blob on 32x32 cells; returns the saved path."""
    cell = 32
    sheet = pygame.Surface((cell * 4, cell), pygame.SRCALPHA)
    for i in range(4):
        cx = i * cell + cell // 2
        r = 8 + i % 2 * 2
        pygame.draw.circle(sheet, (90, 200, 120), (cx, cell - r - 6), r)
        pygame.draw.circle(sheet, (30, 60, 40), (cx - 3, cell - r - 8), 2)
        pygame.draw.circle(sheet, (30, 60, 40), (cx + 3, cell - r - 8), 2)
    path = os.path.join(tempfile.gettempdir(), "idle_spritesheet.png")
    pygame.image.save(sheet, path)
    return path


def build_run_sheet() -> pygame.Surface:
    """6 frames of a sprinting blob on 48x48 cells (bigger than idle!)."""
    cell = 48
    sheet = pygame.Surface((cell * 6, cell), pygame.SRCALPHA)
    for i in range(6):
        cx = i * cell + cell // 2
        bob = int(math.sin(i / 6 * math.tau) * 5)
        cy = cell - 16 + bob
        pygame.draw.circle(sheet, (240, 140, 70), (cx, cy), 12)
        lean = 6 if i < 3 else -6
        pygame.draw.line(sheet, (240, 140, 70), (cx, cy + 10), (cx + lean, cy + 22), 3)
        pygame.draw.circle(sheet, (40, 20, 10), (cx + lean - 4, cy - 4), 2)
        pygame.draw.circle(sheet, (40, 20, 10), (cx + lean + 4, cy - 4), 2)
    return sheet


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=0, help="quit after N frames (headless smoke test)")
    args = parser.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("pygkit animation demo")
    clock = pygame.time.Clock()
    small = pygame.font.SysFont(None, 16)

    idle_path = build_idle_sheet()
    run_surface = build_run_sheet()

    player = AnimationPlayer(fps=8)
    # idle loads straight from a PNG file, run from an in-memory Surface —
    # both work, and the two grids differ freely in size.
    player.play("idle", AnimationSheet.load(idle_path, rows=1, cols=4))
    player.play("run", AnimationSheet(run_surface, rows=1, cols=6), fps=14)
    player.play("idle")

    frame_count = 0
    running = True
    while running:
        dt_ms = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    running = False
                elif event.key == pygame.K_LEFT:
                    player.play("idle")
                elif event.key == pygame.K_RIGHT:
                    player.play("run")
                elif event.key == pygame.K_SPACE:
                    player.pause() if not player.paused else player.resume()
                elif event.key == pygame.K_r:
                    player.reset()

        player.update(dt_ms)

        screen.fill((24, 26, 34))
        pygame.draw.rect(screen, (46, 52, 66), (0, GROUND_Y, W, H - GROUND_Y))

        img = player.image
        if img is not None:
            screen.blit(img, img.get_rect(midbottom=(W // 2, GROUND_Y)))

        lines = [
            f"state: {player.state}  frame: {player.frame_index}  paused: {player.paused}  finished: {player.finished}",
            f"cell sizes -> idle 32px | run 48px (one player, mixed sheets)",
            "LEFT/RIGHT switch  SPACE pause  R reset",
        ]
        y = 8
        for line in lines:
            text = small.render(line, True, (220, 225, 235))
            screen.blit(text, (8, y))
            y += 18

        pygame.display.flip()

        frame_count += 1
        if args.frames and frame_count >= args.frames:
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()
