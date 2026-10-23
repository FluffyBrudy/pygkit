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


def test_padding_overrides_apply(font):
    plain = Button(font, "Go")
    padded = Button(font, "Go", padding_x=20, padding_y=10)
    assert padded.size[0] == plain.size[0] + 40
    assert padded.size[1] == plain.size[1] + 20


def test_hitbox_covers_full_box(font):
    btn = Button(font, "Go", padding_x=20, padding_y=10)
    _render(btn, (50, 60))
    w, h = btn.size
    assert btn.contains((51, 61)) is True
    assert btn.contains((50 + w - 1, 60 + h - 1)) is True
    assert btn.contains((49, 60)) is False


def test_gradient_and_shadow_cached(font):
    btn = Button(font, "Go")
    screen = pygame.Surface((400, 100))
    btn.render(screen, (0, 0))
    assert btn._background is not None
    assert btn._shadow is not None
    bg, shadow = btn._background, btn._shadow
    btn.render(screen, (0, 0))
    assert btn._background is bg
    assert btn._shadow is shadow
    # Gradient spans content size and runs top-to-bottom.
    w, h = btn.box_model["content_width"], btn.box_model["content_height"]
    assert bg.get_size() == (max(1, w), max(1, h))
    assert bg.get_at((w // 2, 0))[:3] != bg.get_at((w // 2, h - 1))[:3]


def test_invalidate_clears_cached_layers(font):
    btn = Button(font, "Go")
    _render(btn, (0, 0))
    assert btn._background is not None
    btn.set_text("Other")
    assert btn._background is None
    assert btn._shadow is None


def test_flat_style_disables_gradient(font):
    style = ButtonStyle(gradient_top=None, gradient_bottom=None, shadow_color=None)
    btn = Button(font, "Go", style=style)
    _render(btn, (0, 0))
    assert btn._background is None
    assert btn._shadow is None


def test_explicit_background_uses_flat(font):
    btn = Button(font, "Go", background=(90, 0, 0, 255))
    _render(btn, (0, 0))
    assert btn._background is None
