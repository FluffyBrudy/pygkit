"""
Menubar demo — bar with text and image buttons, bool event dispatch.

Needs: pygkit[ui]

Controls:
  mouse click         press buttons (only hits fire)
  Q/Esc               quit

Run headless for a smoke test:  python menubar_demo.py --frames 120
"""

import argparse

import pygame

from pygkit.ui import Button, Menubar

W, H = 640, 160


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=0)
    args = parser.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("pygkit menubar demo")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 24)
    small = pygame.font.Font(None, 16)

    img = pygame.Surface((110, 36), pygame.SRCALPHA)
    img.fill((70, 110, 180, 255))
    pygame.draw.rect(img, (200, 220, 255, 255), img.get_rect(), 2, border_radius=6)

    fired: list[str] = []
    bar = Menubar(width=600, height=56)
    start = Button(font, "start", image=img)
    start.on_press.connect(lambda btn: fired.append("start"))
    settings = Button(font, "settings")
    settings.on_press.connect(lambda btn: fired.append("settings"))
    locked = Button(font, "locked", enabled=False)
    locked.on_press.connect(lambda btn: fired.append("locked-never"))
    bar.add(start, anchor="midleft", dx=12)
    bar.add(settings, anchor="center")
    bar.add(locked, anchor="midright", dx=-12)

    count = 0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False
            else:
                bar.handle_event(event)
        bar.update(dt)

        screen.fill((25, 25, 35))
        bar.render(screen, (20, 20))
        last = fired[-1] if fired else "-"
        screen.blit(small.render(f"last fired: {last}   (click empty space: nothing fires)",
                                 True, (160, 160, 180)), (20, 100))
        pygame.display.flip()
        count += 1
        if args.frames and count >= args.frames:
            running = False
    pygame.quit()


if __name__ == "__main__":
    main()
