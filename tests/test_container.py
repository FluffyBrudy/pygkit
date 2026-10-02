from pygkit.ui import Container, CooldownOverlay
from pygkit.utils import Timer


class TestContainer:
    def test_update_ticks_children(self):
        timer = Timer(1.0)
        overlay = CooldownOverlay(timer, 32)
        box = Container()
        box.add(overlay, (0, 0))
        assert timer.elapsed() == 0.0
        box.update(0.5)
        assert timer.elapsed() == 0.5
        box.update(0.5)
        assert timer.reached() is True

    def test_size_covers_children(self):
        timer = Timer(1.0)
        overlay = CooldownOverlay(timer, 32)
        box = Container()
        assert box.size == (0, 0)
        box.add(overlay, (10, 20))
        w, h = overlay.size
        assert box.size == (10 + w, 20 + h)

    def test_remove(self):
        timer = Timer(1.0)
        overlay = CooldownOverlay(timer, 32)
        box = Container()
        box.add(overlay, (0, 0))
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
        box.add(btn, (30, 40))
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
        box.add(btn, (30, 40))
        screen = pygame.Surface((400, 400))
        box.render(screen, (5, 5))
        down = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, {"pos": (37, 47), "button": 1}
        )
        up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (37, 47), "button": 1})
        assert box.handle_event(down) is True
        assert box.handle_event(up) is True
        assert hits == [True]
