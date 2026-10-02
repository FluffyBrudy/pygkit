from pathlib import Path
from typing import Dict, List, Literal, Optional, Tuple

import pygame
from pygame import Channel, Sound

DEFAULT_SFX_CHANNELS = 6
SFX_CHANNELS = DEFAULT_SFX_CHANNELS


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class SoundManager:
    def __init__(self, num_channels: int = 8, main_channels: int = 2) -> None:
        if pygame.mixer.get_init() is None:
            raise RuntimeError("pygame.mixer not initialized")
        if num_channels < 1:
            raise ValueError(f"num_channels must be >= 1, got {num_channels!r}")
        if not 0 <= main_channels <= num_channels:
            raise ValueError(f"main_channels must be 0..num_channels, got {main_channels!r}")

        if num_channels - main_channels < DEFAULT_SFX_CHANNELS:
            num_channels = main_channels + DEFAULT_SFX_CHANNELS

        if pygame.mixer.get_num_channels() < num_channels:
            pygame.mixer.set_num_channels(num_channels)

        self._main: Dict[str, Sound] = {}
        self._sfx: Dict[str, Sound] = {}

        self._num_channels = num_channels
        self._main_count = main_channels
        self._channels = tuple(pygame.Channel(i) for i in range(num_channels))
        self._next_sfx = main_channels
        self._next_main = 0

        self._master = 1.0
        self._kind_vol: Dict[str, float] = {"main": 1.0, "sfx": 1.0}
        self._vol: Dict[Tuple[str, str], float] = {}

    @property
    def sfx_channels(self) -> int:
        return self._num_channels - self._main_count

    def add_sound(
        self, path: str | Path, key: str, kind: Literal["main", "sfx"] = "sfx",
        volume: float = 1.0,
    ) -> bool:
        try:
            scope = self._scope(kind)
        except ValueError:
            return False
        registry = self._main if scope == "main" else self._sfx
        try:
            registry[key] = pygame.Sound(str(path))
            self._vol[(scope, key)] = _clamp(volume)
            return True
        except (FileNotFoundError, TypeError, pygame.error):
            return False

    def _scope(self, kind: str) -> str:
        if kind == "main":
            return "main"
        if kind == "sfx":
            return "sfx"
        raise ValueError(f"kind must be 'main' or 'sfx', got {kind!r}")

    def _pool(self, kind: str):
        scope = self._scope(kind)
        start = 0 if scope == "main" else self._main_count
        stop = self._main_count if scope == "main" else self._num_channels
        for idx in range(start, stop):
            yield idx, self._channels[idx]

    def _check_channel_id(self, channel_id: int) -> Channel:
        if not isinstance(channel_id, int) or isinstance(channel_id, bool):
            raise ValueError(f"channel_id must be an int, got {channel_id!r}")
        if not 0 <= channel_id < self._num_channels:
            raise ValueError(f"channel_id out of range 0..{self._num_channels - 1}")
        return self._channels[channel_id]

    def _effective(self, kind: str, key: str) -> float:
        scope = self._scope(kind)
        return _clamp(self._master * self._kind_vol[scope] * self._vol.get((scope, key), 1.0))

    def _locate(self, channel: Channel) -> Optional[Tuple[str, str]]:
        if not channel.get_busy():
            return None
        sound = channel.get_sound() if hasattr(channel, "get_sound") else None
        if sound is None:
            return None
        for scope, registry in (("main", self._main), ("sfx", self._sfx)):
            for key, owned in registry.items():
                if owned is sound:
                    return (scope, key)
        return None

    def play(
        self,
        key: str,
        kind: Literal["main", "sfx"] = "sfx",
        channel_id: int | None = None,
        loops: int | None = None,
        volume: float | None = None,
        fade_ms: int = 0,
    ) -> Channel:
        scope = self._scope(kind)
        registry = self._main if scope == "main" else self._sfx
        sound = registry.get(key)
        if sound is None:
            raise KeyError(f"Unknown sound '{key}'")

        if loops is None:
            loops = -1 if scope == "main" else 0

        if volume is not None:
            self._vol[(scope, key)] = _clamp(volume)

        fade_ms = max(0, int(fade_ms))
        if channel_id is not None:
            channel = self._check_channel_id(channel_id)
            channel.stop()
            channel.play(sound, loops, 0, fade_ms)
            channel.set_volume(self._effective(scope, key))
            return channel

        channel = self._assign(scope)
        channel.play(sound, loops, 0, fade_ms)
        channel.set_volume(self._effective(scope, key))
        return channel

    def channels_for(self, key: str, kind: Literal["main", "sfx"] = "sfx") -> List[Channel]:
        scope = self._scope(kind)
        registry = self._main if scope == "main" else self._sfx
        sound = registry.get(key)
        if sound is None:
            raise KeyError(f"Unknown sound '{key}'")
        return [
            channel
            for _, channel in self._pool(scope)
            if channel.get_busy() and channel.get_sound() is sound
        ]

    def playing(self, key: str, kind: Literal["main", "sfx"] = "sfx") -> bool:
        return len(self.channels_for(key, kind)) > 0

    def channel_for(self, key: str, kind: Literal["main", "sfx"] = "sfx") -> Optional[Channel]:
        found = self.channels_for(key, kind)
        return found[0] if found else None

    def stop(self, kind: Literal["main", "sfx"] | None = None, key: str | None = None) -> None:
        if kind is None and key is None:
            raise ValueError("stop() needs a kind or use stop_all()")
        if key is not None:
            if kind is None:
                raise ValueError("stop(key=...) needs kind=...")
            for channel in self.channels_for(key, kind):
                channel.stop()
            return
        scope = self._scope(kind)
        for _, channel in self._pool(scope):
            channel.stop()

    def stop_all(self) -> None:
        for ch in self._channels:
            ch.stop()

    def stop_channel(self, channel_id: int) -> None:
        self._check_channel_id(channel_id).stop()

    def fadeout(
        self, time_ms: int, kind: Literal["main", "sfx"] | None = None, key: str | None = None
    ) -> None:
        time_ms = max(0, int(time_ms))
        if key is not None:
            if kind is None:
                raise ValueError("fadeout(key=...) needs kind=...")
            for channel in self.channels_for(key, kind):
                channel.fadeout(time_ms)
            return
        if kind is None:
            for ch in self._channels:
                if ch.get_busy():
                    ch.fadeout(time_ms)
            return
        for _, channel in self._pool(self._scope(kind)):
            if channel.get_busy():
                channel.fadeout(time_ms)

    def set_volume(
        self, value: float, kind: Literal["main", "sfx"] | None = None, key: str | None = None
    ) -> None:
        value = _clamp(value)
        if key is not None:
            if kind is None:
                raise ValueError("set_volume(key=...) needs kind=...")
            scope = self._scope(kind)
            registry = self._main if scope == "main" else self._sfx
            if key not in registry:
                raise KeyError(f"Unknown sound '{key}'")
            self._vol[(scope, key)] = value
            for channel in self.channels_for(key, scope):
                channel.set_volume(self._effective(scope, key))
            return
        if kind is None:
            self._master = value
            for ch in self._channels:
                located = self._locate(ch)
                if located is not None:
                    ch.set_volume(self._effective(*located))
            return
        scope = self._scope(kind)
        self._kind_vol[scope] = value
        for _, channel in self._pool(scope):
            located = self._locate(channel)
            if located is not None:
                channel.set_volume(self._effective(*located))

    def get_volume(
        self, kind: Literal["main", "sfx"] | None = None, key: str | None = None
    ) -> float:
        if key is not None:
            if kind is None:
                raise ValueError("get_volume(key=...) needs kind=...")
            scope = self._scope(kind)
            registry = self._main if scope == "main" else self._sfx
            if key not in registry:
                raise KeyError(f"Unknown sound '{key}'")
            return self._vol.get((scope, key), 1.0)
        if kind is None:
            return self._master
        return self._kind_vol[self._scope(kind)]

    def get_channel(self, channel_id: int) -> Channel:
        return self._check_channel_id(channel_id)

    def _assign(self, kind: Literal["main", "sfx"]) -> Channel:
        if kind == "main":
            for idx in range(self._main_count):
                ch = self._channels[idx]
                if not ch.get_busy():
                    return ch
            if self._main_count == 0:
                raise RuntimeError("no main channels allocated")
            ch = self._channels[self._next_main % self._main_count]
            self._next_main += 1
            ch.stop()
            return ch

        for idx in range(self._main_count, self._num_channels):
            ch = self._channels[idx]
            if not ch.get_busy():
                return ch

        ch = self._channels[self._next_sfx]
        ch.stop()
        self._next_sfx += 1
        if self._next_sfx >= self._num_channels:
            self._next_sfx = self._main_count
        return ch
