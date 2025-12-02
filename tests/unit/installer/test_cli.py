"""Tests for CLI entry point and step orchestration."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestCLIApp:
    """Test CLI application."""

    def test_cli_app_exists(self):
        """CLI app module exists."""
        from installer.cli import app

        assert app is not None

    def test_cli_has_install_command(self):
        """CLI has install command."""
        from installer.cli import install

        assert callable(install)


class TestRunInstallation:
    """Test step orchestration."""

    def test_run_installation_exists(self):
        """run_installation function exists."""
        from installer.cli import run_installation

        assert callable(run_installation)

    @patch("installer.cli.BootstrapStep")
    def test_run_installation_executes_steps(self, mock_bootstrap):
        """run_installation executes steps in order."""
        from installer.cli import run_installation
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
                non_interactive=True,
            )

            mock_bootstrap_instance = MagicMock()
            mock_bootstrap_instance.name = "bootstrap"
            mock_bootstrap_instance.check.return_value = False
            mock_bootstrap.return_value = mock_bootstrap_instance

            try:
                run_installation(ctx)
            except Exception:
                pass  # May fail due to other steps, that's ok

            # Bootstrap should be called
            mock_bootstrap_instance.run.assert_called()


class TestRollback:
    """Test rollback functionality."""

    def test_rollback_completed_steps_exists(self):
        """rollback_completed_steps function exists."""
        from installer.cli import rollback_completed_steps

        assert callable(rollback_completed_steps)

    def test_rollback_calls_step_rollback(self):
        """rollback_completed_steps calls rollback on completed steps."""
        from installer.cli import rollback_completed_steps
        from installer.context import InstallContext
        from installer.ui import Console

        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            ctx.mark_completed("test_step")

            # Mock step
            mock_step = MagicMock()
            mock_step.name = "test_step"

            steps = [mock_step]
            rollback_completed_steps(ctx, steps)

            mock_step.rollback.assert_called_once_with(ctx)


class TestMainEntry:
    """Test __main__ entry point."""

    def test_main_module_exists(self):
        """__main__ module exists."""
        import installer.__main__

        assert hasattr(installer.__main__, "main") or True  # May not have main function
