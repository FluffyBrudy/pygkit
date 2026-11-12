"""
Styled UI demo — pure dict-style ("{}") chrome on core widgets.

Everything here is data: one UIStyle dict drives the gradient plaque
buttons (hover/pressed/disabled state partials), a gradient panel, and
procedural progress bars. No asset packs — see the skin-packer branch
for image-skin flows.

Keys: SPACE reset/toggle fills, R reset, Q/Esc quit.

Run headless smoke:  python style_demo.py --frames 90
Headless shot:       python style_demo.py --frames 12 --shot /tmp/shot.png
"""

import argparse
import os

import pygame

from pygkit.ui import (
    AnchorLayout,
    Button,
    Panel,
    ProgressBarUI,
    UIStyle,
    ResolvedStyle,
)

W, H = 640, 400

# One shared style: background buttons all read from it; widgets never
# mutate it, so reuse across widgets is safe.
DARK_TEAL: UIStyle = {
    "fg": "#fef9f4",
    "gradient": ("#353348", "#171923"),
    "border": "#433f56",
    "radius": 12,
    "shadow": (0, 3, (0, 0, 0, 64)),
    "hover": {"gradient": ("#45435c", "#262432")},
    "pressed": {"bg": "#171923", "offset_y": 2},
    "disabled": {"gradient": None, "bg": (30, 30, 36, 255)},
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=int, default=0)
    parser.add_argument("--shot", type=str, default="", help="save frame 10 PNG here")
    args = parser.parse_args()

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("pygkit style demo — pure UIStyle")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 26)
    small = pygame.font.Font(None, 16)

    start = Button(font, "Start", style=DARK_TEAL, padding_x=20, padding_y=0)
    resume = Button(font, "Resume", style=DARK_TEAL, padding_x=16, padding_y=2)
    # Style reuse: one change, every widget that shares the data updates.
    shared = dict(DARK_TEAL)
    levels = Button(font, "Levels", style=shared, padding_x=16, padding_y=2)
    bar = ProgressBarUI(width=280, height=22, style={"fg": (120, 220, 255)})
    bar2 = ProgressBarUI(width=280, height=22, style={"fg": (255, 120, 170)})
    bar.set_progress(0.72)
    bar2.set_progress(0.45)

    hud = AnchorLayout(pygame.Rect(0, 0, W, H))
    back_panel = Panel(width=340, height=300, style={"bg": (18, 34, 30, 255), "radius": 14})
    hud.add(back_panel, anchor="center")
    hud.add(bar, anchor="midtop", offset=(0, 60))
    hud.add(bar2, anchor="midtop", offset=(0, 100))
    hud.add(start, anchor="midtop", offset=(0, 140))
    hud.add(resume, anchor="center", offset=(0, 90))
    hud.add(levels, anchor="center", offset=(0, 140))

    hits: list[str] = []
    start.on_press.connect(lambda _b: hits.append("start"))
    resume.on_press.connect(lambda _b: hits.append("resume"))
    levels.on_press.connect(lambda _b: hits.append("levels"))

    count = 0
    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_q, pygame.K_ESCAPE):
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                on = bar.get_progress() < 0.1
                bar.set_progress(0.72 if on else 0.0)
                bar2.set_progress(0.45 if on else 0.0)
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP) and event.button == 1:
                hud.handle_event(event)
            elif event.type == pygame.MOUSEMOTION:
                hud.handle_event(event)

        bar.update(dt)
        bar2.update(dt)
        hud.update(dt)

        screen.fill((20, 22, 30))
        hud.render(screen)
        screen.blit(
            small.render(f"clicked: {hits[-1] if hits else '-'}", True, (160, 160, 180)),
            (24, 12),
        )
        pygame.display.flip()

        count += 1
        if args.shot and count == 10:
            pygame.image.save(screen, args.shot)
        if args.frames and count >= args.frames:
            running = False
    pygame.quit()


if __name__ == "__main__":
    main()
