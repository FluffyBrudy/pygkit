"""One public style model and one resolution pipeline for pygkit UI.

:UIStyle is a plain dict schema (CSS-inspired): shareable, themable, and
never mutated by widgets. The schema covers *appearance only* — geometry
(width, padding, ``border_width``) stays in :class:`pygkit.ui.UIOptions`.
Positioning is owned entirely by the layout that applies it; ``UIStyle``
never carries position keys.

Schema::

    style = {
        "bg": "#262432",                       # background (or None)
        "fg": "#ffffff",                       # content ink (text/fill)
        "gradient": ("#353348", "#171923"),    # vertical, top → bottom
        "border": "#433f56",                   # border color (with UIOptions border_width)
        "radius": 12,                          # corner radius (draw only)
        "shadow": (0, 3, "#00000040"),         # dx, dy, color
        "hover":   {"gradient": ("#45435c", "#262432")},  # partial override
        "pressed": {"bg": "#171923"},
        "disabled": {"gradient": None},        # explicit kill
        "selected": {"border": "#8ab4ff"},    # app-controlled toggle/tab state
    }

Resolution: per-widget ``DEFAULT_STYLE`` → user style → active state
override, each layer honoring only the keys it specifies (partial state
dicts inherit unspecified properties). Button state priority is
``disabled > pressed > hover > selected > normal``. ``selected`` is an
application-controlled persistent state; the other Button states follow
interaction. A state may kill the gradient
only by writing ``"gradient": None``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict, TypeAlias

from pygame import Surface
from pygame.typing import ColorLike as PygameColorLike

__all__ = [
    "ColorLike",
    "GradientLike",
    "ShadowLike",
    "StateKey",
    "STATE_KEYS",
    "SKIN_STATE_KEYS",
    "StatePaint",
    "ResolvedStyle",
    "UIStyle",
    "Skin",
    "validate_style",
    "resolve_style",
]

ColorLike: TypeAlias = PygameColorLike
Skin: TypeAlias = "dict[str, Surface]"
GradientLike: TypeAlias = "tuple[ColorLike, ColorLike]"
ShadowLike: TypeAlias = "tuple[int, int, ColorLike]"
StateKey: TypeAlias = Literal["normal", "hover", "pressed", "disabled", "selected"]
STATE_KEYS: tuple[StateKey, ...] = ("normal", "hover", "pressed", "disabled", "selected")
SKIN_STATE_KEYS: tuple[StateKey, ...] = ("normal", "hover", "pressed", "disabled")

_PAINT_KEYS = ("bg", "fg", "gradient", "border", "radius", "shadow", "offset_y")
_STATE_KEYS = ("hover", "pressed", "disabled", "selected")


class StatePaint(TypedDict, total=False):
    """Paint properties allowed in a style or in one state override.

    Restricted subset: a state override may *not* nest further states
    (``style.hover.pressed`` is a validation error).
    """

    bg: ColorLike
    fg: ColorLike
    gradient: GradientLike | None
    border: ColorLike
    radius: int
    shadow: ShadowLike | None
    offset_y: int


class UIStyle(StatePaint, total=False):
    """One public style model shared by every widget.

    Plain dict data: never mutated by pygkit, safe to share across
    widgets, and state overrides are per-property partial.
    """

    hover: StatePaint
    pressed: StatePaint
    disabled: StatePaint
    selected: StatePaint


@dataclass(frozen=True, slots=True)
class ResolvedStyle:
    """Fully resolved, color-normalized style for one widget state.

    Built once per (style, state) and cached on the widget; every field
    is concrete (colors as RGBA tuples) so the chrome engine can key its
    caches on these values directly.
    """

    bg: tuple[int, int, int, int] | None
    fg: tuple[int, int, int, int] | None
    gradient: "tuple[tuple[int, int, int, int], tuple[int, int, int, int]] | None"
    border: tuple[int, int, int, int] | None
    radius: int
    shadow: "tuple[int, int, tuple[int, int, int, int]] | None"
    offset_y: int


def _as_color(value: object, path: str) -> tuple[int, int, int, int]:
    """Normalize a ColorLike to an RGBA tuple with a path-aware error."""
    try:
        from pygame import Color

        color = Color(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(f"{path}: invalid color {value!r} ({exc})") from exc
    return (color.r, color.g, color.b, color.a)


def validate_style(
    style: object, path: str = "style", *, _allow_states: bool = True
) -> None:
    """Validate one style dict (and its state overrides) strictly.

    Raises:
        ValueError: unknown keys, nested states, or malformed values —
            errors name the offending path, e.g. ``style.hover.gradient``.
    """
    if style is None:
        raise ValueError(f"{path}: style must be a dict, got None")
    if not isinstance(style, dict):
        raise ValueError(f"{path}: style must be a dict, got {type(style).__name__}")
    for key, value in style.items():
        if key in _STATE_KEYS:
            if not _allow_states:
                raise ValueError(f"{path}.{key}: state overrides cannot nest states")
            validate_style(value, f"{path}.{key}", _allow_states=False)
            continue
        if key not in _PAINT_KEYS:
            raise ValueError(f"{path}.{key}: unknown style key {key!r}")
        _validate_value(key, value, f"{path}.{key}")


def _validate_value(key: str, value: object, path: str) -> None:
    if key in ("bg", "fg", "border"):
        if value is None:
            raise ValueError(f"{path}: color cannot be None")
        _as_color(value, path)
    elif key == "gradient":
        if value is None:
            return
        if (
            not isinstance(value, tuple)
            or len(value) != 2
        ):
            raise ValueError(f"{path}: gradient must be a (top, bottom) pair or None")
        _as_color(value[0], f"{path}[0]")
        _as_color(value[1], f"{path}[1]")
    elif key == "shadow":
        if value is None:
            return
        if not isinstance(value, tuple) or len(value) != 3 or not isinstance(value[0], int) or not isinstance(value[1], int):
            raise ValueError(f"{path}: shadow must be (dx, dy, color) or None")
        _as_color(value[2], f"{path}[2]")
    elif key == "radius":
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"{path}: radius must be a non-negative int")
    elif key == "offset_y":
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{path}: offset_y must be an int")


def _paint_of(
    layer: dict, path: str, *, allow_states: bool = True
) -> dict[str, object]:
    """Validated paint keys of one layer (top-level style or a state)."""
    validate_style(layer, path, _allow_states=allow_states)
    return {k: v for k, v in layer.items() if k in _PAINT_KEYS}


def resolve_style(
    style: UIStyle,
    state: StateKey = "normal",
    defaults: UIStyle | None = None,
) -> ResolvedStyle:
    """Resolve one concrete :class:`ResolvedStyle` for ``state``.

    Merge order: ``defaults`` (widget-type theme) → ``style`` → the
    active state override. Layers contribute only keys they specify, so
    partial state dicts inherit unspecified properties deterministically.

    Raises:
        ValueError: on invalid style data (from :func:`validate_style`).
    """
    merged: dict[str, object] = {}
    if defaults:
        merged.update(_paint_of(defaults, "DEFAULT_STYLE"))
        if state in _STATE_KEYS:
            default_state = defaults.get(state)
            if default_state:
                merged.update(
                    _paint_of(
                        default_state,
                        f"DEFAULT_STYLE.{state}",
                        allow_states=False,
                    )
                )
    if style:
        merged.update(_paint_of(style, "style"))
        if state in _STATE_KEYS:
            layer = style.get(state)
            if layer:
                merged.update(
                    _paint_of(layer, f"style.{state}", allow_states=False)
                )

    bg = merged.get("bg")
    fg = merged.get("fg")
    gradient = merged.get("gradient")
    border = merged.get("border")
    shadow = merged.get("shadow")
    return ResolvedStyle(
        bg=_as_color(bg, "style.bg") if bg is not None else None,
        fg=_as_color(fg, "style.fg") if fg is not None else None,
        gradient=(
            (_as_color(gradient[0], "style.gradient[0]"), _as_color(gradient[1], "style.gradient[1]"))
            if gradient is not None
            else None
        ),
        border=_as_color(border, "style.border") if border is not None else None,
        radius=int(merged.get("radius", 0) or 0),
        shadow=(
            (int(shadow[0]), int(shadow[1]), _as_color(shadow[2], "style.shadow[2]"))
            if shadow is not None
            else None
        ),
        offset_y=int(merged.get("offset_y", 0) or 0),
    )


def select_state_key(
    state: StateKey,
    *,
    enabled: bool = True,
    armed: bool = False,
    hovered: bool = False,
    selected: bool = False,
) -> StateKey:
    """Deterministic Button state selection.

    ``pressed`` is the transient pointer-down state. ``selected`` is an
    application-controlled persistent state for toggles, tabs, and menus.
    """
    if not enabled:
        return "disabled"
    if armed:
        return "pressed"
    if hovered:
        return "hover"
    if selected:
        return "selected"
    return state
