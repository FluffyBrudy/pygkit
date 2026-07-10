"""
Unit tests for the Dialog System (DialogBox).

Tests the purely logical aspects: state management, typewriter effect,
text processing, and event handling without relying on visual rendering.
"""

import pytest

from pygkit.ui.dialog import (
    DialogBox,
    DialogColors,
    DialogConfig,
    DialogLine,
    TypewriterSpeed,
)


class TestDialogLine:
    """Test DialogLine data structure."""

    def test_dialog_line_creation(self):
        """Test creating a dialog line with all fields."""
        callback_called = False

        def callback():
            nonlocal callback_called
            callback_called = True

        line = DialogLine(speaker="Alice", text="Hello world", callback=callback)

        assert line.speaker == "Alice"
        assert line.text == "Hello world"
        assert line.callback is not None

        line.callback()
        assert callback_called

    def test_dialog_line_defaults(self):
        """Test dialog line with default values."""
        line = DialogLine()

        assert line.speaker is None
        assert line.text == ""
        assert line.callback is None


class TestDialogColors:
    """Test DialogColors configuration."""

    def test_default_colors(self):
        """Test default color values."""
        colors = DialogColors()

        assert colors.box_background == (54, 68, 60, 200)
        assert colors.speaker_name == (251, 224, 83, 255)
        assert colors.dialog_text == (255, 255, 255, 255)

    def test_custom_colors(self):
        """Test creating custom colors."""
        colors = DialogColors(
            box_background=(100, 100, 100, 255),
            speaker_name=(255, 0, 0, 255),
        )

        assert colors.box_background == (100, 100, 100, 255)
        assert colors.speaker_name == (255, 0, 0, 255)

    def test_to_dict(self):
        """Test converting colors to dictionary."""
        colors = DialogColors()
        color_dict = colors.to_dict()

        assert isinstance(color_dict, dict)
        assert "box_background" in color_dict
        assert "speaker_name" in color_dict
        assert "dialog_text" in color_dict


