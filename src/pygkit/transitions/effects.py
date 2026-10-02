import math
import random
from typing import Callable

from pygame import Surface

from ..utils.interpolation import ease_out
from .base import _check_dt, _check_duration


class PixelDissolve:
    """
    Transitions from source to target by revealing randomly-ordered tiles.
    """

    __slots__ = (
        "_tile_size",
        "_easing",
        "_elapsed",
        "_duration",
        "_done",
        "_paused",
        "_order",
        "_grid",
    )

    def __init__(
        self,
        tile_size: int = 8,
        easing: Callable[[float], float] = ease_out,
    ) -> None:
        if not isinstance(tile_size, int) or isinstance(tile_size, bool) or tile_size < 1:
            raise ValueError(f"tile_size must be an int >= 1, got {tile_size!r}")
        self._tile_size = tile_size
        self._easing = easing
        self._elapsed = 0.0
        self._duration = 0.0
        self._done = True
        self._paused = False
        self._order: list[int] = []
        self._grid: tuple[int, int] = (0, 0)

    def start(self, duration: float) -> None:
        self._elapsed = 0.0
        self._duration = _check_duration(duration)
        self._done = False
        self._paused = False
        self._order = []
        self._grid = (0, 0)

    @property
    def done(self) -> bool:
        return self._done

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    @property
    def paused(self) -> bool:
        return self._paused

    def reset(self) -> None:
        self._elapsed = 0.0
        self._duration = 0.0
        self._done = True
        self._paused = False
        self._order.clear()
        self._grid = (0, 0)

    def update(self, dt: float) -> None:
        if self._done or self._paused:
            return
        self._elapsed += _check_dt(dt)
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
        ts = self._tile_size
        cols = max(1, int(math.ceil(w / ts)))
        rows = max(1, int(math.ceil(h / ts)))

        if not self._order or self._grid != (cols, rows):
            self._grid = (cols, rows)
            self._order = list(range(cols * rows))
            random.shuffle(self._order)

        t = self._easing(self._elapsed / self._duration) if self._duration > 0 else 1.0
        reveal_count = int(t * len(self._order))

        revealed = set(self._order[:reveal_count])

        for idx in range(cols * rows):
            gx = idx % cols
            gy = idx // cols
            rx = gx * ts
            ry = gy * ts

            if idx in revealed and target is not None:
                screen.blit(target, (rx, ry), (rx, ry, ts, ts))
            elif source is not None:
                screen.blit(source, (rx, ry), (rx, ry, ts, ts))

        if self._done and target is not None:
            screen.blit(target, (0, 0))


class Shake:
    """
    Camera shake effect.
    Offsets the screen blit by a decaying random offset.
    Can be used standalone or alongside another transition.
    """

    __slots__ = ("_intensity", "_elapsed", "_duration", "_done", "_paused", "_offset")

    def __init__(self, intensity: float = 8.0) -> None:
        if not math.isfinite(intensity) or intensity < 0:
            raise ValueError(f"intensity must be finite and >= 0, got {intensity!r}")
        self._intensity = float(intensity)
        self._elapsed = 0.0
        self._duration = 0.0
        self._done = True
        self._paused = False
        self._offset = (0, 0)

    def start(self, duration: float = 0.3) -> None:
        self._elapsed = 0.0
        self._duration = _check_duration(duration)
        self._done = False
        self._paused = False

    @property
    def done(self) -> bool:
        return self._done

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    @property
    def paused(self) -> bool:
        return self._paused

    def reset(self) -> None:
        self._elapsed = 0.0
        self._duration = 0.0
        self._done = True
        self._paused = False
        self._offset = (0, 0)

    def update(self, dt: float) -> None:
        if self._done or self._paused:
            return
        self._elapsed += _check_dt(dt)
        if self._elapsed >= self._duration:
            self._elapsed = self._duration
            self._done = True
            self._offset = (0, 0)
            return

        t = self._elapsed / self._duration if self._duration > 0 else 1.0
        decay = 1.0 - t
        current = self._intensity * decay

        ox = random.uniform(-current, current)
        oy = random.uniform(-current, current)
        self._offset = (int(ox), int(oy))

    def render(
        self,
        screen: Surface,
        source: Surface | None = None,
        target: Surface | None = None,
    ) -> None:
        surf = target if target is not None else source
        if surf is not None:
            ox, oy = self._offset
            screen.blit(surf, (ox, oy))
