import pygame
import pytest

from pygkit.ui.button import Button, ButtonStyle


@pytest.fixture
def font():
    return pygame.font.Font(None, 22)


def _render(btn, pos=(0, 0)):
    screen = pygame.Surface((400, 100))
    btn.update()
    btn.render(screen, pos)
    return screen


def test_text_fallback_sizing(font):
    btn = Button(font, "Go")
    w, h = btn.size
    assert w > font.size("Go")[0]
    assert h >= font.size("Go")[1]


def test_image_sizing(font):
    img = pygame.Surface((120, 40), pygame.SRCALPHA)
    btn = Button(font, "Go", image=img)
    assert btn.size == (120, 40)


def test_click_fires_only_on_hit(font):
    btn = Button(font, "Go")
    seen = []
    btn.on_press.connect(lambda b: seen.append(b.text))
    _render(btn, (10, 10))
    assert btn.press((15, 15)) is True
    assert btn.activate((15, 15)) is True
    assert seen == ["Go"]


def test_click_without_press_does_not_fire(font):
    btn = Button(font, "Go")
    seen = []
    btn.on_press.connect(lambda b: seen.append(b.text))
    _render(btn, (10, 10))
    assert btn.activate((15, 15)) is False
    assert seen == []


def test_press_off_releases_without_fire(font):
    btn = Button(font, "Go")
    seen = []
    btn.on_press.connect(lambda b: seen.append(b.text))
    _render(btn, (10, 10))
    assert btn.press((15, 15)) is True
    assert btn.activate((300, 90)) is False
    assert seen == []


def test_disabled_never_fires(font):
    btn = Button(font, "Go", enabled=False)
    seen = []
    btn.on_press.connect(lambda b: seen.append(b.text))
    _render(btn, (10, 10))
    assert btn.press((15, 15)) is False
    assert btn.activate((15, 15)) is False
    assert seen == []
    btn.set_enabled(True)
    assert btn.press((15, 15)) is True


def test_style_none_disables_tint(font):
    style = ButtonStyle(hover_tint=None, pressed_tint=None, disabled_tint=None)
    btn = Button(font, "Go", style=style)
    screen = _render(btn, (0, 0))
    assert screen.get_size() == (400, 100)


def test_set_text_rebuilds(font):
    btn = Button(font, "Go")
    _render(btn, (0, 0))
    w_before = btn.size[0]
    btn.set_text("A much longer label")
    assert btn._label is None
    _render(btn, (0, 0))
    assert btn._label is not None
    assert w_before > 0
