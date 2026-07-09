import math


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(t: float) -> float:
    return t * t * (3 - 2 * t)


def ease_in(t: float) -> float:
    return t * t


def ease_out(t: float) -> float:
    return 1 - (1 - t) ** 2


def ease_in_out(t: float) -> float:
    if t < 0.5:
        return 2 * t * t
    return 1 - ((-2 * t + 2) ** 2) / 2


class SimpleInterpolation:
    __slots__ = ("current", "target", "speed")

    def __init__(self, value: float = 1.0, speed: float = 0.1) -> None:
        self.current = value
        self.target = value
        self.speed = speed

    def set(self, target: float) -> None:
        self.target = max(0, min(target, 1.0))

    def update(self) -> None:
        diff = self.target - self.current
        if abs(diff) < 0.001:
            self.current = self.target
        else:
            self.current += diff * self.speed

    def finished(self) -> bool:
        return abs(self.current - self.target) < 0.001
