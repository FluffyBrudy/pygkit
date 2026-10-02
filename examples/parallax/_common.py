"""Shared fixture loader for parallax examples.

Tries the grotto fixture art first, falls back to a procedural strip so
every example runs with or without the fixture on disk.
"""

from pathlib import Path

import pygame

GROTTO = Path(__file__).parent.parent / "assets" / "grotto"


def load(name, scale=1, fallback=None):
    path = GROTTO / name
    if path.exists():
        img = pygame.image.load(str(path)).convert_alpha()
        if scale != 1:
            w, h = img.get_size()
            img = pygame.transform.scale(img, (w * scale, h * scale))
        return img, True
    if fallback is None:
        raise FileNotFoundError(f"missing fixture {path} and no fallback given")
    return fallback(), False


def band(w, h, base, mark):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill(base)
    for x in range(0, w, 32):
        pygame.draw.rect(s, mark, (x, h // 2 - 6, 16, 12))
    return s
