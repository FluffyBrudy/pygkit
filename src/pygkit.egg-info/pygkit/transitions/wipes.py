import math
from typing import Callable

from pygame import SRCALPHA, Surface, draw

from ..utils.interpolation import ease_in_out


class _WipeBase:
    __slots__ = ("_easing", "_elapsed", "_duration", "_done", "_mask")

    def __init__(self, easing: Callable[[float], float] = ease_in_out) -> None:
        self._easing = easing
        self._elapsed = 0.0
        self._duration = 0.0
        self._done = False
        self._mask: Surface | None = None

    def start(self, duration: float) -> None:
        self._elapsed = 0.0
        self._duration = duration
        self._done = False

    @property
    def done(self) -> bool:
        return self._done

    def reset(self) -> None:
        self._elapsed = 0.0
        self._duration = 0.0
        self._done = False
        self._mask = None


class IrisIn(_WipeBase):
    """
    Circle closes in from the edges to the center, revealing black (or a color).
    """

    def __init__(
        self,
        color: tuple[int, int, int] = (0, 0, 0),
        easing: Callable[[float], float] = ease_in_out,
    ) -> None:
        super().__init__(easing)
        self._color = color

    def update(self, dt: float) -> None:
        if self._done:
            return
        self._elapsed += dt
        if self._elapsed >= self._duration:
            self._elapsed = self._duration
            self._done = True

    def render(
        self,
        screen: Surface,
        source: Surface | None = None,
        target: Surface | None = None,
    ) -> None:
        if source is not None:
            screen.blit(source, (0, 0))

        w, h = screen.get_size()
        max_radius = int(math.ceil(math.sqrt(w * w + h * h) / 2))

        t = self._easing(self._elapsed / self._duration) if self._duration > 0 else 1.0
        radius = int(max_radius * (1.0 - t))

        if radius <= 0:
            screen.fill(self._color)
            return

        cx, cy = w // 2, h // 2

        if self._mask is None or self._mask.get_size() != (w, h):
            self._mask = Surface((w, h), SRCALPHA)

        self._mask.fill(self._color)
        draw.circle(self._mask, (0, 0, 0, 0), (cx, cy), radius)
        screen.blit(self._mask, (0, 0))


class IrisOut(_WipeBase):
    """
    Circle expands from the center outward, revealing the target.
    """

    def __init__(
        self,
        easing: Callable[[float], float] = ease_in_out,
    ) -> None:
        super().__init__(easing)

    def update(self, dt: float) -> None:
        if self._done:
            return
        self._elapsed += dt
        if self._elapsed >= self._duration:
            self._elapsed = self._duration
            self._done = True

    def render(
        self,
        screen: Surface,
        source: Surface | None = None,
        target: Surface | None = None,
    ) -> None:
        w, h = screen.get_size()
        max_radius = int(math.ceil(math.sqrt(w * w + h * h) / 2))

        t = self._easing(self._elapsed / self._duration) if self._duration > 0 else 1.0
        radius = int(max_radius * t)
        cx, cy = w // 2, h // 2

        if target is not None:
            screen.blit(target, (0, 0))

        if radius < max_radius:
            if self._mask is None or self._mask.get_size() != (w, h):
                self._mask = Surface((w, h), SRCALPHA)

            self._mask.fill((0, 0, 0, 255))
            draw.circle(self._mask, (0, 0, 0, 0), (cx, cy), radius)
            screen.blit(self._mask, (0, 0))


class Slide(_WipeBase):
    """
    Source slides offscreen while target slides in from the opposite side.
    """

    def __init__(
        self,
        direction: str = "left",
    ) -> None:
        super().__init__()
        if direction not in ("left", "right", "up", "down"):
            raise ValueError(
                f"Invalid direction '{direction}'. Must be left, right, up, or down."
            )
        self._direction = direction
        self._buffer: Surface | None = None

    def update(self, dt: float) -> None:
        if self._done:
            return
        self._elapsed += dt
        if self._elapsed >= self._duration:
            self._elapsed = self._duration
            self._done = True

    def render(
        self,
        screen: Surface,
        source: Surface | None = None,
        target: Surface | None = None,
    ) -> None:
        w, h = screen.get_size()
        t = self._elapsed / self._duration if self._duration > 0 else 1.0

        if self._direction == "left":
            out_offset = (-w * t, 0)
            in_offset = (w * (1.0 - t), 0)
        elif self._direction == "right":
            out_offset = (w * t, 0)
            in_offset = (-w * (1.0 - t), 0)
        elif self._direction == "up":
            out_offset = (0, -h * t)
            in_offset = (0, h * (1.0 - t))
        else:
            out_offset = (0, h * t)
            in_offset = (0, -h * (1.0 - t))

        if self._buffer is None or self._buffer.get_size() != (w, h):
            self._buffer = Surface((w, h))

        self._buffer.fill((0, 0, 0))
        if target is not None:
            self._buffer.blit(target, in_offset)
        if source is not None:
            self._buffer.blit(source, out_offset)

        screen.blit(self._buffer, (0, 0))
