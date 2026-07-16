from __future__ import annotations

from typing import Any, Callable, Generic, TypeVar

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
        self._connections = [c for c in self._connections if c is not callback]

    def disconnect_all(self) -> None:
        self._connections.clear()

    def emit(self, *args: Any, **kwargs: Any) -> None:
        for callback in list(self._connections):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                print(f"Error in signal {self.name}: {e}")

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

    def emit(self, name: str, *args: Any, **kwargs: Any) -> None:
        sig = self.get_signal(name)
        if sig:
            sig.emit(*args, **kwargs)

    def connect(self, name: str, callback: Callable[..., Any]) -> None:
        sig = self.get_signal(name)
        if sig:
            sig.connect(callback)

    def disconnect(self, name: str, callback: Callable[..., Any]) -> None:
        sig = self.get_signal(name)
        if sig:
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
