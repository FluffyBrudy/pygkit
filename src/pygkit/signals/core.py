from __future__ import annotations

import logging
from typing import Any, Callable, Generic, TypeVar

log = logging.getLogger(__name__)

T = TypeVar("T")


class Signal(Generic[T]):
    def __init__(self, name: str = ""):
        self.name = name
        self._connections: list[Callable[..., Any]] = []

    def connect(self, callback: Callable[..., Any]) -> None:
        if callback in self._connections:
            return
        self._connections.append(callback)

    def disconnect(self, callback: Callable[..., Any]) -> None:
        self._connections = [c for c in self._connections if not (c == callback)]

    def disconnect_all(self) -> None:
        self._connections.clear()

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for callback in list(self._connections):
            try:
                callback(*args, **kwargs)
            except Exception:
                log.exception("Error in signal %s", self.name)

    def emit_strict(self, *args: Any, **kwargs: Any) -> None:
        for callback in list(self._connections):
            callback(*args, **kwargs)

    def __len__(self) -> int:
        return len(self._connections)

    def __bool__(self) -> bool:
        return True

    def __iadd__(self, callback: Callable[..., Any]) -> Signal[T]:
        self.connect(callback)
        return self

    def __isub__(self, callback: Callable[..., Any]) -> Signal[T]:
        self.disconnect(callback)
        return self

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.emit(*args, **kwargs)


class SignalBus:
    def __init__(self):
        self._signals: dict[str, Signal[Any]] = {}

    def create_signal(self, name: str) -> Signal[Any]:
        if name not in self._signals:
            self._signals[name] = Signal(name)
        return self._signals[name]

    def get_signal(self, name: str) -> Signal[Any] | None:
        return self._signals.get(name)

    def has_signal(self, name: str) -> bool:
        return name in self._signals

    def remove_signal(self, name: str) -> bool:
        return self._signals.pop(name, None) is not None

    def emit(self, name: str, *args: Any, **kwargs: Any) -> None:
        sig = self.get_signal(name)
        if sig is not None:
            sig.emit(*args, **kwargs)

    def connect(self, name: str, callback: Callable[..., Any]) -> None:
        self.create_signal(name).connect(callback)

    def disconnect(self, name: str, callback: Callable[..., Any]) -> None:
        sig = self.get_signal(name)
        if sig is not None:
            sig.disconnect(callback)


class signal:
    def __init__(self, name: str | None = None):
        self.name = name

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        try:
            return obj.__dict__[self.name]
        except KeyError:
            sig = Signal(self.name)
            obj.__dict__[self.name] = sig
            return sig

    def __set__(self, obj, value):
        if isinstance(value, Signal):
            obj.__dict__[self.name] = value
            return
        raise AttributeError(f"signal {self.name!r} is read-only; use .connect() instead")

    def __delete__(self, obj):
        raise AttributeError(f"signal {self.name!r} cannot be deleted")
