import pygame
import pytest

from pygkit.ui.button import Button


@pytest.fixture
def font():
    return pygame.font.Font(None, 22)


def _render(button, pos=(0, 0)):
    screen = pygame.Surface((400, 120), pygame.SRCALPHA)
    button.render(screen, pos)
    return screen


def test_text_button_auto_sizes_and_reflows(font):
    button = Button(font, "Go", padding_x=8)
    initial_width = button.size[0]
    button.set_text("A much longer label")
    assert button.size[0] > initial_width
    assert button.box_model["full_width"] == button.size[0]


def test_icon_button_accounts_for_icon_gap_and_label(font):
    icon = pygame.Surface((24, 16), pygame.SRCALPHA)
    button = Button(font, "Go", image=icon, icon_gap=7)
    text_width, text_height = font.size("Go")
    assert button.size == (24 + 7 + text_width, max(16, text_height))


def test_click_fires_only_after_press_on_same_button(font):
    button = Button(font, "Go")
    seen = []
    button.on_press.connect(lambda pressed: seen.append(pressed.text))
    _render(button, (10, 10))
    assert button.press((15, 15))
    assert button.activate((15, 15))
    assert seen == ["Go"]
    assert not button.activate((15, 15))


def test_disabled_button_never_arms(font):
    button = Button(font, "Go", enabled=False)
    _render(button, (10, 10))
    assert not button.press((15, 15))
    assert not button.activate((15, 15))


def test_shared_style_is_not_mutated(font):
    style = {"bg": (60, 0, 0, 255), "gradient": None, "radius": 4}
    before = {**style}
    first = Button(font, "One", style=style)
    second = Button(font, "Two", style=style)
    _render(first)
    _render(second)
    assert style == before
    assert first.style is not style
    assert second.style is not style


def test_default_hover_state_changes_procedural_chrome(font):
    button = Button(font, "", width=80, height=40)
    screen = _render(button, (10, 10))
    point = (50, 45)
    normal = screen.get_at(point)
    button._hovered = True
    screen = _render(button, (10, 10))
    assert screen.get_at(point) != normal


def test_user_base_style_overrides_default_active_state(font):
    button = Button(
        font,
        "",
        width=80,
        height=40,
        style={"gradient": None, "bg": (80, 10, 10, 255)},
    )
    button._hovered = True
    screen = _render(button, (10, 10))
    assert screen.get_at((50, 45))[:3] == (80, 10, 10)


def test_user_state_style_overrides_user_base_style(font):
    button = Button(
        font,
        "",
        width=80,
        height=40,
        style={
            "gradient": None,
            "bg": (80, 10, 10, 255),
            "hover": {"bg": (10, 80, 10, 255)},
        },
    )
    button._hovered = True
    screen = _render(button, (10, 10))
    assert screen.get_at((50, 45))[:3] == (10, 80, 10)


def test_disabled_state_has_priority_over_pressed_and_hover(font):
    button = Button(
        font,
        "",
        width=80,
        height=40,
        style={
            "gradient": None,
            "bg": (10, 10, 10, 255),
            "hover": {"bg": (10, 20, 30, 255)},
            "pressed": {"bg": (20, 30, 40, 255)},
            "disabled": {"bg": (30, 40, 50, 255)},
        },
        enabled=False,
    )
    button._hovered = True
    button._armed = True
    assert button._skin_state() == "disabled"
    assert _render(button, (10, 10)).get_at((50, 45))[:3] == (30, 40, 50)


def test_selected_is_persistent_and_lower_priority_than_pointer_states(font):
    button = Button(
        font,
        "",
        width=80,
        height=40,
        selected=True,
        style={
            "gradient": None,
            "bg": (10, 10, 10, 255),
            "selected": {"bg": (20, 30, 40, 255)},
            "hover": {"bg": (30, 40, 50, 255)},
            "pressed": {"bg": (40, 50, 60, 255)},
        },
    )
    assert button.selected
    assert button._skin_state() == "selected"
    assert _render(button, (10, 10)).get_at((50, 45))[:3] == (20, 30, 40)

    button._hovered = True
    assert button._skin_state() == "hover"
    button._armed = True
    assert button._skin_state() == "pressed"

    button._armed = False
    button._hovered = False
    _render(button, (10, 10))
    assert button.press((15, 15))
    assert button.activate((15, 15))
    assert button.selected  # Button never toggles selection by itself.
    button.set_selected(False)
    assert not button.selected