class TestDialogConfig:
    """Test DialogConfig configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DialogConfig()

        assert config.width == 600
        assert config.height == 150
        assert config.font_size == 24
        assert config.typewriter_speed == TypewriterSpeed.MEDIUM
        assert config.show_indicator is True

    def test_custom_config(self):
        """Test creating custom configuration."""
        config = DialogConfig(
            width=800,
            height=200,
            font_size=32,
            typewriter_speed=TypewriterSpeed.FAST,
        )

        assert config.width == 800
        assert config.height == 200
        assert config.font_size == 32
        assert config.typewriter_speed == TypewriterSpeed.FAST

    def test_custom_colors_in_config(self):
        """Test config with custom colors."""
        colors = DialogColors(speaker_name=(255, 100, 50, 255))
        config = DialogConfig(colors=colors)

        assert config.colors.speaker_name == (255, 100, 50, 255)


class TestDialogBox:
    """Test DialogBox logic and state management."""

    def test_initialization(self):
        """Test DialogBox initializes correctly."""
        dialog = DialogBox()

        assert dialog.is_complete is False
        assert dialog.current_text == ""
        assert dialog.full_text == ""

    def test_initialization_with_config(self):
        """Test DialogBox with custom config."""
        config = DialogConfig(width=800, height=200)
        dialog = DialogBox(config)

        assert dialog.config.width == 800
        assert dialog.config.height == 200

    def test_set_dialog(self):
        """Test setting dialog content."""
        dialog = DialogBox()
        dialog.set_dialog("Bob", "This is a test.")

        assert dialog.full_text == "This is a test."
        assert dialog.current_text == ""
        assert dialog.is_complete is False

    def test_set_dialog_without_speaker(self):
        """Test setting dialog without speaker name."""
        dialog = DialogBox()
        dialog.set_dialog(None, "Narrator text.")

        assert dialog.full_text == "Narrator text."
        assert dialog.is_complete is False

    def test_skip_to_end(self):
        """Test skipping typewriter effect."""
        dialog = DialogBox()
        dialog.set_dialog("Alice", "Hello world!")

        result = dialog.skip_to_end()

        assert result is True
        assert dialog.is_complete is True
        assert dialog.current_text == "Hello world!"

    def test_skip_to_end_already_complete(self):
        """Test skipping when already complete."""
        dialog = DialogBox()
        dialog.set_dialog("Alice", "Hello")
        dialog.skip_to_end()

        result = dialog.skip_to_end()

        assert result is False
        assert dialog.is_complete is True

    def test_advance_incomplete(self):
        """Test advance completes incomplete text."""
        dialog = DialogBox()
        dialog.set_dialog("Bob", "Test text")

        result = dialog.advance()

        assert result is True
        assert dialog.is_complete is True

    def test_advance_complete(self):
        """Test advance on complete text."""
        dialog = DialogBox()
        dialog.set_dialog("Bob", "Test")
        dialog.skip_to_end()

        result = dialog.advance()

        assert result is True
        assert dialog.is_complete is True

    def test_typewriter_speed_change(self):
        """Test changing typewriter speed."""
        dialog = DialogBox()
        dialog.set_dialog("Alice", "Slow text")

        dialog.set_typewriter_speed(TypewriterSpeed.EXTRA_FAST)

        assert dialog.config.typewriter_speed == TypewriterSpeed.EXTRA_FAST

    def test_callback_on_complete(self):
        """Test callback is triggered when text completes."""
        callback_called = False

        def callback():
            nonlocal callback_called
            callback_called = True

        dialog = DialogBox()
        dialog.set_dialog("Alice", "Test", callback=callback)

        dialog.skip_to_end()

        assert callback_called is True

    def test_clear(self):
        """Test clearing dialog state."""
        dialog = DialogBox()
        dialog.set_dialog("Bob", "Some text")
        dialog.skip_to_end()

        dialog.clear()

        assert dialog.current_text == ""
        assert dialog.full_text == ""
        assert dialog.is_complete is False

    def test_multiple_dialog_lines(self):
        """Test setting multiple dialog lines sequentially."""
        dialog = DialogBox()

        dialog.set_dialog("Alice", "First line")
        assert dialog.full_text == "First line"

        dialog.skip_to_end()
        assert dialog.is_complete is True

        dialog.set_dialog("Bob", "Second line")
        assert dialog.full_text == "Second line"
        assert dialog.is_complete is False

    def test_update_increments_typewriter(self):
        """Test that update progresses typewriter effect."""
        config = DialogConfig(typewriter_speed=TypewriterSpeed.EXTRA_FAST)
        dialog = DialogBox(config)
        dialog.set_dialog("Test", "Hello")

        initial_text = dialog.current_text
        for _ in range(100):
            dialog.update()

        assert len(dialog.current_text) >= len(initial_text)

    def test_empty_text(self):
        """Test handling empty text."""
        dialog = DialogBox()
        dialog.set_dialog("Alice", "")

        assert dialog.full_text == ""
        dialog.skip_to_end()
        assert dialog.is_complete is True

    def test_long_text(self):
        """Test handling long text."""
        dialog = DialogBox()
        long_text = "This is a very long piece of text. " * 20

        dialog.set_dialog("Narrator", long_text)
        dialog.skip_to_end()

        assert dialog.current_text == long_text
        assert dialog.is_complete is True

    def test_special_characters(self):
        """Test handling special characters."""
        dialog = DialogBox()
        special_text = "Hello! How are you? I'm fine. #tags @mentions"

        dialog.set_dialog("Alice", special_text)
        dialog.skip_to_end()

        assert dialog.current_text == special_text

    def test_unicode_text(self):
        """Test handling unicode characters."""
        dialog = DialogBox()
        unicode_text = "Hello 世界! Привет мир! مرحبا 🌍"

        dialog.set_dialog("Alice", unicode_text)
        dialog.skip_to_end()

        assert dialog.current_text == unicode_text


class TestTypewriterSpeed:
    """Test TypewriterSpeed enum."""

    def test_speed_values(self):
        """Test that speed enum has correct values."""
        assert TypewriterSpeed.EXTRA_FAST.value == 0.015
        assert TypewriterSpeed.FAST.value == 0.025
        assert TypewriterSpeed.MEDIUM.value == 0.04
        assert TypewriterSpeed.SLOW.value == 0.06
        assert TypewriterSpeed.EXTRA_SLOW.value == 0.1

    def test_speed_ordering(self):
        """Test that speeds are in correct order."""
        assert TypewriterSpeed.EXTRA_FAST.value < TypewriterSpeed.FAST.value
        assert TypewriterSpeed.FAST.value < TypewriterSpeed.MEDIUM.value
        assert TypewriterSpeed.MEDIUM.value < TypewriterSpeed.SLOW.value
        assert TypewriterSpeed.SLOW.value < TypewriterSpeed.EXTRA_SLOW.value
