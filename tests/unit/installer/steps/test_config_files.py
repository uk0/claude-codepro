"""Tests for config files step."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest


class TestConfigFilesStep:
    """Test ConfigFilesStep class."""

    def test_config_files_step_has_correct_name(self):
        """ConfigFilesStep has name 'config_files'."""
        from installer.steps.config_files import ConfigFilesStep

        step = ConfigFilesStep()
        assert step.name == "config_files"

    def test_config_files_generates_settings(self):
        """ConfigFilesStep generates settings.local.json from template."""
        from installer.context import InstallContext
        from installer.steps.config_files import ConfigFilesStep
        from installer.ui import Console

        step = ConfigFilesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create template
            template = {"projectDir": "{{PROJECT_DIR}}", "setting": "value"}
            (claude_dir / "settings.local.template.json").write_text(json.dumps(template))

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            # Check settings.local.json was created with substitution
            settings_file = claude_dir / "settings.local.json"
            assert settings_file.exists()
            settings = json.loads(settings_file.read_text())
            assert settings["projectDir"] == str(project_dir)

    def test_config_files_removes_python_settings_when_disabled(self):
        """ConfigFilesStep removes Python settings when install_python=False."""
        from installer.context import InstallContext
        from installer.steps.config_files import ConfigFilesStep
        from installer.ui import Console

        step = ConfigFilesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create template with Python hook
            template = {
                "hooks": {
                    "PostToolUse": [{"hooks": [{"command": "file_checker_python.py"}]}]
                },
                "permissions": {"allow": ["Bash(pytest:*)", "Bash(ls:*)"]}
            }
            (claude_dir / "settings.local.template.json").write_text(json.dumps(template))

            ctx = InstallContext(
                project_dir=project_dir,
                install_python=False,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            settings_file = claude_dir / "settings.local.json"
            settings = json.loads(settings_file.read_text())

            # Python hook should be removed
            hooks = settings.get("hooks", {}).get("PostToolUse", [])
            for group in hooks:
                for hook in group.get("hooks", []):
                    assert "file_checker_python.py" not in hook.get("command", "")


class TestMCPConfigMerge:
    """Test MCP config merging."""

    def test_merge_mcp_config_preserves_existing(self):
        """Merging MCP config preserves existing servers."""
        from installer.steps.config_files import merge_mcp_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".mcp.json"

            # Existing config
            existing = {"mcpServers": {"existing": {"command": "existing-server"}}}
            config_file.write_text(json.dumps(existing))

            # New config
            new_config = {"mcpServers": {"new": {"command": "new-server"}}}

            merge_mcp_config(config_file, new_config)

            result = json.loads(config_file.read_text())
            # Both servers should exist
            assert "existing" in result["mcpServers"]
            assert "new" in result["mcpServers"]

    def test_merge_mcp_config_creates_new(self):
        """Merging creates new config if none exists."""
        from installer.steps.config_files import merge_mcp_config

        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / ".mcp.json"

            new_config = {"mcpServers": {"new": {"command": "new-server"}}}

            merge_mcp_config(config_file, new_config)

            result = json.loads(config_file.read_text())
            assert "new" in result["mcpServers"]


class TestDirectoryInstallation:
    """Test .cipher and .qlty directory installation."""

    def test_install_cipher_directory(self):
        """ConfigFilesStep installs .cipher directory."""
        from unittest.mock import patch

        from installer.context import InstallContext
        from installer.steps.config_files import ConfigFilesStep
        from installer.ui import Console

        step = ConfigFilesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create template
            template = {"setting": "value"}
            (claude_dir / "settings.local.template.json").write_text(json.dumps(template))

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
                local_mode=True,
                local_repo_dir=Path("/fake"),
            )

            # Mock download_directory to simulate installation
            with patch("installer.steps.config_files.download_directory") as mock_download:
                mock_download.return_value = 3  # 3 files installed
                step.run(ctx)

                # Should have called download_directory for .cipher
                calls = mock_download.call_args_list
                cipher_calls = [c for c in calls if ".cipher" in str(c)]
                assert len(cipher_calls) >= 1, "Should install .cipher directory"

    def test_install_qlty_directory(self):
        """ConfigFilesStep installs .qlty directory."""
        from unittest.mock import patch

        from installer.context import InstallContext
        from installer.steps.config_files import ConfigFilesStep
        from installer.ui import Console

        step = ConfigFilesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create template
            template = {"setting": "value"}
            (claude_dir / "settings.local.template.json").write_text(json.dumps(template))

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
                local_mode=True,
                local_repo_dir=Path("/fake"),
            )

            # Mock download_directory to simulate installation
            with patch("installer.steps.config_files.download_directory") as mock_download:
                mock_download.return_value = 2  # 2 files installed
                step.run(ctx)

                # Should have called download_directory for .qlty
                calls = mock_download.call_args_list
                qlty_calls = [c for c in calls if ".qlty" in str(c)]
                assert len(qlty_calls) >= 1, "Should install .qlty directory"

    def test_skips_existing_directories(self):
        """ConfigFilesStep skips directories that already exist."""
        from unittest.mock import patch

        from installer.context import InstallContext
        from installer.steps.config_files import ConfigFilesStep
        from installer.ui import Console

        step = ConfigFilesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create template
            template = {"setting": "value"}
            (claude_dir / "settings.local.template.json").write_text(json.dumps(template))

            # Pre-create directories
            (project_dir / ".cipher").mkdir()
            (project_dir / ".qlty").mkdir()

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
                local_mode=True,
                local_repo_dir=Path("/fake"),
            )

            # Mock download_directory
            with patch("installer.steps.config_files.download_directory") as mock_download:
                mock_download.return_value = 0
                step.run(ctx)

                # Should NOT call download_directory for existing dirs
                calls = mock_download.call_args_list
                cipher_calls = [c for c in calls if ".cipher" in str(c)]
                qlty_calls = [c for c in calls if ".qlty" in str(c)]
                assert len(cipher_calls) == 0, "Should skip existing .cipher"
                assert len(qlty_calls) == 0, "Should skip existing .qlty"


class TestMCPConfigInstallation:
    """Test MCP config file installation and merging."""

    def test_installs_mcp_json(self):
        """ConfigFilesStep installs .mcp.json."""
        from unittest.mock import patch

        from installer.context import InstallContext
        from installer.steps.config_files import ConfigFilesStep
        from installer.ui import Console

        step = ConfigFilesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create template
            template = {"setting": "value"}
            (claude_dir / "settings.local.template.json").write_text(json.dumps(template))

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
                local_mode=True,
                local_repo_dir=Path("/fake"),
            )

            # Mock download_file to return MCP config content
            with patch("installer.steps.config_files.download_directory") as mock_dir:
                mock_dir.return_value = 0
                with patch("installer.steps.config_files.download_file") as mock_download:
                    def fake_download(path, dest, config, progress_callback=None):
                        if ".mcp.json" in path:
                            dest.write_text(json.dumps({"mcpServers": {"new": {"command": "test"}}}))
                            return True
                        return False
                    mock_download.side_effect = fake_download
                    step.run(ctx)

                    # Should have called download_file for .mcp.json
                    mcp_calls = [c for c in mock_download.call_args_list if ".mcp.json" in str(c)]
                    assert len(mcp_calls) >= 1, "Should install .mcp.json"

    def test_installs_mcp_funnel_json(self):
        """ConfigFilesStep installs .mcp-funnel.json."""
        from unittest.mock import patch

        from installer.context import InstallContext
        from installer.steps.config_files import ConfigFilesStep
        from installer.ui import Console

        step = ConfigFilesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create template
            template = {"setting": "value"}
            (claude_dir / "settings.local.template.json").write_text(json.dumps(template))

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
                local_mode=True,
                local_repo_dir=Path("/fake"),
            )

            # Mock download_file to return MCP funnel config
            with patch("installer.steps.config_files.download_directory") as mock_dir:
                mock_dir.return_value = 0
                with patch("installer.steps.config_files.download_file") as mock_download:
                    def fake_download(path, dest, config, progress_callback=None):
                        if ".mcp-funnel.json" in path:
                            dest.write_text(json.dumps({"servers": {"test": {}}}))
                            return True
                        return False
                    mock_download.side_effect = fake_download
                    step.run(ctx)

                    # Should have called download_file for .mcp-funnel.json
                    funnel_calls = [c for c in mock_download.call_args_list if ".mcp-funnel.json" in str(c)]
                    assert len(funnel_calls) >= 1, "Should install .mcp-funnel.json"

    def test_merges_mcp_config_with_existing(self):
        """ConfigFilesStep merges new MCP config with existing."""
        from unittest.mock import patch

        from installer.context import InstallContext
        from installer.steps.config_files import ConfigFilesStep
        from installer.ui import Console

        step = ConfigFilesStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create template
            template = {"setting": "value"}
            (claude_dir / "settings.local.template.json").write_text(json.dumps(template))

            # Create existing MCP config
            existing_mcp = {"mcpServers": {"user-server": {"command": "my-tool"}}}
            (project_dir / ".mcp.json").write_text(json.dumps(existing_mcp))

            ctx = InstallContext(
                project_dir=project_dir,
                ui=Console(non_interactive=True),
                local_mode=True,
                local_repo_dir=Path("/fake"),
            )

            # Mock downloads
            with patch("installer.steps.config_files.download_directory") as mock_dir:
                mock_dir.return_value = 0
                with patch("installer.steps.config_files.download_file") as mock_download:
                    def fake_download(path, dest, config, progress_callback=None):
                        if ".mcp.json" in path:
                            dest.write_text(json.dumps({"mcpServers": {"new-server": {"command": "new-tool"}}}))
                            return True
                        return False
                    mock_download.side_effect = fake_download
                    step.run(ctx)

                    # Check merged result
                    mcp_file = project_dir / ".mcp.json"
                    result = json.loads(mcp_file.read_text())
                    assert "user-server" in result["mcpServers"], "Existing server preserved"
                    assert "new-server" in result["mcpServers"], "New server added"
