import pygame
import pytest

from pygkit.ui import CooldownOverlay
from pygkit.utils import Timer


def test_update_does_not_tick_timer():
    timer = Timer(2.0)
    overlay = CooldownOverlay(timer, 48)
    overlay.update(0.5)
    assert timer.elapsed() == pytest.approx(0.0)
    assert timer.reached() is False
    timer.update(2.0)
    assert timer.reached() is True


def test_padded_overlay_renders():
    timer = Timer(2.0)
    overlay = CooldownOverlay(
        timer, 48, padding_x=6, padding_y=6, border_width=2, border_radius=4
    )
    screen = pygame.Surface((200, 200))
    timer.update(0.5)
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


def test_circular_icon_masked_to_slot():
    timer = Timer(2.0, start_finished=True)
    icon = pygame.Surface((16, 16), pygame.SRCALPHA)
    icon.fill((255, 0, 0, 255))
    overlay = CooldownOverlay(timer, 48, icon=icon, border_radius=24)
    assert overlay._mask is not None
    assert overlay.icon.get_at((0, 0))[3] == 0
    center = overlay.icon.get_size()[0] // 2, overlay.icon.get_size()[1] // 2
    assert overlay.icon.get_at(center)[3] == 255


def test_square_icon_unmasked():
    timer = Timer(2.0, start_finished=True)
    icon = pygame.Surface((16, 16), pygame.SRCALPHA)
    icon.fill((255, 0, 0, 255))
    overlay = CooldownOverlay(timer, 32, icon=icon)
    assert overlay._mask is None
    assert overlay.icon.get_at((0, 0))[3] == 255


def test_sweep_clipped_to_circle():
    timer = Timer(2.0)  # mid-cooldown sweep visible
    overlay = CooldownOverlay(timer, 48, border_radius=24)
    screen = pygame.Surface((200, 200))
    overlay.render(screen, (0, 0))
    assert overlay.overlay_parent.get_at((0, 0))[3] == 0
