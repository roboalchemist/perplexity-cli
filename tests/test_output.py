"""Unit tests for output formatting functions."""

import pytest
from perplexity import display
from io import StringIO
import sys


class TestDisplayFunction:
    """Tests for the display function."""

    def test_display_default_parameters(self, capsys):
        """Test display with default parameters."""
        display("Test message")
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_display_red_text(self, capsys):
        """Test display with red color."""
        display("Error message", color="red")
        captured = capsys.readouterr()
        assert "Error message" in captured.out

    def test_display_green_text(self, capsys):
        """Test display with green color."""
        display("Success message", color="green")
        captured = capsys.readouterr()
        assert "Success message" in captured.out

    def test_display_yellow_text(self, capsys):
        """Test display with yellow color."""
        display("Warning message", color="yellow")
        captured = capsys.readouterr()
        assert "Warning message" in captured.out

    def test_display_blue_text(self, capsys):
        """Test display with blue color."""
        display("Info message", color="blue")
        captured = capsys.readouterr()
        assert "Info message" in captured.out

    def test_display_bold_text(self, capsys):
        """Test display with bold enabled."""
        display("Bold message", bold=True)
        captured = capsys.readouterr()
        assert "Bold message" in captured.out

    def test_display_with_background_color(self, capsys):
        """Test display with different background colors."""
        display("Message with red background", bg_color="red")
        captured = capsys.readouterr()
        assert "Message with red background" in captured.out

    def test_display_with_all_options(self, capsys):
        """Test display with all options enabled."""
        display(
            "Full formatted message",
            color="white",
            bold=True,
            bg_color="blue"
        )
        captured = capsys.readouterr()
        assert "Full formatted message" in captured.out

    def test_display_empty_message(self, capsys):
        """Test display with empty message."""
        display("")
        captured = capsys.readouterr()
        # Empty message should still print something (newline)
        assert captured.out != ""

    def test_display_special_characters(self, capsys):
        """Test display with special characters."""
        display("Test with emojis: ✓ ✗ ★")
        captured = capsys.readouterr()
        assert "✓" in captured.out

    def test_display_long_message(self, capsys):
        """Test display with a long message."""
        long_message = "A" * 1000
        display(long_message)
        captured = capsys.readouterr()
        assert long_message in captured.out

    def test_display_multiline_message(self, capsys):
        """Test display with multiline message."""
        multiline = "Line 1\nLine 2\nLine 3"
        display(multiline)
        captured = capsys.readouterr()
        assert "Line 1" in captured.out
        assert "Line 2" in captured.out
        assert "Line 3" in captured.out

    def test_display_with_newlines(self, capsys):
        """Test display preserves newlines."""
        display("First line\n\nSecond line")
        captured = capsys.readouterr()
        assert "First line" in captured.out
        assert "Second line" in captured.out
