import pygame
import pytest

from pygkit.ui.base import UIBase, generate_box_model


class TestGenerateBoxModel:
    def test_empty(self):
        result = generate_box_model({})
        assert result["full_width"] == 0
        assert result["full_height"] == 0
        assert result["content_width"] == 0
        assert result["content_height"] == 0

    def test_basic(self):
        result = generate_box_model({"width": 100, "height": 50})
        assert result["full_width"] == 100
        assert result["full_height"] == 50
        assert result["content_width"] == 100
        assert result["content_height"] == 50

    def test_padding(self):
        result = generate_box_model(
            {"width": 100, "height": 50, "padding_x": 5, "padding_y": 5}
        )
        assert result["content_width"] == 90
        assert result["content_height"] == 40
        assert result["left"] == 5
        assert result["top"] == 5

    def test_padding_and_border(self):
        result = generate_box_model(
            {
                "width": 100,
                "height": 50,
                "padding_x": 5,
                "padding_y": 5,
                "border_width": 2,
            }
        )
        assert result["content_width"] == 86
        assert result["content_height"] == 36

    def test_margin(self):
        result = generate_box_model(
            {"width": 100, "height": 50, "margin_x": 10, "margin_y": 20}
        )
        assert result["offset_x"] == 10
        assert result["offset_y"] == 20


class TestUIBaseRect:
    def test_rect_matches_size(self):
        class _W(UIBase):
            pass
        w = _W({"width": 120, "height": 48})
        assert w.rect == pygame.Rect(0, 0, 120, 48)
        assert w.rect.size == w.size

    def test_rect_is_local(self):
        # rect is always (0,0,w,h) — local space, not offset by margin
        w = UIBase({"width": 80, "height": 40, "margin_x": 20, "margin_y": 10})
        assert w.rect.topleft == (0, 0)
        assert w.rect.size == (80, 40)

    def test_legacy_chrome_options_are_rejected(self):
        with pytest.raises(TypeError, match="geometry keys"):
            UIBase({"width": 80, "background": (0, 0, 0)})  # type: ignore[typeddict-item]


def test_border_color_with_zero_width_draws_nothing():
    widget = UIBase(
        {"width": 40, "height": 20, "border_width": 0},
        style={"bg": (5, 5, 5, 255), "border": (255, 0, 0, 255), "radius": 0},
    )
    screen = pygame.Surface((60, 40), pygame.SRCALPHA)
    widget.render(screen, (10, 10))
    assert screen.get_at((10, 10))[:3] == (5, 5, 5)
