import pygame
import pytest

from pygkit.ui.button import Button
from pygkit.ui.layout import VBox
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


def _motion(pos):
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos})


def test_menubar_hover_occlusion_clears_lower_entry(font):
    """Topmost overlapping button claims hover; lower button must be cleared."""
    bar = Menubar(width=200, height=40)
    lower = Button(font, "Lo", width=60, height=30)
    upper = Button(font, "Hi", width=60, height=30)
    # Both placed at the same absolute position so they overlap fully.
    bar.add(lower, at=(10, 5))
    bar.add(upper, at=(10, 5))

    screen = pygame.Surface((200, 60))
    bar.update()
    bar.render(screen, (0, 0))

    # Motion into the shared region — upper (added later, rendered topmost) wins.
    bar.handle_event(_motion((10 + 5, 5 + 5)))
    assert upper._hovered is True
    assert lower._hovered is False


def test_menubar_hover_clears_when_pointer_enters_overlap(font):
    """Lower button hovered first; moving into the overlap zone clears it."""
    bar = Menubar(width=300, height=40)
    lower = Button(font, "A", width=80, height=30)
    upper = Button(font, "B", width=80, height=30)
    # lower at x=10, upper at x=60 — overlap region is x 60-89 (relative to bar).
    bar.add(lower, at=(10, 5))
    bar.add(upper, at=(60, 5))

    screen = pygame.Surface((300, 60))
    bar.update()
    bar.render(screen, (0, 0))

    # Hover over lower-only region first.
    bar.handle_event(_motion((20, 20)))
    assert lower._hovered is True
    assert upper._hovered is False

    # Move into the overlap — upper wins; lower must be cleared.
    bar.handle_event(_motion((70, 20)))
    assert upper._hovered is True
    assert lower._hovered is False


def test_menubar_clear_hover_clears_all_children(font):
    """Menubar.clear_hover() clears hover on every child entry."""
    bar = Menubar(width=200, height=40)
    a = Button(font, "A", width=50, height=30)
    b = Button(font, "B", width=50, height=30)
    bar.add(a, at=(10, 5))
    bar.add(b, at=(70, 5))

    screen = pygame.Surface((200, 60))
    bar.update()
    bar.render(screen, (0, 0))

    # Manually set both as hovered.
    a._hovered = True
    b._hovered = True

    bar.clear_hover()
    assert a._hovered is False
    assert b._hovered is False


def test_click_routes_through_vbox_child(font):
    """Regression: buttons inside a layout container added to a Menubar
    must fire — Menubar used to dispatch press/activate only, dropping
    clicks on any child without those attributes."""
    bar = Menubar(width=400, height=120)
    vbox = VBox(gap=8, align="center")
    btn = Button(font, "start")
    hits = []
    btn.on_press.connect(lambda b: hits.append("start"))
    vbox.add(btn)
    bar.add(vbox, anchor="midtop", dy=10)
    screen = pygame.Surface((400, 140))
    bar.update()
    bar.render(screen, (0, 0))

    rect = btn._origin
    assert rect[0] > 0  # laid out, not the phantom (0, 0)
    assert bar.handle_event(_down((rect[0] + btn.size[0] // 2, rect[1] + btn.size[1] // 2))) is True
    assert bar.handle_event(_up((rect[0] + btn.size[0] // 2, rect[1] + btn.size[1] // 2))) is True
    assert hits == ["start"]
    # A miss inside the bar (outside the child) reports False.
    assert bar.handle_event(_down((3, 3))) is False
    assert hits == ["start"]


def _container_case(kind, btn):
    import pygame

    from pygkit.ui.container import Container
    from pygkit.ui.layout import AnchorLayout, GridBox, HBox

    if kind == "vbox":
        from pygkit.ui.layout import VBox
        box = VBox(gap=8)
        box.add(btn)
        return box
    if kind == "hbox":
        box = HBox(gap=8)
        box.add(btn)
        return box
    if kind == "grid":
        box = GridBox(cols=1, cell=(btn.size[0] + 4, btn.size[1] + 4))
        box.add(btn)
        return box
    if kind == "anchor":
        box = AnchorLayout(pygame.Rect(0, 0, btn.size[0] + 20, btn.size[1] + 20))
        box.add(btn, anchor="center")
        return box
    if kind == "nested-menubar":
        box = Menubar(width=btn.size[0] + 12, height=btn.size[1] + 12)
        box.add(btn, anchor="center")
        return box
    box = Container()
    box.add(btn, pos=(5, 5))
    return box


@pytest.mark.parametrize(
    "kind", ["vbox", "hbox", "grid", "anchor", "nested-menubar", "plain"]
)
def test_click_routes_through_nested_containers(font, kind):
    bar = Menubar(width=400, height=120)
    btn = Button(font, "go")
    hits = []
    btn.on_press.connect(lambda b: hits.append(kind))
    box = _container_case(kind, btn)
    bar.add(box, anchor="midtop", dy=10)
    screen = pygame.Surface((400, 140))
    bar.update()
    bar.render(screen, (0, 0))
    cx, cy = btn._origin[0] + btn.size[0] // 2, btn._origin[1] + btn.size[1] // 2
    assert bar.handle_event(_down((cx, cy))) is True
    assert bar.handle_event(_up((cx, cy))) is True
    assert hits == [kind]


def test_hover_motion_routes_through_vbox(font):
    bar = Menubar(width=400, height=120)
    vbox = VBox(gap=8)
    first = Button(font, "one")
    second = Button(font, "two")
    vbox.add(first)
    vbox.add(second)
    bar.add(vbox, anchor="midtop", dy=10)
    screen = pygame.Surface((400, 140))
    bar.update()
    bar.render(screen, (0, 0))
    fx, fy = first._origin
    sx, sy = second._origin
    assert bar.handle_event(_motion((fx + first.size[0] // 2, fy + first.size[1] // 2))) is True
    assert first._hovered is True
    # Moving onto the second lights it and clears the first through the
    # shared dispatch policy (hover occlusion within nested containers).
    assert bar.handle_event(_motion((sx + second.size[0] // 2, sy + second.size[1] // 2))) is True
    assert first._hovered is False
    assert second._hovered is True


def test_menubar_relayout_on_child_resize(font):
    """Auto-relayout: entry rects follow child reflow without manual
    relayout() calls."""
    bar = Menubar(width=400, height=60)
    btn = Button(font, "A")
    bar.add(btn, anchor="midleft", dx=8)
    screen = pygame.Surface((400, 60))
    bar.update()
    bar.render(screen, (0, 0))
    before = bar.entries[0].rect.copy()
    btn.set_text("much longer label")  # auto axes reflow, no manual relayout
    bar.update()
    after = bar.entries[0].rect
    assert after.w > before.w
    # New hit region is live: click the grown rect's right side.
    cx = after.x + after.w - 4
    cy = after.y + after.h // 2
    assert btn.contains((cx, cy)) is True


def test_bare_menubar_renders_default_background():
    bar = Menubar(width=200, height=30)
    screen = pygame.Surface((240, 50), pygame.SRCALPHA)
    bar.render(screen, (20, 10))
    assert screen.get_at((40, 20))[:3] == (20, 22, 28)


def test_explicit_style_beats_default():
    bar = Menubar(width=200, height=30, style={"bg": (99, 10, 10, 255), "radius": 0})
    screen = pygame.Surface((240, 50), pygame.SRCALPHA)
    bar.render(screen, (20, 10))
    assert screen.get_at((40, 20))[:3] == (99, 10, 10)
