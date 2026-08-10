from __future__ import annotations

from pathlib import Path
from typing import Union

import pygame
from pygame import Rect, Surface

PathLike = Union[str, Path]


class AnimationSheet:
    """Grid spritesheet for animation: slices an image into rows x cols frames.

    Frames are indexed row-major (left to right, top to bottom). Cell size is
    derived from the image dimensions (``w // cols``, ``h // rows``), so sheets
    of any pixel size can coexist as separate states on one player.
    """

    __slots__ = ("_surface", "_rows", "_cols", "_cell_w", "_cell_h", "_cache")

    def __init__(self, image: Union[PathLike, Surface], rows: int = 1, cols: int = 1) -> None:
        if not isinstance(rows, int) or not isinstance(cols, int) or isinstance(rows, bool) or isinstance(cols, bool):
            raise TypeError("rows and cols must be ints")
        if rows < 1 or cols < 1:
            raise ValueError(f"rows and cols must be >= 1, got rows={rows}, cols={cols}")

        if isinstance(image, Surface):
            surface = image
        else:
            try:
                surface = pygame.image.load(str(image))
            except (pygame.error, FileNotFoundError) as e:
                raise ValueError(f"Failed to load animation sheet {image!r}: {e}") from e
            if pygame.get_init():
                try:
                    surface = surface.convert_alpha()
                except pygame.error:
                    pass

        width, height = surface.get_size()
        cell_w, cell_h = width // cols, height // rows
        if cell_w < 1 or cell_h < 1:
            raise ValueError(f"Sheet {width}x{height} cannot fit a {rows}x{cols} grid")

        self._surface = surface
        self._rows = rows
        self._cols = cols
        self._cell_w = cell_w
        self._cell_h = cell_h
        self._cache: dict[int, Surface] = {}

    @classmethod
    def load(cls, path: PathLike, rows: int = 1, cols: int = 1) -> "AnimationSheet":
        return cls(path, rows, cols)

    @property
    def frame_count(self) -> int:
        return self._rows * self._cols

    @property
    def cell_size(self) -> tuple[int, int]:
        return (self._cell_w, self._cell_h)

    @property
    def rows(self) -> int:
        return self._rows

    @property
    def cols(self) -> int:
        return self._cols

    def get_frame(self, index: int) -> Surface:
        if index < 0 or index >= self.frame_count:
            raise IndexError(f"Frame index {index} out of range for {self.frame_count} frames")
        cached = self._cache.get(index)
        if cached is None:
            col = index % self._cols
            row = index // self._cols
            src = Rect(col * self._cell_w, row * self._cell_h, self._cell_w, self._cell_h)
            cached = self._surface.subsurface(src).copy()
            self._cache[index] = cached
        return cached
