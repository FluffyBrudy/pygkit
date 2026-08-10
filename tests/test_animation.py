from pathlib import Path

import pygame
import pytest

from pygkit.animation import AnimationPlayer, AnimationSheet


def _make_sheet_png(path: Path, rows: int, cols: int, cell: int, base_hue: int) -> dict[int, tuple[int, int, int]]:
    """Write a synthetic sheet where every cell is a unique solid color."""
    width, height = cols * cell, rows * cell
    sheet = pygame.Surface((width, height))
    colors: dict[int, tuple[int, int, int]] = {}
    for index in range(rows * cols):
        color = (
            (base_hue + index * 37) % 256,
            (base_hue + index * 71) % 256,
            (base_hue + index * 113) % 256,
        )
        colors[index] = color
        col, row = index % cols, index // cols
        sheet.fill(color, (col * cell, row * cell, cell, cell))
    pygame.image.save(sheet, str(path))
    return colors


def _center_color(surface: pygame.Surface) -> tuple[int, int, int]:
    return surface.get_at((surface.get_width() // 2, surface.get_height() // 2))[:3]


@pytest.fixture
def idle_png(tmp_path: Path) -> Path:
    path = tmp_path / "idle_spritesheet.png"
    _make_sheet_png(path, rows=1, cols=4, cell=32, base_hue=10)
    return path


@pytest.fixture
def run_png(tmp_path: Path) -> Path:
    path = tmp_path / "run_spritesheet.png"
    _make_sheet_png(path, rows=2, cols=3, cell=48, base_hue=200)
    return path


class TestAnimationSheet:
    def test_load_from_path(self, idle_png: Path):
        sheet = AnimationSheet.load(idle_png, rows=1, cols=4)
        assert sheet.frame_count == 4
        assert sheet.cell_size == (32, 32)

    def test_constructor_accepts_surface(self):
        surface = pygame.Surface((64, 32))
        sheet = AnimationSheet(surface, rows=2, cols=1)
        assert sheet.frame_count == 2
        assert sheet.cell_size == (64, 16)

    def test_row_major_indexing(self, tmp_path: Path):
        colors = _make_sheet_png(tmp_path / "grid.png", rows=2, cols=3, cell=8, base_hue=0)
        sheet = AnimationSheet.load(tmp_path / "grid.png", rows=2, cols=3)
        for index in range(6):
            assert _center_color(sheet.get_frame(index)) == colors[index]

    def test_frames_are_cached(self, idle_png: Path):
        sheet = AnimationSheet.load(idle_png, rows=1, cols=4)
        assert sheet.get_frame(0) is sheet.get_frame(0)
        assert sheet.get_frame(0) is not sheet.get_frame(1)

    def test_out_of_range_index_raises(self, idle_png: Path):
        sheet = AnimationSheet.load(idle_png, rows=1, cols=4)
        with pytest.raises(IndexError):
            sheet.get_frame(4)
        with pytest.raises(IndexError):
            sheet.get_frame(-1)

    @pytest.mark.parametrize("rows,cols", [(0, 1), (1, 0), (-1, 2)])
    def test_invalid_grid_raises(self, idle_png: Path, rows: int, cols: int):
        with pytest.raises(ValueError):
            AnimationSheet(idle_png, rows=rows, cols=cols)

    def test_missing_file_raises(self):
        with pytest.raises(ValueError):
            AnimationSheet("no_such_sheet.png", rows=1, cols=1)


class TestAnimationPlayer:
    def test_play_registers_state_and_sets_image(self, idle_png: Path):
        player = AnimationPlayer()
        player.play("idle", AnimationSheet.load(idle_png, rows=1, cols=4), fps=10)
        assert player.state == "idle"
        assert player.frame_index == 0
        assert not player.finished
        image = player.image
        assert image is not None
        assert image.get_size() == (32, 32)

    def test_unknown_state_without_sheet_raises(self):
        player = AnimationPlayer()
        with pytest.raises(ValueError):
            player.play("idle")

    def test_update_advances_at_fps(self, idle_png: Path):
        player = AnimationPlayer()
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)  # 100 ms per frame
        player.update(100.0)
        assert player.frame_index == 1
        player.update(250.0)
        assert player.frame_index == 3

    def test_loop_wraps_to_start(self, idle_png: Path):
        player = AnimationPlayer(loop=True)
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)
        for _ in range(5):
            player.update(100.0)
        assert player.frame_index == 1
        assert not player.finished

    def test_non_looping_finishes_on_last_frame(self, idle_png: Path):
        calls = []
        player = AnimationPlayer(on_finish=lambda: calls.append("done"))
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)
        for _ in range(10):
            player.update(100.0)
        assert player.finished
        assert player.frame_index == 3
        assert calls == ["done"]

    def test_finished_player_stays_put(self, idle_png: Path):
        player = AnimationPlayer()
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)
        for _ in range(6):
            player.update(100.0)
        player.update(500.0)
        assert player.frame_index == 3
        assert player.finished

    def test_mixed_size_states(self, idle_png: Path, run_png: Path):
        player = AnimationPlayer(fps=10)
        player.play("idle", AnimationSheet(idle_png, 1, 4))
        player.play("run", AnimationSheet(run_png, 2, 3), fps=12)
        assert player.state == "run"
        assert player.image.get_size() == (48, 48)
        player.play("idle")
        assert player.image.get_size() == (32, 32)

    def test_same_state_play_does_not_restart(self, idle_png: Path):
        player = AnimationPlayer()
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)
        player.update(350.0)
        player.play("idle")
        assert player.frame_index == 3

    def test_switch_clears_finished(self, idle_png: Path, run_png: Path):
        player = AnimationPlayer()
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)
        for _ in range(6):
            player.update(100.0)
        assert player.finished
        player.play("run", AnimationSheet(run_png, 2, 3))
        assert not player.finished
        assert player.frame_index == 0

    def test_pause_resume(self, idle_png: Path):
        player = AnimationPlayer()
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)
        player.pause()
        player.update(100.0)
        assert player.frame_index == 0
        player.resume()
        player.update(100.0)
        assert player.frame_index == 1
        assert not player.paused

    def test_stop_resets_and_pauses(self, idle_png: Path):
        player = AnimationPlayer()
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)
        player.update(150.0)
        player.stop()
        assert player.paused and player.frame_index == 0
        player.update(100.0)
        assert player.frame_index == 0

    def test_reset_clears_pause_and_finished(self, idle_png: Path):
        player = AnimationPlayer()
        player.play("idle", AnimationSheet(idle_png, 1, 4), fps=10)
        for _ in range(6):
            player.update(100.0)
        player.pause()
        player.reset()
        assert not player.paused and not player.finished
        player.update(100.0)
        assert player.frame_index == 1

    def test_no_state_image_is_none(self):
        assert AnimationPlayer().image is None

    def test_default_fps_applies_on_registration(self, idle_png: Path):
        player = AnimationPlayer(fps=4)
        player.play("idle", AnimationSheet(idle_png, 1, 4))
        player.update(250.0)
        assert player.frame_index == 1
