from pathlib import Path
from typing import List, Tuple, Union

import pygame
from pygame import Surface
from pygame.font import Font


def load_font(
    path: Union[str, Path],
    size: int,
    default_size: int | None = None,
) -> Font:
    if isinstance(path, str):
        path = Path(path)
    try:
        if path.exists():
            return Font(str(path), size)
    except (FileNotFoundError, pygame.error, ValueError):
        pass
    return Font(None, default_size if default_size is not None else size)


def outline(
    font: Font,
    text: str,
    color: tuple[int, int, int],
    outline_color: tuple[int, int, int],
    thickness: int = 1,
) -> Surface:
    base = font.render(text, True, color)
    w = base.get_width() + thickness * 2
    h = base.get_height() + thickness * 2
    surf = Surface((w, h))
    surf.set_colorkey((0, 0, 0))
    surf.fill((0, 0, 0))

    for dx in range(-thickness, thickness + 1):
        for dy in range(-thickness, thickness + 1):
            if dx == 0 and dy == 0:
                continue
            surf.blit(font.render(text, True, outline_color), (thickness + dx, thickness + dy))

    surf.blit(base, (thickness, thickness))
    return surf


def shadow(
    font: Font,
    text: str,
    color: tuple[int, int, int],
    shadow_color: tuple[int, int, int],
    offset: tuple[int, int] = (2, 2),
) -> Surface:
    base = font.render(text, True, color)
    shade = font.render(text, True, shadow_color)

    w = base.get_width() + abs(offset[0])
    h = base.get_height() + abs(offset[1])
    surf = Surface((w, h))
    surf.set_colorkey((0, 0, 0))
    surf.fill((0, 0, 0))

    sx = max(0, offset[0])
    sy = max(0, offset[1])
    surf.blit(shade, (sx, sy))
    bx = max(0, -offset[0])
    by = max(0, -offset[1])
    surf.blit(base, (bx, by))
    return surf


def wrap(
    font: Font,
    text: str,
    max_width: int,
) -> List[str]:
    lines: List[str] = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        current = words[0]
        for word in words[1:]:
            test = f"{current} {word}"
            if font.size(test)[0] <= max_width:
                current = test
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def render_multiline(
    font: Font,
    text: str,
    color: tuple[int, int, int],
    max_width: int | None = None,
    line_spacing: int = 2,
    align: str = "left",
) -> Surface:
    if max_width is not None:
        lines = wrap(font, text, max_width)
    else:
        lines = text.split("\n")

    line_h = font.get_linesize()
    total_h = len(lines) * line_h + (len(lines) - 1) * line_spacing
    max_line_w = max(font.size(l)[0] for l in lines) if lines else 0

    surf = Surface((max_line_w, total_h))
    surf.set_colorkey((0, 0, 0))
    surf.fill((0, 0, 0))

    for i, line in enumerate(lines):
        rendered = font.render(line, True, color)
        x = 0
        if align == "center":
            x = (max_line_w - rendered.get_width()) // 2
        elif align == "right":
            x = max_line_w - rendered.get_width()
        y = i * (line_h + line_spacing)
        surf.blit(rendered, (x, y))

    return surf


def fit(
    font: Font,
    text: str,
    max_width: int,
    max_height: int,
    min_size: int = 8,
) -> int:
    size = font.get_height()
    while size >= min_size:
        try:
            test = Font(font.name, size)
        except FileNotFoundError:
            test = Font(None, size)
        w, h = test.size(text)
        if w <= max_width and h <= max_height:
            return size
        size -= 1
    return min_size
