import pygame
import pytest

from pygkit.ui import CooldownOverlay
from pygkit.utils import Timer


def test_update_ticks_timer():
    timer = Timer(2.0)
    overlay = CooldownOverlay(timer, 48)
    overlay.update(0.5)
    assert timer.elapsed() == pytest.approx(0.5)
    assert timer.reached() is False
    overlay.update(1.5)
    assert timer.reached() is True


def test_padded_overlay_renders():
    timer = Timer(2.0)
    overlay = CooldownOverlay(
        timer, 48, padding_x=6, padding_y=6, border_width=2, border_radius=4
    )
    screen = pygame.Surface((200, 200))
    overlay.update(0.5)
    overlay.render(screen, (0, 0))
    assert timer.elapsed() == pytest.approx(0.5)


def test_invalid_size_rejected():
    with pytest.raises(ValueError):
        CooldownOverlay(Timer(1.0), 0)


def test_icon_not_mutated():
    timer = Timer(2.0, start_finished=True)
    icon = pygame.Surface((16, 16), pygame.SRCALPHA)
    icon.fill((255, 0, 0, 255))
    before = icon.get_alpha()
    overlay = CooldownOverlay(timer, 32, icon=icon)
    screen = pygame.Surface((200, 200))
    overlay.render(screen, (0, 0))
    assert icon.get_alpha() == before