def test_selected_skin_uses_normal_frame(font):
    frames = {}
    for state, color in {
        "normal": (10, 20, 30, 255),
        "hover": (40, 50, 60, 255),
        "pressed": (70, 80, 90, 255),
        "disabled": (100, 110, 120, 255),
    }.items():
        frame = pygame.Surface((80, 40), pygame.SRCALPHA)
        frame.fill(color)
        frames[state] = frame
    button = Button(font, "", width=80, height=40, images=frames, selected=True)
    _render(button)
    assert button._skin_state() == "selected"
    assert button.local_surface.get_at((40, 20))[:3] == (10, 20, 30)


def test_skinned_corners_stay_transparent_no_chrome_leak(font):
    """Skin frames provide their own chrome; nothing paints beneath them.

    Rounded-corner art must keep its transparent corners — engine chrome
    under the frames would bleed through as a colored backing.
    """
    frames = {}
    for state, color in {
        "normal": (10, 20, 30, 255),
        "hover": (40, 50, 60, 255),
        "pressed": (70, 80, 90, 255),
        "disabled": (100, 110, 120, 255),
    }.items():
        frame = pygame.Surface((80, 40), pygame.SRCALPHA)
        frame.fill((0, 0, 0, 0))
        pygame.draw.rect(frame, color, (0, 0, 80, 40), border_radius=14)
        frames[state] = frame
    button = Button(font, "", width=80, height=40, images=frames)
    screen = _render(button)
    # Procedural chrome (a 40x40 default or any bg color) would cover the
    # corner; a correct skin-only path leaves full alpha transparency.
    assert screen.get_at((0, 0))[3] == 0
    assert screen.get_at((79, 39))[3] == 0
    # Interior stays art-backed.
    assert screen.get_at((40, 20))[:3] == (10, 20, 30)


def test_set_selected_requires_bool(font):
    with pytest.raises(TypeError, match="selected must be bool"):
        Button(font, "Go").set_selected(1)  # type: ignore[arg-type]


def test_explicit_gradient_none_uses_flat_background(font):
    button = Button(
        font,
        "",
        width=80,
        height=40,
        style={"gradient": None, "bg": (90, 0, 0, 255)},
    )
    screen = _render(button, (10, 10))
    assert screen.get_at((50, 45))[:3] == (90, 0, 0)
    assert not button._gradient_cache


def test_state_foregrounds_render_distinct_cached_labels(font):
    button = Button(
        font,
        "Go",
        style={"fg": (255, 0, 0, 255), "hover": {"fg": (0, 255, 0, 255)}},
    )
    _render(button)
    button._hovered = True
    _render(button)
    assert set(button._labels) == {"normal", "hover"}


def test_style_replacement_clears_caches_and_changes_render(font):
    button = Button(font, "", width=80, height=40)
    before = _render(button, (10, 10)).get_at((50, 45))
    assert button._gradient_cache
    button.set_style({"gradient": None, "bg": (0, 90, 0, 255)})
    assert not button._gradient_cache
    after = _render(button, (10, 10)).get_at((50, 45))
    assert after != before
    assert after[:3] == (0, 90, 0)


def test_shadow_is_cached_and_opt_in(font):
    button = Button(
        font,
        "",
        width=80,
        height=40,
        style={
            "gradient": None,
            "bg": (20, 20, 20, 255),
            "shadow": (0, 2, (0, 0, 0, 120)),
        },
    )
    _render(button, (10, 10))
    assert len(button._shadow_cache) == 1
    cached = next(iter(button._shadow_cache.values()))
    _render(button, (10, 10))
    assert next(iter(button._shadow_cache.values())) is cached


def test_masked_skin_hit_testing(font):
    frame = pygame.Surface((80, 40), pygame.SRCALPHA)
    pygame.draw.rect(frame, (100, 100, 100, 255), (5, 0, 70, 40), border_radius=8)
    skin = {state: frame.copy() for state in ("normal", "hover", "pressed", "disabled")}
    mask = pygame.mask.from_surface(frame)
    button = Button(
        font,
        "",
        width=80,
        height=40,
        images=skin,
        hit_masks={state: mask for state in skin},
    )
    _render(button, (10, 10))
    assert not button.contains((10, 10))
    assert button.contains((50, 30))


def test_contains_false_before_first_render(font):
    """Un-laid-out buttons can't be hit: no phantom clicks at the origin."""
    hits = []
    button = Button(font, "Go")
    button.on_press.connect(lambda b: hits.append("go"))
    assert button.contains((10, 10)) is False
    assert button.press((10, 10)) is False
    assert button.activate((10, 10)) is False
    assert button._armed is False
    assert hits == []
    # After the first render (origin recorded), the same point hits.
    _render(button, (10, 10))
    assert button.contains((11, 11)) is True
