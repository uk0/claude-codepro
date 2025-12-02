"""Tests for installer UI abstraction layer."""

from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest


class TestConsole:
    """Test Console wrapper class."""

    def test_console_status_outputs_blue_text(self):
        """Console.status should output styled message."""
        from installer.ui import Console

        console = Console()
        # Should not raise
        console.status("Installing...")

    def test_console_success_outputs_green_checkmark(self):
        """Console.success should output green checkmark message."""
        from installer.ui import Console

        console = Console()
        console.success("Installed successfully")

    def test_console_warning_outputs_yellow_warning(self):
        """Console.warning should output yellow warning message."""
        from installer.ui import Console

        console = Console()
        console.warning("This might cause issues")

    def test_console_error_outputs_red_error(self):
        """Console.error should output red error message."""
        from installer.ui import Console

        console = Console()
        console.error("Installation failed")

    def test_console_section_creates_panel(self):
        """Console.section should create a bordered panel."""
        from installer.ui import Console

        console = Console()
        console.section("Installing Dependencies")

    def test_console_progress_context_manager(self):
        """Console.progress should return a context manager."""
        from installer.ui import Console

        console = Console()
        with console.progress(total=10, description="Downloading") as progress:
            progress.advance(5)
            progress.advance(5)


class TestConsoleNonInteractive:
    """Test Console in non-interactive mode."""

    def test_confirm_returns_default_in_non_interactive(self):
        """In non-interactive mode, confirm returns default."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        assert console.confirm("Continue?", default=True) is True
        assert console.confirm("Continue?", default=False) is False

    def test_select_returns_first_in_non_interactive(self):
        """In non-interactive mode, select returns first choice."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        result = console.select("Choose:", choices=["A", "B", "C"])
        assert result == "A"

    def test_input_returns_default_in_non_interactive(self):
        """In non-interactive mode, input returns default."""
        from installer.ui import Console

        console = Console(non_interactive=True)
        result = console.input("Enter value:", default="default_value")
        assert result == "default_value"


class TestConsoleTable:
    """Test Console table functionality."""

    def test_console_table_renders_data(self):
        """Console.table should render tabular data."""
        from installer.ui import Console

        console = Console()
        data = [
            {"Step": "Bootstrap", "Status": "Complete"},
            {"Step": "GitSetup", "Status": "Pending"},
        ]
        console.table(data, title="Installation Status")
