import pygame

from pygkit.ui.panel import Panel


CHAMFER = [(8, 0), (172, 0), (180, 8), (180, 48), (172, 56), (8, 56), (0, 48), (0, 8)]


def test_rectangular_panel_uses_shared_style_engine():
    panel = Panel(
        width=120,
        height=48,
        style={"gradient": None, "bg": (10, 20, 30, 255), "radius": 6},
    )
    screen = pygame.Surface((160, 80), pygame.SRCALPHA)
    panel.render(screen, (10, 10))
    assert panel.size == (120, 48)
    assert screen.get_at((70, 34))[:3] == (10, 20, 30)


def test_polygon_panel_uses_shared_flat_fill_and_border():
    panel = Panel(
        width=180,
        height=56,
        polygon=CHAMFER,
        outline_width=2,
        style={
            "gradient": None,
            "bg": (255, 0, 128, 255),
            "border": (255, 255, 0, 255),
        },
    )
    screen = pygame.Surface((200, 80), pygame.SRCALPHA)
    screen.fill((0, 0, 0, 255))
    panel.render(screen)
    assert screen.get_at((90, 28))[:3] == (255, 0, 128)
    assert screen.get_at((90, 0))[:3] == (255, 255, 0)
    assert screen.get_at((0, 0))[:3] == (0, 0, 0)


def test_polygon_panel_supports_shared_gradient_painting():
    panel = Panel(
        width=180,
        height=56,
        polygon=CHAMFER,
        style={"gradient": ((255, 0, 0), (0, 0, 255))},
    )
    screen = pygame.Surface((200, 80), pygame.SRCALPHA)
    panel.render(screen)
    assert screen.get_at((90, 5)) != screen.get_at((90, 50))


def test_panel_extension_rects_are_preserved():
    content = pygame.Rect(8, 8, 163, 39)
    header = pygame.Rect(0, 0, 180, 12)
    panel = Panel(width=180, height=56, content_rect=content, header_rect=header)
    assert panel.content_rect == content
    assert panel.header_rect == header


def test_polygon_branch_runs_plugins():
    panel = Panel(
        polygon=list(CHAMFER),
        style={"bg": (10, 20, 30, 255), "radius": 0},
    )
    drawn = []
    panel.add_plugin(lambda surf: drawn.append(True))
    screen = pygame.Surface((200, 80), pygame.SRCALPHA)
    panel.render(screen)
    assert drawn == [True]
