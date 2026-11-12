"""Tests for pack_spritesheet: flat packing, columns wrapping, labels."""

import pygame
import pytest

from pygkit.animation import AnimationSheet, pack_spritesheet

CELL = 8


def _frame(path, color, size=(CELL, CELL)):
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.fill(color)
    pygame.image.save(surf, str(path))


@pytest.fixture
def frames_dir(tmp_path):
    for i, color in enumerate([(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]):
        _frame(tmp_path / f"frame_{i:02d}.png", color)
    return tmp_path


def test_default_is_single_row(frames_dir):
    sheet = pack_spritesheet(frames_dir, target="file")
    assert sheet.get_size() == (4 * CELL, CELL)


def test_columns_one_stacks_vertically(frames_dir):
    sheet = pack_spritesheet(frames_dir, target="file", columns=1)
    assert sheet.get_size() == (CELL, 4 * CELL)


def test_columns_wraps_rows(frames_dir):
    sheet = pack_spritesheet(frames_dir, target="file", columns=2)
    assert sheet.get_size() == (2 * CELL, 2 * CELL)
    assert sheet.get_at((0, 0)).r == 255 and sheet.get_at((0, 0)).g == 0
    assert sheet.get_at((CELL, 0)).g == 255
    assert sheet.get_at((0, CELL)).b == 255
    assert sheet.get_at((CELL, CELL)).r == 255 and sheet.get_at((CELL, CELL)).b == 0


def test_ragged_last_row_padded_transparent(frames_dir):
    sheet = pack_spritesheet(frames_dir, target="file", columns=3)
    assert sheet.get_size() == (3 * CELL, 2 * CELL)
    pad = sheet.get_at((2 * CELL, CELL))
    assert pad.a == 0
    assert sheet.get_at((0, CELL)).r == 255 and sheet.get_at((0, CELL)).b == 0


def test_columns_readable_by_animationsheet(frames_dir, tmp_path):
    out = tmp_path / "packed.png"
    pygame.image.save(pack_spritesheet(frames_dir, target="file", columns=2), str(out))
    sheet = AnimationSheet(out, rows=2, cols=2)
    assert sheet.frame_count == 4
    assert sheet.get_frame(0).get_at((0, 0)).r == 255
    assert sheet.get_frame(2).get_at((0, 0)).b == 255


def test_columns_label_only_on_last_row(frames_dir):
    sheet = pack_spritesheet(frames_dir, target="file", columns=1, add_label=True, font_size=8)
    w, h = sheet.get_size()
    assert w > CELL
    assert h == 4 * CELL
    for row in range(3):
        assert sheet.get_at((CELL + 2, row * CELL)).a == 0


def test_columns_rejected_for_dir_target(frames_dir):
    (frames_dir / "walk").mkdir()
    _frame(frames_dir / "walk" / "a.png", (1, 2, 3, 255))
    with pytest.raises(ValueError, match="columns is only valid"):
        pack_spritesheet(frames_dir, target="dir", columns=2)


@pytest.mark.parametrize("bad", [0, -1, True, "2", 2.0])
def test_columns_validation(frames_dir, bad):
    with pytest.raises((TypeError, ValueError)):
        pack_spritesheet(frames_dir, target="file", columns=bad)


def test_single_row_label_unchanged(frames_dir):
    sheet = pack_spritesheet(frames_dir, target="file", add_label=True, font_size=8)
    w, h = sheet.get_size()
    assert h == CELL
    assert w > 4 * CELL


def test_hundred_frames_with_columns_within_limit(tmp_path):
    for i in range(100):
        _frame(tmp_path / f"f_{i:03d}.png", (i % 255, 100, 200, 255))
    sheet = pack_spritesheet(tmp_path, target="file", columns=3)
    assert sheet.get_size() == (3 * CELL, 34 * CELL)


def test_one_frame_over_limit_still_raises(tmp_path):
    for i in range(101):
        _frame(tmp_path / f"f_{i:03d}.png", (i % 255, 100, 200, 255))
    with pytest.raises(ValueError, match="Too many frames"):
        pack_spritesheet(tmp_path, target="file", columns=3)
