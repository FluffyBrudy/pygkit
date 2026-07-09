from typing import Protocol

from pygame import Surface


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
