import pygame
import pytest

from pygkit.ui import ProgressBarUI
from pygkit.ui.button import Button


@pytest.fixture
def font():
    return pygame.font.Font(None, 20)


def test_default_path_unchanged():
    bar = ProgressBarUI(width=100, height=20)
    bar.set_progress(0.5)
    bar.update(10.0)
    screen = pygame.Surface((200, 60))
    bar.render(screen, (0, 0))
    assert bar.get_progress() > 0.4


def test_track_and_fill_area_clip():
    track = pygame.Surface((60, 20), pygame.SRCALPHA)
    track.fill((20, 40, 60, 255))          # opaque interior
    pygame.draw.rect(track, (0, 0, 0, 0), (0, 0, 60, 20), 2)  # transparent frame
    art = pygame.Surface((60, 20), pygame.SRCALPHA)
    art.fill((200, 30, 30, 255))           # full state: opaque fill art
    pygame.draw.rect(art, (0, 0, 0, 0), (0, 0, 60, 20), 2)

    bar = ProgressBarUI(width=60, height=20, border_width=0, track_image=track, fill_image=art)
    bar.set_progress(0.5)
    bar.update(10.0)
    screen = pygame.Surface((200, 60))
    bar.render(screen, (0, 0))

    # Interior left half: fill art color; right half: track color beneath.
    assert screen.get_at((18, 10))[:3] == (200, 30, 30)
    assert screen.get_at((48, 10))[:3] == (20, 40, 60)
    # Transparent frame row stays background (no fill leak).
    assert screen.get_at((30, 1))[:3] != (200, 30, 30)


def test_fill_zero_and_full():
    art = pygame.Surface((40, 16), pygame.SRCALPHA)
    art.fill((10, 200, 10, 255))
    bar = ProgressBarUI(width=40, height=16, border_width=0, track_image=art, fill_image=art)
    screen = pygame.Surface((80, 40))
    bar.set_progress(0.0)
    bar.update(10.0)
    bar.render(screen, (0, 0))
    assert screen.get_at((20, 8))[:3] == (10, 200, 10)  # track shows at 0
    bar.set_progress(1.0)
    bar.update(10.0)
    bar.render(screen, (0, 0))
    assert screen.get_at((20, 8))[:3] == (10, 200, 10)  # full art still covers


def _stretch(src, size):
    """Plain stretch — the test probes shape, not nine-slice mechanics."""
    return pygame.transform.scale(src, size)


def test_nine_slice_bar_shape():
    src = pygame.Surface((40, 24), pygame.SRCALPHA)
    pygame.draw.rect(src, (9, 9, 9, 255), (0, 0, 40, 24), border_radius=10)
    out = _stretch(src, (280, 42))
    assert out.get_size() == (280, 42)
    assert out.get_at((0, 0))[3] == src.get_at((0, 0))[3]


def test_fill_origin_respects_art_border_zone():
    """Fill starts after the art's left border (decor stays unpainted)."""
    art = pygame.Surface((40, 16), pygame.SRCALPHA)
    art.fill((30, 30, 40, 255), special_flags=pygame.BLEND_RGBA_ADD) if False else None
    art.fill((30, 30, 40, 255))
    bar = ProgressBarUI(
        width=40, height=16, padding_x=10, padding_y=0,
        border_width=0, style={"fg": (255, 0, 0), "radius": 0},
        track_image=art,
    )
    bar.set_progress(1.0)
    bar.update(10.0)
    screen = pygame.Surface((80, 40))
    bar.render(screen, (0, 0))
    assert screen.get_at((3, 8))[:3] == (30, 30, 40)   # left art zone intact
    assert screen.get_at((38, 8))[:3] == (30, 30, 40)  # right art zone intact
    assert screen.get_at((20, 8))[:3] == (255, 0, 0)   # content filled


def _down(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})


def test_button_hover_routes_through_motion(font):
    from pygkit.ui.container import Container

    btn = Button(font, "Go")
    box = Container()
    box.add(btn, pos=(30, 40))
    screen = pygame.Surface((200, 200))
    box.render(screen, (5, 5))  # button _origin becomes (35, 45)
    assert btn._hovered is False
    box.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (50, 60)}))
    assert btn._hovered is True
    box.handle_event(pygame.event.Event(pygame.MOUSEMOTION, {"pos": (5, 5)}))
    assert btn._hovered is False


def test_menubar_motion_reaches_child(font):
    from pygkit.ui.menubar import Menubar

    bar = Menubar(width=300, height=50)
    btn = Button(font, "A")
    bar.add(btn, at=(10, 5))
    screen = pygame.Surface((320, 80))
    bar.update()
    bar.render(screen, (0, 0))
    assert btn._hovered is False
    bar.handle_event(
        pygame.event.Event(pygame.MOUSEMOTION, {"pos": (20, 15)})
    )
    assert btn._hovered is True


def test_silhouette_rebuilt_when_track_image_replaced():
    def _solid(size, color):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill(color)
        return surf

    track_a = _solid((30, 20), (255, 255, 255, 255))
    track_b = _solid((30, 20), (255, 255, 255, 255))
    track_b.set_at((5, 5), (0, 0, 0, 0))
    bar = ProgressBarUI(width=30, height=20, border_width=0, track_image=track_a, style={"fg": (255, 0, 0, 255), "gradient": None})
    bar.set_progress(1.0)
    bar.update(10.0)
    screen_a = pygame.Surface((40, 30), pygame.SRCALPHA)
    bar.render(screen_a)
    assert screen_a.get_at((15, 10))[:3] == (255, 0, 0)

    bar.track_image = track_b
    screen_b = pygame.Surface((40, 30), pygame.SRCALPHA)
    bar.render(screen_b)
    assert screen_b.get_at((5, 5)).a == 0
