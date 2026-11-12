import pygame


class Timer:
    __slots__ = ("interval", "start_timer")

    def __init__(self, interval: float | int, stale_init: bool = False) -> None:
        self.start_timer = pygame.time.get_ticks()
        if stale_init:
            self.start_timer -= int(interval) - 1
        self.interval = int(interval)

    def reset(self) -> None:
        self.start_timer = pygame.time.get_ticks()

    def reached(self) -> bool:
        return self.elapsed() >= self.interval

    def reached_at(self, ratio: float) -> bool:
        if ratio <= 0 or ratio >= 1.0:
            return False
        return self.elapsed() >= int(self.interval * ratio)

    def stale(self) -> None:
        if self.interval > 0:
            self.start_timer -= self.interval - 1

    def elapsed(self) -> int:
        return pygame.time.get_ticks() - self.start_timer

    def ratio(self) -> float:
        td = self.elapsed()
        if td >= self.interval:
            return 1.0
        return td / self.interval
