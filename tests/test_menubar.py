import pygame
import pytest

from pygkit.ui.button import Button
from pygkit.ui.menubar import Menubar
from pygkit.ui.progressbar import ProgressBarUI


@pytest.fixture
def font():
    return pygame.font.Font(None, 22)


def _down(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})


def _up(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": 1})


def test_add_remove_positions(font):
    bar = Menubar(width=400, height=40)
    a = Button(font, "A")
    b = Button(font, "B")
    bar.add(a, anchor="midleft", dx=8)
    bar.add(b, anchor="midright", dx=-8)
    assert len(bar.entries) == 2
    left_rect = bar.entries[0].rect
    right_rect = bar.entries[1].rect
    assert left_rect.x < right_rect.x
    assert bar.remove(a) is True
    assert bar.remove(a) is False
    assert len(bar.entries) == 1


def test_click_dispatch_topmost_only(font):
    bar = Menubar(width=400, height=40)
    hits = []
    a = Button(font, "A")
    b = Button(font, "B")
    a.on_press.connect(lambda btn: hits.append("a"))
    b.on_press.connect(lambda btn: hits.append("b"))
    bar.add(a, at=(10, 5))
    bar.add(b, at=(10, 5))
    screen = pygame.Surface((400, 60))
    bar.update()
    bar.render(screen, (0, 0))
    assert bar.handle_event(_down((20, 15))) is True
    assert bar.handle_event(_up((20, 15))) is True
    assert hits == ["b"]


def test_miss_returns_false(font):
    bar = Menubar(width=400, height=40)
    hits = []
    a = Button(font, "A")
    a.on_press.connect(lambda btn: hits.append("a"))
    bar.add(a, at=(10, 5))
    screen = pygame.Surface((400, 60))
    bar.update()
    bar.render(screen, (0, 0))
    assert bar.handle_event(_down((300, 30))) is False
    assert bar.handle_event(_up((300, 30))) is False
    assert hits == []
    other = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
    assert bar.handle_event(other) is False


def test_bar_moves_children_ride(font):
    bar = Menubar(width=400, height=40)
    a = Button(font, "A")
    hits = []
    a.on_press.connect(lambda btn: hits.append("a"))
    bar.add(a, at=(10, 5))
    screen = pygame.Surface((500, 100))
    bar.update()
    bar.render(screen, (50, 20))
    assert bar.handle_event(_down((50 + 10 + 5, 20 + 5 + 5))) is True
    assert bar.handle_event(_up((50 + 10 + 5, 20 + 5 + 5))) is True
    assert hits == ["a"]


def test_static_children_render_without_claiming(font):
    bar = Menubar(width=400, height=40)
    static = ProgressBarUI(width=100, height=10)
    bar.add(static, at=(10, 5))
    screen = pygame.Surface((400, 60))
    bar.update()
    bar.render(screen, (0, 0))
    assert bar.handle_event(_down((20, 10))) is False
    assert bar.handle_event(_up((20, 10))) is False


def test_relayout_after_resize(font):
    bar = Menubar(width=400, height=40)
    a = Button(font, "A")
    bar.add(a, anchor="midleft", dx=8)
    first = bar.entries[0].rect.x
    bar.entries[0].anchor = "midright"
    bar.entries[0].dx = -8
    bar.relayout()
    assert bar.entries[0].rect.x > first
    screen = pygame.Surface((400, 60))
    bar.update()
    bar.render(screen, (0, 0))


def test_image_backed_bar(font):
    img = pygame.Surface((300, 50), pygame.SRCALPHA)
    img.fill((40, 40, 60, 255))
    bar = Menubar(image=img)
    assert bar.size == (300, 50)
    a = Button(font, "Go", image=pygame.Surface((80, 30), pygame.SRCALPHA))
    bar.add(a, anchor="center")
    screen = pygame.Surface((300, 60))
    bar.update()
    bar.render(screen, (0, 0))


def test_add_rejects_non_widget(font):
    from pygkit.protocols import Clickable, Widget

    bar = Menubar(width=400, height=40)
    with pytest.raises(TypeError, match="render/update/size"):
        bar.add(object())  # type: ignore[arg-type]
    assert isinstance(Button(font, "A"), Widget)
    assert isinstance(Button(font, "A"), Clickable)
    from pygkit.ui.progressbar import ProgressBarUI

    assert isinstance(ProgressBarUI(width=50, height=10), Widget)
    assert not isinstance(ProgressBarUI(width=50, height=10), Clickable)
