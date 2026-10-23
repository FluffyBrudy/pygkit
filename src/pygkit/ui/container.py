"""Composable groups of widgets with cached local layout positions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pygame
from pygame import Surface

from ..protocols import Widget


@dataclass
class _Child:
    widget: Widget
    placement: Any
    position: tuple[int, int] = (0, 0)


class Container:
    """Content-sized group with explicit child positions.

    Positions are local to this container. Negative positions may overflow
    its reported size without increasing it.
    """

    def __init__(self) -> None:
        self._child_records: list[_Child] = []
        self._layout_dirty = True
        self._size_snapshot: tuple[tuple[int, int], ...] = ()
        self._settings_snapshot: object = None

    def add(
        self, child: Widget, *, pos: tuple[int, int] = (0, 0)
    ) -> Widget:
        """Add ``child`` at a position relative to this container."""
        self._append_child(child, pos)
        return child

    def _append_child(self, child: Widget, placement: Any) -> int:
        if not isinstance(child, Widget):
            raise TypeError(
                f"{type(self).__name__}.add() needs render/update/size, "
                f"got {type(child).__name__}"
            )
        self._child_records.append(_Child(child, placement))
        self._layout_dirty = True
        return len(self._child_records) - 1

    def _child_count(self) -> int:
        return len(self._child_records)

    def _child_at(self, index: int) -> Widget:
        return self._child_records[index].widget

    def _placement_at(self, index: int) -> Any:
        return self._child_records[index].placement

    def _set_placement(self, index: int, placement: Any) -> None:
        self._child_records[index].placement = placement
        self._layout_dirty = True

    def _set_position(self, index: int, position: tuple[int, int]) -> None:
        self._child_records[index].position = position

    def _index_of(self, child: Widget) -> int | None:
        return next(
            (
                index
                for index, entry in enumerate(self._child_records)
                if entry.widget is child
            ),
            None,
        )

    def _layout_settings(self) -> object:
        """Return values that affect placement; subclasses may override."""
        return None

    def _resolve_layout(self) -> None:
        for index in range(self._child_count()):
            self._set_position(index, self._resolve_position(index))

    def _resolve_position(self, index: int) -> tuple[int, int]:
        return self._placement_at(index)

    def _ensure_layout(self) -> None:
        sizes = tuple(
            self._child_at(i).size for i in range(self._child_count())
        )
        settings = self._layout_settings()
        if (
            self._layout_dirty
            or sizes != self._size_snapshot
            or settings != self._settings_snapshot
        ):
            self._resolve_layout()
            self._size_snapshot = sizes
            self._settings_snapshot = settings
            self._layout_dirty = False

    @property
    def children(self) -> list[tuple[Widget, tuple[int, int]]]:
        """Return a snapshot of children and their resolved local positions."""
        self._ensure_layout()
        return [
            (entry.widget, entry.position) for entry in self._child_records
        ]

    def relayout(self) -> None:
        """Invalidate cached positions; child size changes are detected too."""
        self._layout_dirty = True
        self._ensure_layout()

    def remove(self, child: Widget) -> bool:
        index = self._index_of(child)
        if index is None:
            return False
        del self._child_records[index]
        self._layout_dirty = True
        return True

    @property
    def size(self) -> tuple[int, int]:
        self._ensure_layout()
        return (
            max(
                (
                    entry.position[0] + entry.widget.size[0]
                    for entry in self._child_records
                ),
                default=0,
            ),
            max(
                (
                    entry.position[1] + entry.widget.size[1]
                    for entry in self._child_records
                ),
                default=0,
            ),
        )

    def handle_event(self, event: pygame.event.Event) -> bool:
        self._ensure_layout()
        if event.type not in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            return False
        if getattr(event, "button", None) != 1:
            return False
        method_name = (
            "press" if event.type == pygame.MOUSEBUTTONDOWN else "activate"
        )
        for entry in reversed(self._child_records):
            method = getattr(entry.widget, method_name, None)
            if method is not None and method(event.pos):
                return True
            route = getattr(entry.widget, "handle_event", None)
            if route is not None and route(event):
                return True
        return False

    def update(self, dt: float = 0.0) -> None:
        self._ensure_layout()
        for entry in self._child_records:
            entry.widget.update(dt)

    def render(
        self, screen: Surface, pos_offset: tuple[int, int] = (0, 0)
    ) -> None:
        self._ensure_layout()
        for entry in self._child_records:
            position = entry.position
            entry.widget.render(
                screen,
                (position[0] + pos_offset[0], position[1] + pos_offset[1]),
            )
