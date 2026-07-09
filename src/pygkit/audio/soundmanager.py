from pathlib import Path
from typing import Dict, Literal

import pygame
from pygame import Channel, Sound

SFX_CHANNELS = 6


class SoundManager:
    def __init__(self, num_channels: int = 8, main_channels: int = 2) -> None:
        if pygame.mixer.get_init() is None:
            raise RuntimeError("pygame.mixer not initialized")

        if main_channels + SFX_CHANNELS > num_channels:
            num_channels = main_channels + SFX_CHANNELS

        self._main: Dict[str, Sound] = {}
        self._sfx: Dict[str, Sound] = {}

        self._num_channels = num_channels
        self._main_count = main_channels
        self._channels = tuple(pygame.Channel(i) for i in range(num_channels))
        self._next_sfx = main_channels

    def add_sound(
        self, path: Path, key: str, kind: Literal["main", "sfx"] = "sfx"
    ) -> bool:
        scope = self._main if kind == "main" else self._sfx
        try:
            scope[key] = pygame.Sound(str(path))
            return True
        except (FileNotFoundError, TypeError, pygame.error) as e:
            return False

    def play(
        self,
        key: str,
        kind: Literal["main", "sfx"] = "sfx",
        channel_id: int | None = None,
        loops: int | None = None,
    ) -> None:
        scope = self._main if kind == "main" else self._sfx
        sound = scope.get(key)
        if sound is None:
            raise KeyError(f"Unknown sound '{key}'")

        if loops is None:
            loops = -1 if kind == "main" else 0

        if channel_id is not None:
            self._channels[channel_id].stop()
            self._channels[channel_id].play(sound, loops)
            return

        channel = self._assign(kind)
        channel.play(sound, loops)

    def stop_all(self) -> None:
        for ch in self._channels:
            ch.stop()

    def stop_channel(self, channel_id: int) -> None:
        self._channels[channel_id].stop()

    def get_channel(self, channel_id: int) -> Channel:
        return self._channels[channel_id]

    def _assign(self, kind: Literal["main", "sfx"]) -> Channel:
        if kind == "main":
            for idx in range(self._main_count):
                ch = self._channels[idx]
                if not ch.get_busy():
                    return ch
            ch = self._channels[0]
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
