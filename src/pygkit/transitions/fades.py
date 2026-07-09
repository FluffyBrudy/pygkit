from typing import Callable

from pygame import SRCALPHA, Surface

from ..utils.interpolation import ease_in_out


class _FadeBase:
    __slots__ = ("_color", "_easing", "_overlay", "_elapsed", "_duration", "_done")

    def __init__(
        self,
        color: tuple[int, int, int] = (0, 0, 0),
        easing: Callable[[float], float] = ease_in_out,
    ) -> None:
        self._color = color
        self._easing = easing
        self._overlay: Surface | None = None
        self._elapsed = 0.0
        self._duration = 0.0
        self._done = True

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
        self._overlay = None


class FadeToBlack(_FadeBase):
    """
    Fades the source surface to black.
    """

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

        t = self._easing(self._elapsed / self._duration) if self._duration > 0 else 1.0
        alpha = int(t * 255)

        if alpha > 0:
            size = screen.get_size()
            if (
                self._overlay is None
                or self._overlay.get_size() != size
            ):
                self._overlay = Surface(size, SRCALPHA)
            self._overlay.fill((*self._color, alpha))
            screen.blit(self._overlay, (0, 0))


class FadeFromBlack(_FadeBase):
    """
    Fades from black to reveal the target surface.
    """

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
        if target is not None:
            screen.blit(target, (0, 0))

        t = self._easing(self._elapsed / self._duration) if self._duration > 0 else 1.0
        alpha = int((1.0 - t) * 255)

        if alpha > 0:
            size = screen.get_size()
            if (
                self._overlay is None
                or self._overlay.get_size() != size
            ):
                self._overlay = Surface(size, SRCALPHA)
            self._overlay.fill((*self._color, alpha))
            screen.blit(self._overlay, (0, 0))


class Crossfade(_FadeBase):
    """
    Blends from source to target.
    """

    def __init__(self, easing: Callable[[float], float] = ease_in_out) -> None:
        super().__init__(easing=easing)

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
        t = self._easing(self._elapsed / self._duration) if self._duration > 0 else 1.0

        if target is not None:
            screen.blit(target, (0, 0))

        if source is not None and t < 1.0:
            alpha = int((1.0 - t) * 255)
            size = screen.get_size()
            if (
                self._overlay is None
                or self._overlay.get_size() != size
            ):
                self._overlay = Surface(size, SRCALPHA)
            self._overlay.fill((0, 0, 0, 0))
            self._overlay.blit(source, (0, 0))
            self._overlay.set_alpha(alpha)
            screen.blit(self._overlay, (0, 0))


class Flash(_FadeBase):
    """
    Brief white (or colored) flash that fades quickly.
    Default duration 0.15s.
    """

    def __init__(
        self,
        color: tuple[int, int, int] = (255, 255, 255),
        easing: Callable[[float], float] = ease_in_out,
    ) -> None:
        super().__init__(color=color, easing=easing)

    def start(self, duration: float | None = None) -> None:
        super().start(0.15 if duration is None else duration)

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

        t = self._easing(self._elapsed / self._duration) if self._duration > 0 else 1.0
        alpha = int((1.0 - t) * 255)

        if alpha > 0:
            size = screen.get_size()
            if (
                self._overlay is None
                or self._overlay.get_size() != size
            ):
                self._overlay = Surface(size, SRCALPHA)
            self._overlay.fill((*self._color, alpha))
            screen.blit(self._overlay, (0, 0))
