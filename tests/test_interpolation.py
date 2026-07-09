import math

from pygkit.utils.interpolation import (
    SimpleInterpolation,
    ease_in,
    ease_in_out,
    ease_out,
    lerp,
    smoothstep,
)


class TestEasingFunctions:
    def test_lerp(self):
        assert lerp(0, 100, 0.5) == 50
        assert lerp(0, 100, 0) == 0
        assert lerp(0, 100, 1) == 100

    def test_smoothstep(self):
        assert smoothstep(0) == 0
        assert smoothstep(1) == 1
        assert smoothstep(0.5) == 0.5

    def test_ease_in(self):
        assert ease_in(0) == 0
        assert ease_in(1) == 1
        assert ease_in(0.5) == 0.25

    def test_ease_out(self):
        assert ease_out(0) == 0
        assert ease_out(1) == 1
        assert ease_out(0.5) == 0.75

    def test_ease_in_out(self):
        assert ease_in_out(0) == 0
        assert ease_in_out(1) == 1
        assert ease_in_out(0.25) == 2 * 0.25 * 0.25


class TestSimpleInterpolation:
    def test_init(self):
        s = SimpleInterpolation(1.0, 0.1)
        assert s.current == 1.0
        assert s.target == 1.0

    def test_set(self):
        s = SimpleInterpolation(0, 0.5)
        s.set(0.5)
        assert s.target == 0.5

    def test_set_clamps(self):
        s = SimpleInterpolation(0, 0.5)
        s.set(1.5)
        assert s.target == 1.0
        s.set(-0.5)
        assert s.target == 0.0

    def test_update_converges(self):
        s = SimpleInterpolation(0, 1.0)
        s.set(1.0)
        s.update()
        assert s.current == 1.0

    def test_finished(self):
        s = SimpleInterpolation(0, 1.0)
        s.set(1.0)
        s.update()
        assert s.finished() is True

    def test_not_finished(self):
        s = SimpleInterpolation(0, 0.1)
        s.set(1.0)
        assert s.finished() is False
