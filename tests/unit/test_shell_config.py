"""Unit tests for scripts/lib/shell_config.py."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from lib.shell_config import add_shell_alias


class TestAddShellAlias:
    """Test add_shell_alias function."""

    def test_add_shell_alias_creates_new_alias_when_none_exists(self):
        """Test that add_shell_alias creates new alias when file has no alias."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shell_file = Path(tmpdir) / ".bashrc"
            shell_file.write_text("# Existing content\nexport PATH=/usr/bin\n")

            add_shell_alias(
                shell_file,
                'alias ccp="cd /project && claude"',
                ".bashrc",
                "ccp",
                Path("/project"),
            )

            content = shell_file.read_text()
            assert "# Claude CodePro alias - /project" in content
            assert 'alias ccp="cd /project && claude"' in content

    def test_add_shell_alias_updates_existing_marker_section(self):
        """Test that add_shell_alias updates alias when marker exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shell_file = Path(tmpdir) / ".bashrc"
            shell_file.write_text(
                "# Existing content\n"
                "# Claude CodePro alias - /project\n"
                'alias ccp="cd /old && claude"\n'
                "export PATH=/usr/bin\n"
            )

            add_shell_alias(
                shell_file,
                'alias ccp="cd /new && claude"',
                ".bashrc",
                "ccp",
                Path("/project"),
            )

            content = shell_file.read_text()
            assert 'alias ccp="cd /new && claude"' in content
            assert 'alias ccp="cd /old && claude"' not in content

    def test_add_shell_alias_replaces_existing_alias_without_marker(self):
        """Test that add_shell_alias updates existing alias that doesn't have our marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shell_file = Path(tmpdir) / ".bashrc"
            shell_file.write_text(
                "# Existing content\n"
                'alias ccp="some other command"\n'
                "export PATH=/usr/bin\n"
            )

            add_shell_alias(
                shell_file,
                'alias ccp="cd /project && claude"',
                ".bashrc",
                "ccp",
                Path("/project"),
            )

            content = shell_file.read_text()
            assert "# Claude CodePro alias - /project" in content
            assert 'alias ccp="cd /project && claude"' in content
            assert 'alias ccp="some other command"' not in content

    def test_add_shell_alias_handles_missing_file(self):
        """Test that add_shell_alias handles missing shell file gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shell_file = Path(tmpdir) / ".bashrc"
            # Don't create the file

            # Should not raise exception
            add_shell_alias(
                shell_file,
                'alias ccp="cd /project && claude"',
                ".bashrc",
                "ccp",
                Path("/project"),
            )

            # File should still not exist
            assert not shell_file.exists()

    def test_add_shell_alias_preserves_other_content(self):
        """Test that add_shell_alias preserves other shell file content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            shell_file = Path(tmpdir) / ".zshrc"
            original_content = (
                "# My custom config\n"
                "export PATH=/custom/bin:$PATH\n"
                "alias ll='ls -la'\n"
                "# End of config\n"
            )
            shell_file.write_text(original_content)

            add_shell_alias(
                shell_file,
                'alias ccp="cd /project && claude"',
                ".zshrc",
                "ccp",
                Path("/project"),
            )

            content = shell_file.read_text()
            # Check original content is preserved
            assert "# My custom config" in content
            assert "export PATH=/custom/bin:$PATH" in content
            assert "alias ll='ls -la'" in content
            assert "# End of config" in content
            # Check new alias is added
            assert 'alias ccp="cd /project && claude"' in content
