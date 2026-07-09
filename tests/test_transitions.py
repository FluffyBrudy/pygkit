import pygame
import pytest

from pygkit.transitions import (
    Crossfade,
    FadeFromBlack,
    FadeToBlack,
    Flash,
    IrisIn,
    IrisOut,
    PixelDissolve,
    Shake,
    Slide,
    TransitionRunner,
    TransitionState,
)


class TestFades:
    def test_fade_to_black_lifecycle(self):
        t = FadeToBlack()
        assert t.done is True
        t.start(1.0)
        assert t.done is False
        t.update(0.5)
        assert t.done is False
        t.update(0.5)
        assert t.done is True

    def test_fade_to_black_zero_duration(self):
        t = FadeToBlack()
        t.start(0)
        t.update(0)
        assert t.done is True

    def test_fade_from_black_lifecycle(self):
        t = FadeFromBlack()
        t.start(0.5)
        t.update(0.5)
        assert t.done is True

    def test_crossfade_lifecycle(self):
        t = Crossfade()
        t.start(1.0)
        t.update(0.3)
        assert t.done is False
        t.update(0.7)
        assert t.done is True

    def test_flash_default_duration(self):
        t = Flash()
        t.start()
        assert t.done is False
        t.update(0.15)
        assert t.done is True

    def test_reset(self):
        t = FadeToBlack()
        t.start(1.0)
        t.update(1.0)
        assert t.done is True
        t.reset()
        assert t.done is False
        assert t._elapsed == 0.0

    def test_update_past_duration(self):
        t = FadeToBlack()
        t.start(0.5)
        t.update(10.0)
        assert t.done is True


class TestWipes:
    def test_iris_in_lifecycle(self):
        t = IrisIn()
        t.start(0.5)
        t.update(0.5)
        assert t.done is True

    def test_iris_out_lifecycle(self):
        t = IrisOut()
        t.start(0.5)
        t.update(0.5)
        assert t.done is True

    def test_slide_invalid_direction(self):
        with pytest.raises(ValueError):
            Slide("diagonal")

    def test_slide_lifecycle(self):
        t = Slide("right")
        t.start(0.3)
        t.update(0.3)
        assert t.done is True


class TestEffects:
    def test_pixel_dissolve_lifecycle(self):
        t = PixelDissolve(16)
        t.start(1.0)
        assert t.done is False
        t.update(0.5)
        assert t.done is False
        t.update(0.5)
        assert t.done is True

    def test_shake_lifecycle(self):
        t = Shake(10.0)
        t.start(0.3)
        assert t.done is False
        t.update(0.3)
        assert t.done is True
        assert t._offset == (0, 0)


class TestTransitionRunner:
    def test_idle_initial_state(self):
        runner = TransitionRunner(FadeToBlack(), FadeFromBlack())
        assert runner.state is TransitionState.IDLE

    def test_start_out(self):
        runner = TransitionRunner(FadeToBlack(), FadeFromBlack())
        runner.start_out(0.5)
        assert runner.state is TransitionState.OUT
        assert runner.fade_out.done is False

    def test_out_to_in_flow(self):
        runner = TransitionRunner(FadeToBlack(), FadeFromBlack())
        runner.start_out(0.1)
        runner.update(0.1)
        assert runner.done_out is True
        runner.start_in(0.1)
        assert runner.state is TransitionState.IN
        runner.update(0.1)
        assert runner.done is True

    def test_no_fade_out(self):
        runner = TransitionRunner(fade_in=FadeFromBlack())
        runner.start_out(0.1)
        assert runner.state is TransitionState.OUT
        runner.update(0.1)
        assert runner.done_out is True

    def test_no_fade_in(self):
        runner = TransitionRunner(fade_out=FadeToBlack())
        runner.start_out(0.1)
        runner.update(0.1)
        assert runner.done_out is True
        runner.start_in(0.1)
        runner.update(0.1)
        assert runner.done is True

    def test_reset(self):
        runner = TransitionRunner(FadeToBlack(), FadeFromBlack())
        runner.start_out(0.1)
        runner.update(0.1)
        runner.reset()
        assert runner.state is TransitionState.IDLE

    def test_no_transitions(self):
        runner = TransitionRunner()
        runner.start_out(0.1)
        runner.update(0.1)
        assert runner.done_out is True
        runner.start_in(0.1)
        runner.update(0.1)
        assert runner.done is True
