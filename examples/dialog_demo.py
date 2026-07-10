"""
Dialog System Demo for pygkit.

This example demonstrates the production-grade DialogBox system with:
- Typewriter effect with multiple speed presets
- Customizable colors and transparency
- Speaker name highlighting
- Animated progress indicator
- Word wrapping and multi-line support
"""

import pygame
from pygame import Surface

from pygkit import (
    DialogBox,
    DialogColors,
    DialogConfig,
    TypewriterSpeed,
)


def main() -> None:
    """Run the dialog system demonstration."""
    pygame.init()

    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("pygkit Dialog System Demo")

    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)

    config = DialogConfig(
        width=650,
        height=160,
        padding_x=25,
        padding_y=18,
        border_radius=10,
        border_width=2,
        font_size=22,
        name_font_size=24,
        typewriter_speed=TypewriterSpeed.MEDIUM,
        show_indicator=True,
        indicator_blink_interval=500,
    )

    config.colors.box_background = (54, 68, 60, 200)
    config.colors.box_border = (20, 25, 22, 255)
    config.colors.speaker_name = (251, 224, 83, 255)
    config.colors.dialog_text = (255, 255, 255, 255)
    config.colors.text_outline = (20, 25, 22, 255)
    config.colors.indicator_color = (207, 228, 235, 255)

    dialog = DialogBox(config)

    dialog_x = (screen_width - config.width) // 2
    dialog_y = screen_height - config.height - 20

    dialog_sequence = [
        ("Kryn", "What a strange thing this is..."),
        ("Kryn", "I've never seen anything like it in all my travels."),
        (None, "The ancient artifact hums with an otherworldly energy."),
        ("Kryn", "Perhaps it's best not to touch it. Who knows what might happen?"),
        (
            "System",
            "You feel a mysterious power emanating from the object.",
        ),
        ("Kryn", "Let's leave this place. Something tells me we're not meant to be here."),
    ]

    current_index = 0
    speaker, text = dialog_sequence[current_index]
    dialog.set_dialog(speaker, text)
    
    running = True
    show_speed_demo = False

    speed_help = font.render(
        "Press 1-5: Change speed | Space: Skip/Advance | R: Restart | S: Toggle speed demo",
        True,
        (200, 200, 200),
    )

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if dialog.advance():
                        if current_index < len(dialog_sequence) - 1:
                            current_index += 1
                            speaker, text = dialog_sequence[current_index]
                            dialog.set_dialog(speaker, text)

                elif event.key == pygame.K_r:
                    current_index = 0
                    speaker, text = dialog_sequence[current_index]
                    dialog.set_dialog(speaker, text)

                elif event.key == pygame.K_s:
                    show_speed_demo = not show_speed_demo

                elif event.key == pygame.K_1:
                    dialog.set_typewriter_speed(TypewriterSpeed.EXTRA_FAST)
                elif event.key == pygame.K_2:
                    dialog.set_typewriter_speed(TypewriterSpeed.FAST)
                elif event.key == pygame.K_3:
                    dialog.set_typewriter_speed(TypewriterSpeed.MEDIUM)
                elif event.key == pygame.K_4:
                    dialog.set_typewriter_speed(TypewriterSpeed.SLOW)
                elif event.key == pygame.K_5:
                    dialog.set_typewriter_speed(TypewriterSpeed.EXTRA_SLOW)

        dialog.update(dt)

        screen.fill((30, 35, 40))

        pygame.draw.rect(screen, (60, 70, 80), (100, 200, 150, 150), border_radius=8)
        pygame.draw.rect(screen, (80, 90, 100), (300, 250, 200, 100), border_radius=8)
        pygame.draw.circle(screen, (100, 120, 140), (600, 300), 80)

        dialog.render(screen, (dialog_x, dialog_y))

        screen.blit(speed_help, (10, 10))

        speed_text = font.render(
            f"Current Speed: {dialog.config.typewriter_speed.name}",
            True,
            (251, 224, 83),
        )
        screen.blit(speed_text, (10, 35))

        progress_text = font.render(
            f"Dialog: {current_index + 1}/{len(dialog_sequence)}",
            True,
            (200, 200, 200),
        )
        screen.blit(progress_text, (10, 55))

        if show_speed_demo:
            demo_text = [
                "Speed Demo Mode:",
                "1: EXTRA_FAST (0.015s/char)",
                "2: FAST (0.025s/char)",
                "3: MEDIUM (0.040s/char)",
                "4: SLOW (0.060s/char)",
                "5: EXTRA_SLOW (0.100s/char)",
            ]
            for i, line in enumerate(demo_text):
                color = (255, 255, 255) if i == 0 else (180, 180, 180)
                text_surf = font.render(line, True, color)
                screen.blit(text_surf, (screen_width - 220, 10 + i * 20))

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
