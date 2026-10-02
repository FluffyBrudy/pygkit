from __future__ import annotations

import math

import pygame
from pygame import Surface

MODES = ("tile", "clamp", "once")
ANCHORS = ("top", "bottom", "center")


def _normalize_factor(factor: float | tuple[float, float]) -> tuple[float, float]:
    if isinstance(factor, (int, float)) and not isinstance(factor, bool):
        fx = float(factor)
        fy = 0.0
    else:
        try:
            fx, fy = factor
        except (TypeError, ValueError):
            raise ValueError(f"factor must be a number or (fx, fy) pair, got {factor!r}") from None
        fx, fy = float(fx), float(fy)
    if not math.isfinite(fx) or not math.isfinite(fy):
        raise ValueError(f"factor must be finite, got {(fx, fy)!r}")
    return (fx, fy)


class ParallaxLayer:
    __slots__ = ("image", "factor", "offset", "x_mode", "y_mode", "anchor")

    def __init__(
        self,
        image: Surface,
        factor: float | tuple[float, float] = 0.0,
        x_mode: str = "tile",
        y_mode: str = "clamp",
        anchor: str = "bottom",
        scale: int = 1,
        offset: tuple[float, float] = (0.0, 0.0),
    ) -> None:
        if image is None:
            raise ValueError("image must not be None")
        if x_mode not in MODES:
            raise ValueError(f"x_mode must be one of {MODES}, got {x_mode!r}")
        if y_mode not in MODES:
            raise ValueError(f"y_mode must be one of {MODES}, got {y_mode!r}")
        if anchor not in ANCHORS:
            raise ValueError(f"anchor must be one of {ANCHORS}, got {anchor!r}")
        if not isinstance(scale, int) or isinstance(scale, bool) or scale < 1:
            raise ValueError(f"scale must be an int >= 1, got {scale!r}")
        w, h = image.get_size()
        if w < 1 or h < 1:
            raise ValueError(f"image must be at least 1x1, got {(w, h)!r}")
        if scale > 1:
            image = pygame.transform.scale(image, (w * scale, h * scale))
        try:
            ox, oy = offset
        except (TypeError, ValueError):
            raise ValueError(f"offset must be an (x, y) pair, got {offset!r}") from None
        self.image = image
        self.factor = _normalize_factor(factor)
        self.offset = (float(ox), float(oy))
        self.x_mode = x_mode
        self.y_mode = y_mode
        self.anchor = anchor


def _tile_positions(scroll: float, size: int, screen: int) -> list[int]:
    off = -scroll % size
    pos = off - size
    out = []
    while pos < screen:
        out.append(int(pos))
        pos += size
    return out


def _clamp_position(scroll: float, size: int, screen: int) -> int:
    if size >= screen:
        return int(-min(max(scroll, 0.0), size - screen))
    return 0


def _anchor_position(size: int, screen: int, anchor: str) -> int:
    if anchor == "top":
        return 0
    if anchor == "bottom":
        return screen - size
    return (screen - size) // 2


class ParallaxBackground:
    __slots__ = ("layers",)

    def __init__(self, layers: list[ParallaxLayer] | None = None) -> None:
        self.layers: list[ParallaxLayer] = list(layers) if layers else []

    def add(self, layer: ParallaxLayer) -> ParallaxLayer:
        self.layers.append(layer)
        return layer

    def remove(self, layer: ParallaxLayer) -> bool:
        if layer in self.layers:
            self.layers.remove(layer)
            return True
        return False

    def __len__(self) -> int:
        return len(self.layers)

    def render(self, screen: Surface, cam_x: float, cam_y: float) -> None:
        sw, sh = screen.get_size()
        for layer in self.layers:
            img = layer.image
            w, h = img.get_size()
            fx, fy = layer.factor
            ox, oy = layer.offset
            sx, sy = cam_x * fx - ox, cam_y * fy - oy
            if layer.x_mode == "tile":
                xs = _tile_positions(sx, w, sw)
            elif layer.x_mode == "clamp":
                xs = [_clamp_position(sx, w, sw)]
            else:
                xs = [int(-sx)]
            if layer.y_mode == "tile":
                ys = _tile_positions(sy, h, sh)
            elif layer.y_mode == "clamp":
                if h >= sh:
                    ys = [_clamp_position(sy, h, sh)]
                else:
                    ys = [_anchor_position(h, sh, layer.anchor)]
            else:
                ys = [int(-sy)]
            for x in xs:
                if x + w <= 0 or x >= sw:
                    continue
                for y in ys:
                    if y + h <= 0 or y >= sh:
                        continue
                    screen.blit(img, (x, y))
