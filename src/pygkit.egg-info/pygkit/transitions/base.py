from enum import Enum, auto
from typing import Protocol

from pygame import Surface


class Transition(Protocol):
    def start(self, duration: float) -> None: ...

    def update(self, dt: float) -> None: ...

    def render(
        self,
        screen: Surface,
        source: Surface | None = None,
        target: Surface | None = None,
    ) -> None: ...

    @property
    def done(self) -> bool: ...

    def reset(self) -> None: ...


class TransitionState(Enum):
    IDLE = auto()
    OUT = auto()
    IN = auto()
    DONE = auto()


class TransitionRunner:
    __slots__ = ("fade_out", "fade_in", "state")

    def __init__(
        self, fade_out: Transition | None = None, fade_in: Transition | None = None
    ) -> None:
        self.fade_out = fade_out
        self.fade_in = fade_in
        self.state = TransitionState.IDLE

    def start_out(self, duration: float = 0.5) -> None:
        if self.fade_out is not None:
            self.fade_out.start(duration)
        self.state = TransitionState.OUT

    def start_in(self, duration: float = 0.5) -> None:
        if self.fade_in is not None:
            self.fade_in.start(duration)
        self.state = TransitionState.IN

    def update(self, dt: float) -> None:
        if self.state is TransitionState.OUT:
            if self.fade_out is not None:
                self.fade_out.update(dt)
                if self.fade_out.done:
                    self.state = TransitionState.IDLE
            else:
                self.state = TransitionState.IDLE
        elif self.state is TransitionState.IN:
            if self.fade_in is not None:
                self.fade_in.update(dt)
                if self.fade_in.done:
                    self.state = TransitionState.DONE
            else:
                self.state = TransitionState.DONE

    def render(
        self,
        screen: Surface,
        source: Surface | None = None,
        target: Surface | None = None,
    ) -> None:
        if self.state is TransitionState.OUT and self.fade_out is not None:
            self.fade_out.render(screen, source=source, target=None)
        elif self.state is TransitionState.IN and self.fade_in is not None:
            self.fade_in.render(screen, source=None, target=target)
        elif self.state is TransitionState.DONE and target is not None:
            screen.blit(target, (0, 0))

    @property
    def done_out(self) -> bool:
        return (
            self.state is TransitionState.IDLE
            and (self.fade_out is None or self.fade_out.done)
        )

    @property
    def done(self) -> bool:
        return self.state is TransitionState.DONE

    def reset(self) -> None:
        if self.fade_out is not None:
            self.fade_out.reset()
        if self.fade_in is not None:
            self.fade_in.reset()
        self.state = TransitionState.IDLE
