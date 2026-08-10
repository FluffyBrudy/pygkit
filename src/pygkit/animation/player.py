from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .sheet import AnimationSheet


@dataclass
class _State:
    sheet: AnimationSheet
    fps: float
    loop: bool
    on_finish: Callable[[], None] | None


class AnimationPlayer:
    """Multi-state animation player where each state owns its own spritesheet.

    States are registered lazily via :meth:`play`; sheets may differ freely in
    pixel size and grid layout between states. Playback is time-based: feed
    ``update(dt_ms)`` each frame and blit ``image``.
    """

    __slots__ = (
        "_states",
        "_state_name",
        "_frame_index",
        "_elapsed_in_frame",
        "_finished",
        "_paused",
        "_default_fps",
        "_default_loop",
        "_default_on_finish",
    )

    def __init__(
        self,
        fps: float = 10.0,
        loop: bool = False,
        on_finish: Callable[[], None] | None = None,
    ) -> None:
        self._validate_fps(fps)
        self._states: dict[str, _State] = {}
        self._state_name: str | None = None
        self._frame_index = 0
        self._elapsed_in_frame = 0.0
        self._finished = False
        self._paused = False
        self._default_fps = fps
        self._default_loop = loop
        self._default_on_finish = on_finish

    @staticmethod
    def _validate_fps(fps: float) -> None:
        if fps is None or fps <= 0:
            raise ValueError(f"fps must be > 0, got {fps!r}")

    @property
    def state(self) -> str | None:
        return self._state_name

    @property
    def frame_index(self) -> int:
        return self._frame_index

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def states(self) -> tuple[str, ...]:
        return tuple(self._states)

    @property
    def image(self):
        if self._state_name is None:
            return None
        return self._states[self._state_name].sheet.get_frame(self._frame_index)

    def play(
        self,
        name: str,
        sheet: AnimationSheet | None = None,
        *,
        fps: float | None = None,
        loop: bool | None = None,
        on_finish: Callable[[], None] | None = None,
    ) -> None:
        """Switch to *name*, registering the state on first use.

        Registration requires *sheet*; omitted options fall back to the
        player defaults given at construction. Calling ``play`` for the state
        already playing does not restart it — use :meth:`reset`.
        """
        if name not in self._states:
            if sheet is None:
                raise ValueError(f"Unknown animation state {name!r}: pass a sheet to register it first")
            resolved_fps = self._default_fps if fps is None else fps
            self._validate_fps(resolved_fps)
            self._states[name] = _State(
                sheet=sheet,
                fps=float(resolved_fps),
                loop=self._default_loop if loop is None else bool(loop),
                on_finish=self._default_on_finish if on_finish is None else on_finish,
            )

        if name == self._state_name:
            return
        self._state_name = name
        self.reset()

    def update(self, dt_ms: float) -> None:
        """Advance playback by *dt_ms* milliseconds of wall time."""
        if self._paused or self._state_name is None or self._finished:
            return
        state = self._states[self._state_name]
        frame_count = state.sheet.frame_count
        frame_duration = 1000.0 / state.fps
        self._elapsed_in_frame += max(0.0, dt_ms)
        while self._elapsed_in_frame >= frame_duration:
            self._elapsed_in_frame -= frame_duration
            next_index = self._frame_index + 1
            if next_index < frame_count:
                self._frame_index = next_index
                continue
            if state.loop:
                self._frame_index = 0
            else:
                self._frame_index = frame_count - 1
                self._elapsed_in_frame = 0.0
                self._finished = True
                if state.on_finish is not None:
                    state.on_finish()
                break

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def reset(self) -> None:
        self._frame_index = 0
        self._elapsed_in_frame = 0.0
        self._finished = False
        self._paused = False

    def stop(self) -> None:
        self.reset()
        self._paused = True
