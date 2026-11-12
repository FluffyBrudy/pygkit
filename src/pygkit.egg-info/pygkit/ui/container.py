from typing import List, Tuple

from pygame import Surface

from .base import UIBase


class Container:
    def __init__(self) -> None:
        self.children: List[Tuple[UIBase, Tuple[int, int]]] = []

    def add(self, child: UIBase, pos: Tuple[int, int] = (0, 0)) -> None:
        self.children.append((child, pos))

    def update(self) -> None:
        for child, _ in self.children:
            child.update()

    def render(self, screen: Surface) -> None:
        for child, offset in self.children:
            child.render(screen, offset)
