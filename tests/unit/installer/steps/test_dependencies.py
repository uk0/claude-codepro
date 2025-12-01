"""Tests for dependencies step."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestDependenciesStep:
    """Test DependenciesStep class."""

    def test_dependencies_step_has_correct_name(self):
        """DependenciesStep has name 'dependencies'."""
        from installer.steps.dependencies import DependenciesStep

        step = DependenciesStep()
        assert step.name == "dependencies"

    def test_dependencies_check_returns_false(self):
        """DependenciesStep.check returns False (always runs)."""
        from installer.context import InstallContext
        from installer.steps.dependencies import DependenciesStep
        from installer.ui import Console

        step = DependenciesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # Dependencies always need to be checked
            assert step.check(ctx) is False

    @patch("installer.steps.dependencies.install_nodejs")
    @patch("installer.steps.dependencies.install_claude_code")
    def test_dependencies_run_installs_core(self, mock_claude, mock_nodejs):
        """DependenciesStep installs core dependencies."""
        from installer.context import InstallContext
        from installer.steps.dependencies import DependenciesStep
        from installer.ui import Console

        step = DependenciesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                install_python=False,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            # Core dependencies should be installed
            mock_nodejs.assert_called_once()
            mock_claude.assert_called_once()

    @patch("installer.steps.dependencies.install_nodejs")
    @patch("installer.steps.dependencies.install_uv")
    @patch("installer.steps.dependencies.install_python_tools")
    @patch("installer.steps.dependencies.install_claude_code")
    def test_dependencies_installs_python_when_enabled(
        self, mock_claude, mock_python_tools, mock_uv, mock_nodejs
    ):
        """DependenciesStep installs Python tools when enabled."""
        from installer.context import InstallContext
        from installer.steps.dependencies import DependenciesStep
        from installer.ui import Console

        step = DependenciesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                install_python=True,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            # Python tools should be installed
            mock_uv.assert_called_once()
            mock_python_tools.assert_called_once()


class TestDependencyInstallFunctions:
    """Test individual dependency install functions."""

    def test_install_nodejs_exists(self):
        """install_nodejs function exists."""
        from installer.steps.dependencies import install_nodejs

        assert callable(install_nodejs)

    def test_install_claude_code_exists(self):
        """install_claude_code function exists."""
        from installer.steps.dependencies import install_claude_code

        assert callable(install_claude_code)

    def test_install_uv_exists(self):
        """install_uv function exists."""
        from installer.steps.dependencies import install_uv

        assert callable(install_uv)

    def test_install_python_tools_exists(self):
        """install_python_tools function exists."""
        from installer.steps.dependencies import install_python_tools

        assert callable(install_python_tools)

    def test_install_newman_exists(self):
        """install_newman function exists."""
        from installer.steps.dependencies import install_newman

        assert callable(install_newman)

    def test_install_dotenvx_exists(self):
        """install_dotenvx function exists."""
        from installer.steps.dependencies import install_dotenvx

        assert callable(install_dotenvx)


class TestNewmanDotenvxInstall:
    """Test newman and dotenvx installation."""

    @patch("installer.steps.dependencies.command_exists")
    @patch("subprocess.run")
    def test_install_newman_calls_npm(self, mock_run, mock_cmd_exists):
        """install_newman calls npm install."""
        from installer.steps.dependencies import install_newman

        mock_cmd_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = install_newman()

        # Should call npm install
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "npm" in call_args
        assert "newman" in call_args

    @patch("installer.steps.dependencies.command_exists")
    def test_install_newman_skips_if_exists(self, mock_cmd_exists):
        """install_newman skips if already installed."""
        from installer.steps.dependencies import install_newman

        mock_cmd_exists.return_value = True

        result = install_newman()

        assert result is True

    @patch("installer.steps.dependencies.command_exists")
    @patch("subprocess.run")
    def test_install_dotenvx_calls_npm(self, mock_run, mock_cmd_exists):
        """install_dotenvx calls npm install."""
        from installer.steps.dependencies import install_dotenvx

        mock_cmd_exists.return_value = False
        mock_run.return_value = MagicMock(returncode=0)

        result = install_dotenvx()

        # Should call npm install
        mock_run.assert_called()
        call_args = mock_run.call_args[0][0]
        assert "npm" in call_args
        assert "@dotenvx/dotenvx" in call_args

    @patch("installer.steps.dependencies.command_exists")
    def test_install_dotenvx_skips_if_exists(self, mock_cmd_exists):
        """install_dotenvx skips if already installed."""
        from installer.steps.dependencies import install_dotenvx

        mock_cmd_exists.return_value = True

        result = install_dotenvx()

        assert result is True
