"""Optional, single-policy layout containers."""

from __future__ import annotations

from pygame import Rect

from ..protocols import Widget
from .anchors import ANCHORS, place
from .container import Container


class AnchorLayout(Container):
    """Place each child against an explicit local reference rectangle."""

    def __init__(self, within: Rect) -> None:
        super().__init__()
        self.within = Rect(within)

    def add(
        self,
        child: Widget,
        *,
        anchor: str = "topleft",
        offset: tuple[int, int] = (0, 0),
    ) -> Widget:
        """Add a child at one of the nine anchors plus a local offset."""
        if anchor not in ANCHORS:
            raise ValueError(
                f"unknown anchor {anchor!r}; pick from {list(ANCHORS)}"
            )
        self._append_child(child, (anchor, offset))
        return child

    def set_within(self, within: Rect) -> None:
        """Replace the local reference rectangle and invalidate positions."""
        self.within = Rect(within)
        self._layout_dirty = True

    def _layout_settings(self) -> object:
        return tuple(self.within)

    def _resolve_position(self, index: int) -> tuple[int, int]:
        anchor, offset = self._placement_at(index)
        return place(
            self._child_at(index).size,
            self.within,
            anchor,
            *offset,
        ).topleft

    @property
    def size(self) -> tuple[int, int]:
        return self.within.size


class _LinearLayout(Container):
    """Shared flow behavior for horizontal and vertical strips."""

    _axis: str = "row"

    def __init__(
        self, origin: tuple[int, int] = (0, 0), gap: int = 0
    ) -> None:
        super().__init__()
        self.origin = tuple(origin)
        self.gap = gap

    def add(self, child: Widget) -> Widget:
        """Append a child to the flow; placement is managed by this layout."""
        self._append_child(child, None)
        return child

    def _layout_settings(self) -> object:
        return (self._axis, self.origin, self.gap)

    def _resolve_layout(self) -> None:
        x, y = self.origin
        for index in range(self._child_count()):
            self._set_position(index, (x, y))
            width, height = self._child_at(index).size
            if self._axis == "row":
                x += max(0, width) + self.gap
            else:
                y += max(0, height) + self.gap

    def set_origin(self, origin: tuple[int, int]) -> None:
        self.origin = tuple(origin)
        self._layout_dirty = True

    def set_gap(self, gap: int) -> None:
        self.gap = gap
        self._layout_dirty = True


class HBox(_LinearLayout):
    """Horizontal flow layout with a fixed gap between children."""

    _axis = "row"


class VBox(_LinearLayout):
    """Vertical flow layout with a fixed gap between children."""

    _axis = "column"


class GridBox(Container):
    """Fixed-cell grid with explicit slots or row-major automatic insertion."""

    def __init__(
        self,
        cols: int,
        cell: tuple[int, int],
        gap: int = 0,
        origin: tuple[int, int] = (0, 0),
    ) -> None:
        super().__init__()
        if cols <= 0:
            raise ValueError(f"cols must be > 0, got {cols}")
        self._cols = cols
        self._cell = (max(0, cell[0]), max(0, cell[1]))
        self._gap = gap
        self._origin = tuple(origin)

    @property
    def cols(self) -> int:
        return self._cols

    @property
    def cell(self) -> tuple[int, int]:
        return self._cell

    @property
    def gap(self) -> int:
        return self._gap

    @property
    def grid_origin(self) -> tuple[int, int]:
        return self._origin

    def _check_slot(self, row_index: int, col: int) -> None:
        if row_index < 0:
            raise ValueError(f"row must be >= 0, got {row_index}")
        if not 0 <= col < self._cols:
            raise ValueError(f"col must be in [0, {self._cols}), got {col}")

    def _occupied(self) -> set[tuple[int, int]]:
        return {
            self._placement_at(index)
            for index in range(self._child_count())
        }

    def add(self, child: Widget) -> Widget:
        """Add ``child`` to the first free row-major grid slot."""
        occupied = self._occupied()
        row_index = 0
        while True:
            for col in range(self._cols):
                slot = (row_index, col)
                if slot not in occupied:
                    self._append_child(child, slot)
                    return child
            row_index += 1

    def set(self, child: Widget, row: int, col: int) -> Widget:
        """Place or move a child to an unoccupied explicit slot."""
        self._check_slot(row, col)
        target = (row, col)
        for index in range(self._child_count()):
            if (
                self._placement_at(index) == target
                and self._child_at(index) is not child
            ):
                raise ValueError(f"slot ({row}, {col}) is already occupied")
        existing = self._index_of(child)
        if existing is None:
            self._append_child(child, target)
        else:
            self._set_placement(existing, target)
        return child

    def at(self, row: int, col: int) -> Widget | None:
        """Return the widget at ``(row, col)``, or ``None`` if empty."""
        self._check_slot(row, col)
        for index in range(self._child_count()):
            if self._placement_at(index) == (row, col):
                return self._child_at(index)
        return None

    def _layout_settings(self) -> object:
        return (self._cols, self._cell, self._gap, self._origin)

    def _resolve_layout(self) -> None:
        cell_width, cell_height = self._cell
        for index in range(self._child_count()):
            row_index, col = self._placement_at(index)
            self._set_position(
                index,
                (
                    self._origin[0] + col * (cell_width + self._gap),
                    self._origin[1] + row_index * (cell_height + self._gap),
                ),
            )

    def set_cols(self, cols: int) -> None:
        if cols <= 0:
            raise ValueError(f"cols must be > 0, got {cols}")
        if any(col >= cols for _, col in self._occupied()):
            raise ValueError(
                "cannot shrink columns while an occupied slot is outside "
                "the new range"
            )
        self._cols = cols
        self._layout_dirty = True

    def set_cell(self, cell: tuple[int, int]) -> None:
        self._cell = (max(0, cell[0]), max(0, cell[1]))
        self._layout_dirty = True

    def set_gap(self, gap: int) -> None:
        self._gap = gap
        self._layout_dirty = True

    def set_origin(self, origin: tuple[int, int]) -> None:
        self._origin = tuple(origin)
        self._layout_dirty = True

    def remove(self, child: Widget) -> bool:
        removed = super().remove(child)
        if removed:
            self._layout_dirty = True
        return removed

    @property
    def size(self) -> tuple[int, int]:
        if self._child_count() == 0:
            return (0, 0)
        rows = max(row for row, _ in self._occupied()) + 1
        cell_width, cell_height = self._cell
        width = (
            self._origin[0]
            + self._cols * cell_width
            + (self._cols - 1) * self._gap
        )
        height = (
            self._origin[1]
            + rows * cell_height
            + (rows - 1) * self._gap
        )
        return (max(0, width), max(0, height))
