import pytest

from pygkit.ui.theming import resolve_style, validate_style


def test_resolver_merges_default_and_user_layers_in_documented_order():
    defaults = {
        "bg": "#101010",
        "fg": "#ffffff",
        "gradient": ("#202020", "#000000"),
        "hover": {"border": "#445566", "offset_y": -1},
    }
    style = {
        "bg": "#112233",
        "gradient": None,
        "hover": {"fg": "#abcdef"},
    }
    resolved = resolve_style(style, "hover", defaults)
    assert resolved.bg == (17, 34, 51, 255)
    assert resolved.gradient is None
    assert resolved.border == (68, 85, 102, 255)
    assert resolved.fg == (171, 205, 239, 255)
    assert resolved.offset_y == -1


def test_user_base_beats_default_active_state_but_user_state_wins_last():
    defaults = {"bg": "#111111", "hover": {"bg": "#222222"}}
    user = {"bg": "#333333", "hover": {"bg": "#444444"}}
    assert resolve_style(user, "hover", defaults).bg == (68, 68, 68, 255)
    assert resolve_style({"bg": "#333333"}, "hover", defaults).bg == (51, 51, 51, 255)


def test_explicit_state_gradient_none_kills_inherited_gradient():
    resolved = resolve_style(
        {"gradient": ("#ffffff", "#000000"), "hover": {"gradient": None}},
        "hover",
    )
    assert resolved.gradient is None


def test_selected_is_a_valid_application_controlled_style_state():
    resolved = resolve_style(
        {"bg": "#111111", "selected": {"bg": "#224488"}}, "selected"
    )
    assert resolved.bg == (34, 68, 136, 255)


@pytest.mark.parametrize(
    ("style", "path"),
    [
        ({"not_a_style_key": 1}, "style.not_a_style_key"),
        ({"hover": {"pressed": {}}}, "style.hover.pressed"),
        ({"hover": {"gradient": ("#fff",)}}, "style.hover.gradient"),
        ({"shadow": (0, "down", "#000")}, "style.shadow"),
        ({"radius": -1}, "style.radius"),
    ],
)
def test_validation_errors_name_the_bad_style_path(style, path):
    with pytest.raises(ValueError, match=path):
        validate_style(style)


def test_skin_importable_from_package():
    from pygkit.ui import Skin

    assert Skin is not None
