import math


class Timer:
    __slots__ = ("duration", "loop", "_elapsed", "_paused", "timescale")

    def __init__(
        self,
        duration: float,
        *,
        loop: bool = False,
        paused: bool = False,
        timescale: float = 1.0,
        start_finished: bool = False,
    ) -> None:
        if not math.isfinite(duration) or duration < 0:
            raise ValueError(f"duration must be finite and >= 0, got {duration!r}")
        if not math.isfinite(timescale):
            raise ValueError(f"timescale must be finite, got {timescale!r}")
        self.duration = float(duration)
        self.loop = bool(loop)
        self._elapsed = float(duration) if start_finished else 0.0
        self._paused = bool(paused)
        self.timescale = float(timescale)

    def update(self, dt: float) -> bool:
        if self._paused:
            return self.reached()
        if not math.isfinite(dt) or dt < 0:
            dt = 0.0
        self._elapsed += dt * self.timescale
        if self.loop and self.duration > 0:
            if self._elapsed >= self.duration:
                self._elapsed %= self.duration
                return True
            return False
        if self._elapsed > self.duration:
            self._elapsed = self.duration
        return self.reached()

    def elapsed(self) -> float:
        return self._elapsed

    def remaining(self) -> float:
        left = self.duration - self._elapsed
        return left if left > 0 else 0.0

    def ratio(self) -> float:
        if self.duration <= 0:
            return 1.0
        t = self._elapsed / self.duration
        if t < 0:
            return 0.0
        return 1.0 if t > 1.0 else t

    def reached(self) -> bool:
        return self._elapsed >= self.duration

    def reset(self) -> None:
        self._elapsed = 0.0

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    @property
    def paused(self) -> bool:
        return self._paused
