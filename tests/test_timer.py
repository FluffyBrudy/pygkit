import pytest

from pygkit.utils.timer import Timer


class TestTimer:
    def test_init(self):
        t = Timer(1.0)
        assert t.duration == 1.0
        assert t.elapsed() == 0.0
        assert t.reached() is False

    def test_update_advances(self):
        t = Timer(1.0)
        assert t.update(0.4) is False
        assert t.update(0.6) is True
        assert t.reached() is True

    def test_frozen_without_update(self):
        t = Timer(1.0)
        assert t.reached() is False
        assert t.elapsed() == 0.0

    def test_ratio(self):
        t = Timer(2.0)
        assert t.ratio() == 0.0
        t.update(1.0)
        assert t.ratio() == pytest.approx(0.5)
        t.update(5.0)
        assert t.ratio() == 1.0

    def test_remaining(self):
        t = Timer(2.0)
        assert t.remaining() == pytest.approx(2.0)
        t.update(0.5)
        assert t.remaining() == pytest.approx(1.5)
        t.update(5.0)
        assert t.remaining() == 0.0

    def test_reset(self):
        t = Timer(1.0)
        t.update(1.0)
        assert t.reached() is True
        t.reset()
        assert t.reached() is False
        assert t.elapsed() == 0.0

    def test_start_finished(self):
        t = Timer(1.0, start_finished=True)
        assert t.reached() is True
        assert t.ratio() == 1.0

    def test_zero_duration_reached(self):
        t = Timer(0.0)
        assert t.reached() is True
        assert t.ratio() == 1.0

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError):
            Timer(-1.0)

    def test_nonfinite_duration_raises(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with pytest.raises(ValueError):
                Timer(bad)

    def test_nonfinite_timescale_raises(self):
        for bad in (float("nan"), float("inf"), float("-inf")):
            with pytest.raises(ValueError):
                Timer(1.0, timescale=bad)

    def test_negative_timescale_allowed(self):
        t = Timer(1.0, timescale=-1.0)
        t.update(0.5)
        assert t.elapsed() == pytest.approx(-0.5)

    def test_nonfinite_dt_ignored(self):
        t = Timer(1.0)
        t.update(float("nan"))
        t.update(float("inf"))
        assert t.elapsed() == 0.0
        t.update(1.0)
        assert t.reached() is True

    def test_negative_dt_ignored(self):
        t = Timer(1.0)
        t.update(-5.0)
        assert t.elapsed() == 0.0

    def test_pause(self):
        t = Timer(1.0)
        t.pause()
        assert t.paused is True
        t.update(5.0)
        assert t.elapsed() == 0.0
        t.resume()
        assert t.paused is False
        t.update(1.0)
        assert t.reached() is True

    def test_timescale(self):
        t = Timer(1.0, timescale=2.0)
        t.update(0.5)
        assert t.reached() is True

    def test_loop(self):
        t = Timer(1.0, loop=True)
        assert t.update(1.5) is True
        assert t.elapsed() == pytest.approx(0.5)
        assert t.update(0.4) is False
        assert t.update(0.1) is True
        assert t.elapsed() == pytest.approx(0.0)
