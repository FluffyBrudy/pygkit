import pygame
import pytest

from pygkit.ui import Button, CooldownOverlay, DialogBox, Menubar, Panel, ProgressBarUI
from pygkit.ui.base import UIBase
from pygkit.utils import Timer


@pytest.fixture
def font():
    return pygame.font.Font(None, 22)


def _solid(size, color):
    image = pygame.Surface(size, pygame.SRCALPHA)
    image.fill(color)
    return image


def test_background_image_is_inside_content_and_below_border():
    widget = UIBase(
        {"width": 30, "height": 30, "padding_x": 2, "padding_y": 2, "border_width": 2},
        style={"border": (255, 255, 255), "radius": 8},
        background_image=_solid((4, 4), (240, 20, 20, 255)),
    )
    screen = pygame.Surface((40, 40), pygame.SRCALPHA)
    widget.render(screen, (5, 5))
    # Border remains the topmost chrome layer and padding is left untouched.
    assert screen.get_at((5, 20))[:3] == (255, 255, 255)
    assert screen.get_at((8, 20))[3] == 0
    assert screen.get_at((20, 20))[:3] == (240, 20, 20)
    # The rounded content mask removes image pixels from its corners.
    assert screen.get_at((9, 9))[3] == 0


def test_background_image_cache_reuses_then_replaces_derived_surface():
    first = _solid((8, 8), (255, 0, 0, 255))
    widget = UIBase({"width": 20, "height": 20}, background_image=first)
    screen = pygame.Surface((30, 30), pygame.SRCALPHA)
    widget.render(screen)
    cached = next(iter(widget._background_image_cache.values()))
    widget.render(screen)
    assert next(iter(widget._background_image_cache.values())) is cached

    second = _solid((8, 8), (0, 255, 0, 255))
    widget.set_background_image(second)
    assert not widget._background_image_cache
    widget.render(screen)
    assert screen.get_at((10, 10))[:3] == (0, 255, 0)


def test_panel_background_image_is_clipped_by_polygon_and_content_rect():
    polygon = [(5, 0), (25, 0), (30, 5), (30, 25), (25, 30), (5, 30), (0, 25), (0, 5)]
    panel = Panel(
        width=30,
        height=30,
        polygon=polygon,
        outline_width=0,
        content_rect=pygame.Rect(2, 2, 26, 26),
        style={"gradient": None, "bg": (0, 0, 0, 0)},
        background_image=_solid((4, 4), (255, 0, 0, 255)),
    )
    screen = pygame.Surface((40, 40), pygame.SRCALPHA)
    panel.render(screen, (5, 5))
    assert screen.get_at((20, 20))[:3] == (255, 0, 0)
    assert screen.get_at((5, 5))[3] == 0
    assert screen.get_at((6, 20))[3] == 0  # outside the content rect


def test_cooldown_icon_uses_shared_circular_content_clip():
    overlay = CooldownOverlay(
        Timer(1.0, start_finished=True),
        40,
        icon=_solid((10, 10), (10, 200, 40, 255)),
        style={"radius": 20},
    )
    screen = pygame.Surface((50, 50), pygame.SRCALPHA)
    overlay.render(screen, (5, 5))
    assert screen.get_at((5, 5))[3] == 0
    assert screen.get_at((25, 25))[:3] == (10, 200, 40)


def test_background_image_is_supported_by_public_widgets():
    image = _solid((8, 8), (100, 120, 140, 255))
    font = pygame.font.Font(None, 18)
    widgets = [
        Button(font, "Go", background_image=image),
        Panel(width=30, height=20, background_image=image),
        ProgressBarUI(width=30, height=20, background_image=image),
        Menubar(width=30, height=20, background_image=image),
        DialogBox(background_image=image),
    ]
    screen = pygame.Surface((800, 300), pygame.SRCALPHA)
    for widget in widgets:
        widget.render(screen)


def test_button_skin_remains_above_generic_background_image():
    font = pygame.font.Font(None, 18)
    frames = {
        state: _solid((30, 20), (10, 30, 220, 255))
        for state in ("normal", "hover", "pressed", "disabled")
    }
    button = Button(
        font,
        "",
        width=30,
        height=20,
        images=frames,
        background_image=_solid((8, 8), (240, 20, 20, 255)),
    )
    screen = pygame.Surface((40, 30), pygame.SRCALPHA)
    button.render(screen)
    assert screen.get_at((15, 10))[:3] == (10, 30, 220)


def test_progress_track_art_remains_above_generic_background_image():
    track = _solid((30, 20), (10, 30, 220, 255))
    bar = ProgressBarUI(
        width=30,
        height=20,
        border_width=0,
        track_image=track,
        background_image=_solid((8, 8), (240, 20, 20, 255)),
    )
    bar.set_progress(0.0)
    bar.update(10.0)
    screen = pygame.Surface((40, 30), pygame.SRCALPHA)
    bar.render(screen)
    assert screen.get_at((15, 10))[:3] == (10, 30, 220)


def test_button_icon_stays_visible_above_opaque_skin(font):
    skin = {
        state: _solid((30, 20), (10, 30, 220, 255))
        for state in ("normal", "hover", "pressed", "disabled", "selected")
    }
    icon = _solid((6, 6), (0, 200, 0, 255))
    button = Button(font, "", width=30, height=20, images=skin, image=icon)
    screen = pygame.Surface((40, 30), pygame.SRCALPHA)
    button.render(screen)
    assert screen.get_at((15, 10))[:3] == (10, 30, 220)
    assert screen.get_at((5, 5))[:3] == (0, 200, 0)


def test_skinned_button_paints_background_image_under_skin(font):
    skin = {
        state: _solid((30, 20), (0, 0, 0, 0))
        for state in ("normal", "hover", "pressed", "disabled", "selected")
    }
    button = Button(
        font,
        "",
        width=30,
        height=20,
        images=skin,
        background_image=_solid((30, 20), (240, 20, 20, 255)),
    )
    screen = pygame.Surface((40, 30), pygame.SRCALPHA)
    button.render(screen)
    assert screen.get_at((15, 10))[:3] == (240, 20, 20)
