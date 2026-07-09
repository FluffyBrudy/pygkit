import pygame
import pytest

from pygkit.utils.text import fit, load_font, outline, render_multiline, shadow, wrap


@pytest.fixture
def font():
    pygame.font.init()
    f = pygame.font.Font(None, 22)
    yield f
    pygame.font.quit()


class TestLoadFont:
    def test_loads_path(self, font, tmp_path):
        p = tmp_path / "test.ttf"
        p.write_bytes(b"")  # invalid font file, will fallback
        result = load_font(p, 22)
        assert isinstance(result, pygame.font.Font)
        assert result.get_height() > 0

    def test_missing_path(self, font):
        result = load_font("/nonexistent/font.ttf", 16)
        assert isinstance(result, pygame.font.Font)
        assert result.get_height() > 0

    def test_default_size(self, font):
        result = load_font("missing.ttf", 16, default_size=32)
        assert result.get_height() > 20


class TestOutline:
    def test_returns_surface(self, font):
        surf = outline(font, "Hi", (255, 255, 255), (0, 0, 0))
        assert isinstance(surf, pygame.Surface)
        assert surf.get_width() > 0
        assert surf.get_height() > 0


class TestShadow:
    def test_returns_surface(self, font):
        surf = shadow(font, "Hi", (255, 255, 255), (0, 0, 0))
        assert isinstance(surf, pygame.Surface)

    def test_offset_adds_size(self, font):
        no_offset = shadow(font, "Hi", (255, 255, 255), (0, 0, 0), (0, 0))
        offset = shadow(font, "Hi", (255, 255, 255), (0, 0, 0), (5, 5))
        assert offset.get_width() >= no_offset.get_width()
        assert offset.get_height() >= no_offset.get_height()


class TestWrap:
    def test_no_wrap_needed(self, font):
        lines = wrap(font, "hello", 500)
        assert lines == ["hello"]

    def test_wraps_long_line(self, font):
        text = "hello " * 50
        lines = wrap(font, text, 60)
        assert len(lines) > 1
        assert all(font.size(l)[0] <= 60 for l in lines)

    def test_empty(self, font):
        assert wrap(font, "", 100) == [""]

    def test_newline_preserved(self, font):
        lines = wrap(font, "a\nb", 500)
        assert lines == ["a", "b"]


class TestRenderMultiline:
    def test_single_line(self, font):
        surf = render_multiline(font, "hello", (255, 255, 255))
        assert isinstance(surf, pygame.Surface)
        assert surf.get_height() > 0

    def test_multi_line(self, font):
        surf = render_multiline(font, "a\nb\nc", (255, 255, 255))
        assert surf.get_height() > font.get_linesize() * 2

    def test_wrap(self, font):
        text = "word " * 50
        surf = render_multiline(font, text, (255, 255, 255), max_width=60)
        assert surf.get_width() <= 60


class TestFit:
    def test_returns_font_size(self, font):
        size = fit(font, "hello", 200, 50)
        assert isinstance(size, int)
        assert 8 <= size <= font.get_height()

    def test_downscales(self, font):
        big = pygame.font.Font(None, 72)
        size = fit(big, "hello world this is long", 100, 30)
        assert size < 72
        assert 8 <= size <= 72
