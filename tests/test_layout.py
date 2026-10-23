import pygame
import pytest

from pygkit.ui.button import Button
from pygkit.ui.container import Container
from pygkit.ui.layout import AnchorLayout, GridBox, HBox, VBox
from pygkit.ui.anchors import ANCHORS, place


@pytest.fixture
def font():
    return pygame.font.Font(None, 20)


class Stub:
    def __init__(self, w, h):
        self._size = (w, h)

    @property
    def size(self):
        return self._size

    def render(self, screen, pos_offset=(0, 0)):
        pass

    def update(self, dt=0.0):
        pass


def _down(pos):
    return pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1}
    )


def _up(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": 1})


class TestAnchorLayout:
    @pytest.mark.parametrize("anchor", ANCHORS)
    def test_all_nine_anchors(self, anchor):
        within = pygame.Rect(10, 20, 100, 80)
        panel = AnchorLayout(within)
        child = Stub(20, 10)
        panel.add(child, anchor=anchor)
        expected = place(child.size, within, anchor).topleft
        assert panel.children[0][1] == expected

    def test_positions(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 400, 300))
        a = Stub(50, 20)
        b = Stub(50, 20)
        panel.add(a, anchor="topleft")
        panel.add(b, anchor="center")
        assert panel.children[0][1] == (0, 0)
        assert panel.children[1][1] == (175, 140)

    def test_size_is_within(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 400, 300))
        panel.add(Stub(50, 20), anchor="center")
        assert panel.size == (400, 300)

    def test_set_within_moves_children(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 400, 300))
        child = Stub(50, 20)
        panel.add(child, anchor="center")
        panel.set_within(pygame.Rect(0, 0, 200, 100))
        assert panel.children[0][1] == (75, 40)
        assert panel.size == (200, 100)

    def test_relayout_after_child_resize(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 400, 300))
        child = Stub(50, 20)
        panel.add(child, anchor="center")
        child._size = (100, 20)
        assert panel.children[0][1] == (150, 140)

    def test_overflow_allowed(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 100, 100))
        child = Stub(200, 200)
        panel.add(child, anchor="center")
        assert panel.children[0][1] == (-50, -50)

    def test_remove(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 400, 300))
        a = Stub(10, 10)
        panel.add(a, anchor="topleft")
        assert panel.remove(a) is True
        assert panel.remove(a) is False
        assert panel.children == []

    def test_rejects_position_argument(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 100, 100))
        with pytest.raises(TypeError):
            panel.add(Stub(10, 10), pos=(0, 0))

    def test_rejects_anchor_argument(self):
        with pytest.raises(TypeError):
            Container().add(Stub(10, 10), anchor="center")

    def test_bad_anchor(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 100, 100))
        with pytest.raises(ValueError, match="unknown anchor"):
            panel.add(Stub(10, 10), anchor="everywhere")

    def test_rejects_non_widget(self):
        panel = AnchorLayout(pygame.Rect(0, 0, 100, 100))
        with pytest.raises(TypeError):
            panel.add(object(), anchor="center")

    def test_within_copied(self):
        ref = pygame.Rect(0, 0, 100, 100)
        panel = AnchorLayout(ref)
        ref.w = 999
        assert panel.within.width == 100

    def test_click_routing(self, font):
        panel = AnchorLayout(pygame.Rect(0, 0, 400, 300))
        hits = []
        btn = Button(font, "Go")
        btn.on_press.connect(lambda b: hits.append(True))
        panel.add(btn, anchor="topleft", offset=(30, 40))
        screen = pygame.Surface((400, 300))
        panel.render(screen, (5, 5))
        w, h = btn.size
        pos = (5 + 30 + w // 2, 5 + 40 + h // 2)
        assert panel.handle_event(_down(pos)) is True
        assert panel.handle_event(_up(pos)) is True
        assert hits == [True]


class TestHBoxVBox:
    def test_hbox_order(self):
        bar = HBox(origin=(10, 10), gap=4)
        a, b = Stub(50, 20), Stub(30, 20)
        bar.add(a)
        bar.add(b)
        assert bar.children[0][1] == (10, 10)
        assert bar.children[1][1] == (64, 10)

    def test_vbox_order(self):
        col = VBox(origin=(0, 0), gap=5)
        a, b = Stub(50, 20), Stub(50, 30)
        col.add(a)
        col.add(b)
        assert col.children[0][1] == (0, 0)
        assert col.children[1][1] == (0, 25)

    def test_set_origin_gap(self):
        bar = HBox(origin=(0, 0), gap=0)
        bar.add(Stub(10, 10))
        bar.add(Stub(10, 10))
        bar.set_origin((5, 5))
        assert bar.children[0][1] == (5, 5)
        bar.set_gap(10)
        assert bar.children[1][1] == (25, 5)

    def test_relayout_after_resize(self):
        bar = HBox(gap=4)
        a = Stub(10, 10)
        b = Stub(10, 10)
        bar.add(a)
        bar.add(b)
        a._size = (20, 10)
        assert bar.children[1][1] == (24, 0)

    def test_remove(self):
        bar = HBox()
        a = Stub(10, 10)
        b = Stub(10, 10)
        bar.add(a)
        bar.add(b)
        assert bar.remove(a) is True
        assert bar.children[0][0] is b
        assert bar.children[0][1] == (0, 0)
        assert bar.remove(a) is False

    def test_rejects_non_widget(self):
        with pytest.raises(TypeError):
            HBox().add(object())

    def test_pos_arg_rejected(self):
        bar = HBox()
        with pytest.raises(TypeError):
            bar.add(Stub(10, 10), pos=(5, 5))

    def test_click_routing(self, font):
        bar = HBox(origin=(16, 16), gap=8)
        hits = []
        btn = Button(font, "Go")
        btn.on_press.connect(lambda b: hits.append(True))
        bar.add(btn)
        screen = pygame.Surface((400, 200))
        bar.render(screen, (0, 0))
        w, h = btn.size
        pos = (16 + w // 2, 16 + h // 2)
        assert bar.handle_event(_down(pos)) is True
        assert bar.handle_event(_up(pos)) is True
        assert hits == [True]


class TestGridBox:
    def test_bad_cols(self):
        with pytest.raises(ValueError, match="cols"):
            GridBox(0, (40, 30))

    def test_add_row_major(self):
        g = GridBox(cols=2, cell=(40, 30), gap=4, origin=(10, 10))
        cells = [Stub(10, 10) for _ in range(3)]
        for c in cells:
            g.add(c)
        assert g.children[0][1] == (10, 10)
        assert g.children[1][1] == (54, 10)
        assert g.children[2][1] == (10, 44)

    def test_size_full_extent(self):
        g = GridBox(cols=2, cell=(40, 30), gap=4, origin=(10, 10))
        assert g.size == (0, 0)
        g.add(Stub(5, 5))
        assert g.size == (10 + 2 * 40 + 4, 10 + 1 * 30)
        g.add(Stub(5, 5))
        g.add(Stub(5, 5))
        assert g.size == (10 + 2 * 40 + 4, 10 + 2 * 30 + 4)

    def test_set_and_at(self):
        g = GridBox(cols=3, cell=(20, 20))
        a = Stub(5, 5)
        g.set(a, 2, 1)
        assert g.at(2, 1) is a
        assert g.at(0, 0) is None
        assert g.children[0][1] == (20, 40)

    def test_set_out_of_range(self):
        g = GridBox(cols=2, cell=(20, 20))
        with pytest.raises(ValueError):
            g.set(Stub(5, 5), 0, 2)
        with pytest.raises(ValueError):
            g.set(Stub(5, 5), -1, 0)
        with pytest.raises(ValueError):
            g.at(0, 2)

    def test_set_occupied(self):
        g = GridBox(cols=2, cell=(20, 20))
        g.add(Stub(5, 5))
        with pytest.raises(ValueError, match="occupied"):
            g.set(Stub(5, 5), 0, 0)

    def test_set_moves_child(self):
        g = GridBox(cols=2, cell=(20, 20))
        a = Stub(5, 5)
        g.add(a)
        g.set(a, 1, 1)
        assert g.at(0, 0) is None
        assert g.at(1, 1) is a

    def test_remove(self):
        g = GridBox(cols=2, cell=(20, 20))
        a = Stub(5, 5)
        g.add(a)
        assert g.remove(a) is True
        assert g.remove(a) is False
        assert g.size == (0, 0)

    def test_set_cols_shrink_occupied(self):
        g = GridBox(cols=3, cell=(20, 20))
        g.set(Stub(5, 5), 0, 2)
        with pytest.raises(ValueError, match="shrink"):
            g.set_cols(2)
        g.set_cols(4)
        assert g.cols == 4

    def test_set_cell_gap_origin(self):
        g = GridBox(cols=2, cell=(20, 20), gap=0, origin=(0, 0))
        a = Stub(5, 5)
        g.add(a)
        g.add(Stub(5, 5))
        g.set_gap(10)
        assert g.children[1][1] == (30, 0)
        g.set_cell((10, 10))
        assert g.children[1][1] == (20, 0)
        g.set_origin((5, 5))
        assert g.children[0][1] == (5, 5)

    def test_rejects_non_widget(self):
        with pytest.raises(TypeError):
            GridBox(2, (20, 20)).add(object())

    def test_click_routing(self, font):
        g = GridBox(cols=2, cell=(120, 60), gap=0, origin=(0, 0))
        hits = []
        btn = Button(font, "Go")
        btn.on_press.connect(lambda b: hits.append(True))
        g.add(btn)
        screen = pygame.Surface((400, 200))
        g.render(screen, (10, 10))
        w, h = btn.size
        pos = (10 + w // 2, 10 + h // 2)
        assert g.handle_event(_down(pos)) is True
        assert g.handle_event(_up(pos)) is True


def test_nested_container_render_and_event_routing(font):
    outer = Container()
    inner = Container()
    btn = Button(font, "Go")
    hits = []
    btn.on_press.connect(lambda _button: hits.append(True))
    inner.add(btn, pos=(5, 7))
    outer.add(inner, pos=(40, 30))
    outer.render(pygame.Surface((200, 200)), (10, 20))
    assert btn._origin == (55, 57)
    assert outer.handle_event(_down((btn._origin[0] + 1, btn._origin[1] + 1)))
    assert outer.handle_event(_up((btn._origin[0] + 1, btn._origin[1] + 1)))
    assert hits == [True]


def test_anchor_layout_can_place_a_whole_layout():
    bar = HBox(gap=4)
    bar.add(Stub(20, 10))
    bar.add(Stub(30, 10))
    parent = AnchorLayout(pygame.Rect(0, 0, 100, 80))
    parent.add(bar, anchor="bottomright", offset=(-5, -5))
    assert parent.children[0][1] == (41, 65)


def test_content_size_ignores_negative_overflow():
    box = Container()
    box.add(Stub(20, 10), pos=(-8, -4))
    box.add(Stub(12, 5), pos=(6, 3))
    assert box.size == (18, 8)
