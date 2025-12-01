"""Tests for shell config step."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestShellConfigStep:
    """Test ShellConfigStep class."""

    def test_shell_config_step_has_correct_name(self):
        """ShellConfigStep has name 'shell_config'."""
        from installer.steps.shell_config import ShellConfigStep

        step = ShellConfigStep()
        assert step.name == "shell_config"

    def test_shell_config_check_returns_bool(self):
        """ShellConfigStep.check returns boolean."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            result = step.check(ctx)
            assert isinstance(result, bool)

    @patch("installer.steps.shell_config.get_shell_config_files")
    def test_shell_config_run_adds_alias(self, mock_get_files):
        """ShellConfigStep.run adds ccp alias to shell configs."""
        from installer.context import InstallContext
        from installer.steps.shell_config import ShellConfigStep
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create shell config file
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text("# existing config\n")
            mock_get_files.return_value = [bashrc]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            content = bashrc.read_text()
            # Should contain alias
            assert "ccp" in content or "claude-code" in content

    def test_shell_config_handles_fish_syntax(self):
        """ShellConfigStep uses fish syntax for fish shell."""
        from installer.steps.shell_config import get_alias_line

        bash_line = get_alias_line("bash")
        fish_line = get_alias_line("fish")

        assert "alias" in bash_line
        assert "function" in fish_line or "alias" in fish_line


class TestAliasHelpers:
    """Test shell alias helper functions."""

    def test_get_alias_line_returns_string(self):
        """get_alias_line returns a string."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_alias_contains_ccp(self):
        """Alias line contains ccp command."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert "ccp" in result

    def test_alias_builds_rules(self):
        """Alias runs build.py to compile rules."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert "build.py" in result
        assert ".claude/rules/build.py" in result

    def test_alias_uses_dotenvx(self):
        """Alias uses dotenvx to load environment variables."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert "dotenvx run claude" in result

    def test_alias_uses_nvm(self):
        """Alias sets Node.js version via nvm."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert "nvm use 22" in result

    def test_alias_detects_ccp_project(self):
        """Alias checks for CCP project before running."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("bash")
        assert ".claude/rules/build.py" in result
        assert "/workspaces" in result

    def test_fish_alias_uses_correct_syntax(self):
        """Fish alias uses 'and' instead of '&&' and fish-specific syntax."""
        from installer.steps.shell_config import get_alias_line

        result = get_alias_line("fish")
        # Fish uses 'and' for chaining commands, 'test' instead of '[]'
        assert "test -f" in result or "and" in result
        assert "dotenvx run claude" in result
        assert "nvm use 22" in result
