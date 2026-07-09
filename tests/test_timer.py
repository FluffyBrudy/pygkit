import pygame
import pytest

from pygkit.utils.timer import Timer


class TestTimer:
    def test_init(self):
        t = Timer(1000)
        assert t.interval == 1000

    def test_reached(self):
        t = Timer(0)
        assert t.reached() is True

    def test_not_reached(self):
        t = Timer(100000)
        assert t.reached() is False

    def test_reset(self):
        t = Timer(1000)
        t.reset()
        assert t.elapsed() < 50

    def test_ratio(self):
        t = Timer(1000)
        assert 0 <= t.ratio() <= 1.0

    def test_ratio_past_interval(self):
        t = Timer(1000)
        t.start_timer = pygame.time.get_ticks() - 2000
        assert t.ratio() == 1.0

    def test_stale(self):
        t = Timer(1000)
        t.stale()
        assert t.elapsed() >= 999

    def test_reached_at_invalid(self):
        t = Timer(1000)
        assert t.reached_at(0) is False
        assert t.reached_at(1.0) is False
