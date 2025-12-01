"""Tests for platform utilities module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


class TestPlatformDetection:
    """Test platform detection functions."""

    def test_is_macos_returns_bool(self):
        """is_macos returns boolean."""
        from installer.platform_utils import is_macos

        result = is_macos()
        assert isinstance(result, bool)

    def test_is_linux_returns_bool(self):
        """is_linux returns boolean."""
        from installer.platform_utils import is_linux

        result = is_linux()
        assert isinstance(result, bool)

    def test_is_windows_returns_bool(self):
        """is_windows returns boolean."""
        from installer.platform_utils import is_windows

        result = is_windows()
        assert isinstance(result, bool)

    def test_is_wsl_returns_bool(self):
        """is_wsl returns boolean."""
        from installer.platform_utils import is_wsl

        result = is_wsl()
        assert isinstance(result, bool)

    @patch("platform.system", return_value="Darwin")
    def test_is_macos_with_darwin(self, mock_system):
        """is_macos returns True on Darwin."""
        from installer.platform_utils import is_macos

        assert is_macos() is True

    @patch("platform.system", return_value="Linux")
    def test_is_linux_with_linux(self, mock_system):
        """is_linux returns True on Linux."""
        from installer.platform_utils import is_linux

        assert is_linux() is True

    @patch("platform.system", return_value="Windows")
    def test_is_windows_with_windows(self, mock_system):
        """is_windows returns True on Windows."""
        from installer.platform_utils import is_windows

        assert is_windows() is True


class TestCommandExists:
    """Test command_exists function."""

    def test_command_exists_finds_common_commands(self):
        """command_exists finds common system commands."""
        from installer.platform_utils import command_exists

        # These should exist on any Unix-like system
        assert command_exists("ls") is True
        assert command_exists("cat") is True

    def test_command_exists_returns_false_for_nonexistent(self):
        """command_exists returns False for nonexistent commands."""
        from installer.platform_utils import command_exists

        assert command_exists("definitely_not_a_real_command_12345") is False


class TestPackageManager:
    """Test package manager detection."""

    def test_get_package_manager_returns_string_or_none(self):
        """get_package_manager returns string or None."""
        from installer.platform_utils import get_package_manager

        result = get_package_manager()
        assert result is None or isinstance(result, str)


class TestPlatformDirs:
    """Test platformdirs integration."""

    def test_get_config_dir_returns_path(self):
        """get_config_dir returns a Path."""
        from installer.platform_utils import get_config_dir

        result = get_config_dir()
        assert isinstance(result, Path)

    def test_get_data_dir_returns_path(self):
        """get_data_dir returns a Path."""
        from installer.platform_utils import get_data_dir

        result = get_data_dir()
        assert isinstance(result, Path)


class TestShellConfig:
    """Test shell configuration utilities."""

    def test_get_shell_config_files_returns_list(self):
        """get_shell_config_files returns list of paths."""
        from installer.platform_utils import get_shell_config_files

        result = get_shell_config_files()
        assert isinstance(result, list)
        for path in result:
            assert isinstance(path, Path)

    def test_shell_config_files_includes_common_shells(self):
        """get_shell_config_files includes common shell configs."""
        from installer.platform_utils import get_shell_config_files

        result = get_shell_config_files()
        path_names = [p.name for p in result]
        # Should include at least one of these common configs
        common_configs = [".bashrc", ".zshrc", "config.fish"]
        assert any(name in path_names for name in common_configs)


class TestPlatformSuffix:
    """Test platform suffix generation."""

    def test_get_platform_suffix_returns_string(self):
        """get_platform_suffix returns a string."""
        from installer.platform_utils import get_platform_suffix

        result = get_platform_suffix()
        assert isinstance(result, str)
        assert "-" in result  # e.g., "linux-x86_64"

    @patch("platform.system", return_value="Linux")
    @patch("platform.machine", return_value="x86_64")
    def test_get_platform_suffix_linux_x86_64(self, mock_machine, mock_system):
        """get_platform_suffix returns correct format for Linux x86_64."""
        from installer.platform_utils import get_platform_suffix

        result = get_platform_suffix()
        assert result == "linux-x86_64"

    @patch("platform.system", return_value="Darwin")
    @patch("platform.machine", return_value="arm64")
    def test_get_platform_suffix_darwin_arm64(self, mock_machine, mock_system):
        """get_platform_suffix returns correct format for macOS arm64."""
        from installer.platform_utils import get_platform_suffix

        result = get_platform_suffix()
        assert result == "darwin-arm64"
