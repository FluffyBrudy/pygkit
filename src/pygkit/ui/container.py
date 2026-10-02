from typing import List, Tuple

import pygame
from pygame import Surface

from .base import UIBase


class Container:
    def __init__(self) -> None:
        self.children: List[Tuple[UIBase, Tuple[int, int]]] = []

    def add(self, child: UIBase, pos: Tuple[int, int] = (0, 0)) -> None:
        self.children.append((child, pos))

    def remove(self, child: UIBase) -> bool:
        for i, (entry, _) in enumerate(self.children):
            if entry is child:
                del self.children[i]
                return True
        return False

    @property
    def size(self) -> tuple[int, int]:
        w = 0
        h = 0
        for child, pos in self.children:
            cw, ch = child.size
            w = max(w, pos[0] + cw)
            h = max(h, pos[1] + ch)
        return (w, h)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for child, _ in reversed(self.children):
                press = getattr(child, "press", None)
                if press is not None and press(event.pos):
                    return True
            return False
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            for child, _ in reversed(self.children):
                activate = getattr(child, "activate", None)
                if activate is not None and activate(event.pos):
                    return True
            return False
        return False

    def update(self, dt: float = 0.0) -> None:
        for child, _ in self.children:
            child.update(dt)

    def render(self, screen: Surface, pos_offset: Tuple[int, int] = (0, 0)) -> None:
        for child, offset in self.children:
            child.render(screen, (offset[0] + pos_offset[0], offset[1] + pos_offset[1]))
