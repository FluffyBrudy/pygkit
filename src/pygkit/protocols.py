from typing import Any, Protocol, runtime_checkable

from pygame import Surface

from .signals import Signal


class Renderable(Protocol):
    def render(self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)): ...

    def update(self): ...


class UIElement(Protocol):
    def render(self, screen: Surface): ...

    def update(self): ...

    @property
    def size(self) -> tuple[int, int]: ...

    @property
    def pos(self) -> tuple[int, int]: ...


class Drawable(Protocol):
    def draw(self, surface: Surface): ...


class Updateable(Protocol):
    def update(self): ...


@runtime_checkable
class Widget(Renderable, Protocol):
    @property
    def size(self) -> tuple[int, int]: ...


class Clickable(Widget, Protocol):
    # contains/press/activate take screen coords; widgets track origin at render.

    on_press: Signal[Any]

    def contains(self, pos: tuple[int, int]) -> bool: ...

    def press(self, pos: tuple[int, int]) -> bool: ...

    def activate(self, pos: tuple[int, int]) -> bool: ...
