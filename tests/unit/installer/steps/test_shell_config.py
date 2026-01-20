"""Tests for shell config step."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

from installer.steps.shell_config import (
    CCP_ALIAS_MARKER,
    ShellConfigStep,
    alias_exists_in_file,
    get_alias_line,
    remove_old_alias,
)


class TestShellConfigStep:
    """Test ShellConfigStep class."""

    def test_shell_config_step_has_correct_name(self):
        """ShellConfigStep has name 'shell_config'."""
        step = ShellConfigStep()
        assert step.name == "shell_config"

    def test_shell_config_check_always_returns_false(self):
        """ShellConfigStep.check always returns False to ensure alias updates."""
        from installer.context import InstallContext
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            assert step.check(ctx) is False

    @patch("installer.steps.shell_config.get_shell_config_files")
    def test_shell_config_run_adds_alias(self, mock_get_files):
        """ShellConfigStep.run adds ccp alias to shell configs."""
        from installer.context import InstallContext
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc = Path(tmpdir) / ".bashrc"
            bashrc.write_text("# existing config\n")
            mock_get_files.return_value = [bashrc]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            content = bashrc.read_text()
            assert CCP_ALIAS_MARKER in content
            assert "ccp()" in content  # Function, not alias

    @patch("installer.steps.shell_config.get_shell_config_files")
    def test_shell_config_updates_old_alias(self, mock_get_files):
        """ShellConfigStep.run updates existing alias with new version."""
        from installer.context import InstallContext
        from installer.ui import Console

        step = ShellConfigStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            bashrc = Path(tmpdir) / ".bashrc"
            # Old alias with wrapper.py approach
            bashrc.write_text(f"{CCP_ALIAS_MARKER}\nalias ccp='old wrapper.py version'\n# other config\n")
            mock_get_files.return_value = [bashrc]

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            content = bashrc.read_text()
            # Old alias removed
            assert "wrapper.py" not in content
            # New alias added
            assert ".claude/bin/ccp" in content
            assert CCP_ALIAS_MARKER in content


class TestAliasHelpers:
    """Test alias helper functions."""

    def test_get_alias_line_returns_string(self):
        """get_alias_line returns a string."""
        result = get_alias_line("bash")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_alias_line_bash_contains_function(self):
        """Bash alias line uses ccp() function."""
        result = get_alias_line("bash")
        assert "ccp()" in result
        assert ".claude/bin/ccp" in result
        assert '"$@"' in result  # Arguments forwarding

    def test_get_alias_line_fish_uses_fish_syntax(self):
        """Fish alias line uses fish function syntax."""
        result = get_alias_line("fish")
        assert "function ccp" in result
        assert ".claude/bin/ccp" in result
        assert "test -f" in result
        assert "$argv" in result  # Fish arguments forwarding

    def test_get_alias_line_handles_devcontainer(self):
        """Alias line includes /workspaces fallback for devcontainers."""
        result = get_alias_line("bash")
        assert "/workspaces" in result

    def test_alias_exists_in_file_detects_marker(self):
        """alias_exists_in_file detects alias marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / ".bashrc"
            config.write_text(f"{CCP_ALIAS_MARKER}\nalias ccp='...'\n")
            assert alias_exists_in_file(config) is True

    def test_alias_exists_in_file_detects_alias_without_marker(self):
        """alias_exists_in_file detects alias ccp without marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / ".bashrc"
            config.write_text("alias ccp='something'\n")
            assert alias_exists_in_file(config) is True

    def test_alias_exists_in_file_returns_false_when_missing(self):
        """alias_exists_in_file returns False when not configured."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / ".bashrc"
            config.write_text("# some other config\n")
            assert alias_exists_in_file(config) is False


class TestAliasRemoval:
    """Test alias removal for updates."""

    def test_remove_old_alias_removes_marker_and_alias(self):
        """remove_old_alias removes marker and alias line."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / ".bashrc"
            config.write_text(f"# before\n{CCP_ALIAS_MARKER}\nalias ccp='complex alias'\n# after\n")

            result = remove_old_alias(config)

            assert result is True
            content = config.read_text()
            assert "alias ccp" not in content
            assert CCP_ALIAS_MARKER not in content
            assert "# before" in content
            assert "# after" in content

    def test_remove_old_alias_removes_standalone_alias(self):
        """remove_old_alias removes alias without marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / ".bashrc"
            config.write_text("# config\nalias ccp='something'\n# more\n")

            result = remove_old_alias(config)

            assert result is True
            content = config.read_text()
            assert "alias ccp" not in content

    def test_remove_old_alias_returns_false_when_no_alias(self):
        """remove_old_alias returns False when no alias exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Path(tmpdir) / ".bashrc"
            config.write_text("# just config\n")

            result = remove_old_alias(config)

            assert result is False
