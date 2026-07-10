"""
Interactive transitions demo.
Cycles through all transition types. Press SPACE to trigger the next transition.
"""

import pygame

from pygkit.transitions import (
    Crossfade,
    FadeFromBlack,
    FadeToBlack,
    Flash,
    IrisIn,
    IrisOut,
    PixelDissolve,
    Shake,
    Slide,
    TransitionRunner,
)

W, H = 640, 480

pygame.init()
pygame.display.set_mode((W, H))
pygame.display.set_caption("pygkit Transitions Demo")
font = pygame.font.Font(None, 26)
small = pygame.font.Font(None, 18)

clock = pygame.time.Clock()
running = True


def make_scene_surf(color, label, label_color):
    surf = pygame.Surface((W, H))
    surf.fill(color)
    text = font.render(label, True, label_color)
    r = text.get_rect(center=(W // 2, H // 2))
    surf.blit(text, r)
    for y in range(0, H, 40):
        for x in range(0, W, 40):
            pygame.draw.rect(surf, (255, 255, 255, 30), (x, y, 40, 40), 1)
    return surf


scene_a = make_scene_surf((40, 50, 70), "SCENE A", (180, 200, 240))
scene_b = make_scene_surf((70, 40, 50), "SCENE B", (240, 180, 200))

current = scene_a
next_scene = scene_b


transitions_list = [
    ("FadeToBlack + FadeFromBlack", TransitionRunner(FadeToBlack(), FadeFromBlack())),
    ("Crossfade", TransitionRunner(Crossfade(), None)),
    ("Flash", TransitionRunner(Flash(), None)),
    ("IrisIn + IrisOut", TransitionRunner(IrisIn(), IrisOut())),
    ("Slide left", TransitionRunner(Slide("left"), None)),
    ("Slide up", TransitionRunner(Slide("up"), None)),
    ("PixelDissolve", TransitionRunner(PixelDissolve(16), None)),
    ("Shake + Crossfade", TransitionRunner(Shake(intensity=12), Crossfade())),
]

trans_idx = 0
runner = transitions_list[trans_idx][1]
transition_name = transitions_list[trans_idx][0]
triggered = False

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False
            elif event.key == pygame.K_SPACE and not triggered:
                triggered = True
                runner.start_out(0.6)
            elif event.key == pygame.K_RIGHT:
                trans_idx = (trans_idx + 1) % len(transitions_list)
                runner = transitions_list[trans_idx][1]
                transition_name = transitions_list[trans_idx][0]
                triggered = False
                current = scene_a
                next_scene = scene_b
            elif event.key == pygame.K_LEFT:
                trans_idx = (trans_idx - 1) % len(transitions_list)
                runner = transitions_list[trans_idx][1]
                transition_name = transitions_list[trans_idx][0]
                triggered = False
                current = scene_a
                next_scene = scene_b

    screen = pygame.display.get_surface()
    screen.fill((0, 0, 0))

    if triggered:
        runner.update(1 / 60)

        if runner.done_out:
            current, next_scene = next_scene, current
            runner.start_in(0.6)

        runner.render(screen, current, next_scene)

        if runner.done:
            triggered = False
            runner.reset()
    else:
        screen.blit(current, (0, 0))

    marker = "--> "
    names = [f"{marker if i == trans_idx else '     '} {t[0]}" for i, t in enumerate(transitions_list)]
    y = 10
    for i, name in enumerate(names):
        c = (200, 200, 80) if i == trans_idx else (130, 130, 140)
        screen.blit(small.render(name, True, c), (10, y))
        y += 18

    screen.blit(
        small.render("SPACE: trigger  |  LEFT/RIGHT arrow: switch type  |  Q: quit", True, (150, 150, 170)),
        (10, H - 22),
    )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
