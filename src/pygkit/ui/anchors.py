from __future__ import annotations

from pygame import Rect

ANCHORS = (
    "topleft",
    "midtop",
    "topright",
    "midleft",
    "center",
    "midright",
    "bottomleft",
    "midbottom",
    "bottomright",
)


def anchor_point(rect: Rect, anchor: str) -> tuple[int, int]:
    if anchor not in ANCHORS:
        raise ValueError(f"unknown anchor {anchor!r}; pick from {list(ANCHORS)}")
    point = getattr(rect, anchor)
    return (point[0], point[1])


def place(
    size: tuple[int, int],
    within: Rect,
    anchor: str = "topleft",
    dx: int = 0,
    dy: int = 0,
) -> Rect:
    rect = Rect((0, 0), (max(0, size[0]), max(0, size[1])))
    ax, ay = anchor_point(within, anchor)
    setattr(rect, anchor, (ax + dx, ay + dy))
    return rect


def row(
    sizes: list[tuple[int, int]],
    *,
    gap: int = 0,
    origin: tuple[int, int] = (0, 0),
) -> list[Rect]:
    rects: list[Rect] = []
    x = origin[0]
    for w, h in sizes:
        rects.append(Rect(x, origin[1], max(0, w), max(0, h)))
        x += max(0, w) + gap
    return rects


def column(
    sizes: list[tuple[int, int]],
    *,
    gap: int = 0,
    origin: tuple[int, int] = (0, 0),
) -> list[Rect]:
    rects: list[Rect] = []
    y = origin[1]
    for w, h in sizes:
        rects.append(Rect(origin[0], y, max(0, w), max(0, h)))
        y += max(0, h) + gap
    return rects


def grid(
    count: int,
    cols: int,
    cell: tuple[int, int],
    *,
    gap: int = 0,
    origin: tuple[int, int] = (0, 0),
) -> list[Rect]:
    if cols <= 0:
        raise ValueError(f"cols must be > 0, got {cols}")
    cw, ch = max(0, cell[0]), max(0, cell[1])
    return [
        Rect(origin[0] + (i % cols) * (cw + gap), origin[1] + (i // cols) * (ch + gap), cw, ch)
        for i in range(max(0, count))
    ]
