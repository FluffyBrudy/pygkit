import pygame
import pytest

from pygkit.ui.anchors import ANCHORS, anchor_point, column, grid, place, row


def test_nine_anchors():
    assert len(ANCHORS) == 9
    rect = pygame.Rect(10, 20, 100, 60)
    assert anchor_point(rect, "topleft") == (10, 20)
    assert anchor_point(rect, "center") == (60, 50)
    assert anchor_point(rect, "bottomright") == (110, 80)
    assert anchor_point(rect, "midtop") == (60, 20)
    with pytest.raises(ValueError, match="unknown anchor"):
        anchor_point(rect, "everywhere")


def test_place():
    within = pygame.Rect(0, 0, 200, 100)
    assert place((50, 20), within, "topleft") == pygame.Rect(0, 0, 50, 20)
    assert place((50, 20), within, "center") == pygame.Rect(75, 40, 50, 20)
    assert place((50, 20), within, "bottomright", dx=-5) == pygame.Rect(145, 80, 50, 20)


def test_row_column():
    rects = row([(50, 20), (30, 20)], gap=4, origin=(10, 10))
    assert rects == [pygame.Rect(10, 10, 50, 20), pygame.Rect(64, 10, 30, 20)]
    rects = column([(50, 20), (50, 30)], gap=5, origin=(0, 0))
    assert rects == [pygame.Rect(0, 0, 50, 20), pygame.Rect(0, 25, 50, 30)]


def test_grid():
    rects = grid(5, 2, (40, 30), gap=4, origin=(10, 10))
    assert rects[0] == pygame.Rect(10, 10, 40, 30)
    assert rects[1] == pygame.Rect(54, 10, 40, 30)
    assert rects[2] == pygame.Rect(10, 44, 40, 30)
    assert rects[4] == pygame.Rect(10, 78, 40, 30)
    with pytest.raises(ValueError, match="cols"):
        grid(5, 0, (40, 30))
