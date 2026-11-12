import pygame

from pygkit.ui import Container, CooldownOverlay
from pygkit.utils import Timer


class TestContainer:
    def test_update_propagates_without_ticking_readonly_children(self):
        timer = Timer(1.0)
        overlay = CooldownOverlay(timer, 32)
        box = Container()
        box.add(overlay, pos=(0, 0))
        assert timer.elapsed() == 0.0
        box.update(0.5)
        assert timer.elapsed() == 0.0
        timer.update(1.0)
        assert timer.reached() is True

    def test_size_covers_children(self):
        timer = Timer(1.0)
        overlay = CooldownOverlay(timer, 32)
        box = Container()
        assert box.size == (0, 0)
        box.add(overlay, pos=(10, 20))
        w, h = overlay.size
        assert box.size == (10 + w, 20 + h)

    def test_remove(self):
        timer = Timer(1.0)
        overlay = CooldownOverlay(timer, 32)
        box = Container()
        box.add(overlay, pos=(0, 0))
        assert box.remove(overlay) is True
        assert box.remove(overlay) is False
        assert box.size == (0, 0)


class TestContainerLayout:
    def test_render_applies_offsets(self):
        import pygame

        from pygkit.ui.button import Button

        font = pygame.font.Font(None, 20)
        btn = Button(font, "Go")
        box = Container()
        box.add(btn, pos=(30, 40))
        screen = pygame.Surface((400, 400))
        box.render(screen, (5, 5))
        assert btn._origin == (35, 45)

    def test_handle_event_routes_to_child(self):
        import pygame

        from pygkit.ui.button import Button

        font = pygame.font.Font(None, 20)
        hits = []
        btn = Button(font, "Go")
        btn.on_press.connect(lambda b: hits.append(True))
        box = Container()
        box.add(btn, pos=(30, 40))
        screen = pygame.Surface((400, 400))
        box.render(screen, (5, 5))
        down = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (37, 47), "button": 1}
        )
        up = pygame.event.Event(
            pygame.MOUSEBUTTONUP, {"pos": (37, 47), "button": 1}
        )
        assert box.handle_event(down) is True
        assert box.handle_event(up) is True
        assert hits == [True]


class TestContainerHoverOcclusion:
    """Hover must be cleared on lower siblings when a topmost child wins MOUSEMOTION."""

    def _motion(self, pos):
        return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos})

    def test_lower_button_hover_cleared_by_overlapping_upper(self):
        """Moving into an overlap zone: the lower button loses hover."""
        font = pygame.font.Font(None, 20)
        from pygkit.ui.button import Button

        # Two 40x20 buttons placed at the same position so they overlap entirely.
        lower = Button(font, "Lo", width=40, height=20)
        upper = Button(font, "Hi", width=40, height=20)
        box = Container()
        box.add(lower, pos=(0, 0))
        box.add(upper, pos=(0, 0))

        screen = pygame.Surface((80, 40))
        # Render so origins are recorded.
        box.render(screen, (0, 0))

        # Hover over the shared region — upper wins, lower should be cleared.
        box.handle_event(self._motion((10, 10)))
        assert upper._hovered is True
        assert lower._hovered is False

    def test_hover_clears_when_pointer_moves_from_lower_to_upper_overlap(self):
        """Lower button was hovered first; entering the upper overlap clears it."""
        font = pygame.font.Font(None, 20)
        from pygkit.ui.button import Button

        # lower occupies x 0-59, upper occupies x 40-99 — they overlap at x 40-59.
        lower = Button(font, "A", width=60, height=30)
        upper = Button(font, "B", width=60, height=30)
        box = Container()
        box.add(lower, pos=(0, 0))
        box.add(upper, pos=(40, 0))

        screen = pygame.Surface((120, 40))
        box.render(screen, (0, 0))

        # First hover over the lower-only region.
        box.handle_event(self._motion((10, 15)))
        assert lower._hovered is True
        assert upper._hovered is False

        # Move into the overlap — upper now wins; lower must be cleared.
        box.handle_event(self._motion((50, 15)))
        assert upper._hovered is True
        assert lower._hovered is False

    def test_clear_hover_propagates_through_nested_container(self):
        """clear_hover descends into nested Container children."""
        font = pygame.font.Font(None, 20)
        from pygkit.ui.button import Button

        inner_btn = Button(font, "Inner", width=40, height=20)
        inner_box = Container()
        inner_box.add(inner_btn, pos=(0, 0))

        outer_box = Container()
        outer_box.add(inner_box, pos=(0, 0))

        screen = pygame.Surface((80, 40))
        outer_box.render(screen, (0, 0))
        # Manually set hovered so we can observe the clear.
        inner_btn._hovered = True
        inner_btn._origin = (0, 0)
        inner_btn._origin_valid = True

        outer_box.clear_hover()
        assert inner_btn._hovered is False
