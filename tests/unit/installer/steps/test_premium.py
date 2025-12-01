"""Tests for premium features step."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


class TestPremiumStep:
    """Test PremiumStep class."""

    def test_premium_step_has_correct_name(self):
        """PremiumStep has name 'premium'."""
        from installer.steps.premium import PremiumStep

        step = PremiumStep()
        assert step.name == "premium"

    def test_check_returns_true_when_no_premium_key(self):
        """check() returns True when no premium key provided."""
        from installer.context import InstallContext
        from installer.steps.premium import PremiumStep
        from installer.ui import Console

        step = PremiumStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                premium_key=None,
                ui=Console(non_interactive=True),
            )

            # No premium key means skip this step
            assert step.check(ctx) is True

    def test_check_returns_false_when_premium_key_provided(self):
        """check() returns False when premium key is provided."""
        from installer.context import InstallContext
        from installer.steps.premium import PremiumStep
        from installer.ui import Console

        step = PremiumStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                premium_key="TEST-LICENSE-KEY",
                ui=Console(non_interactive=True),
            )

            # Has premium key, need to run
            assert step.check(ctx) is False

    def test_check_returns_true_when_premium_already_installed(self):
        """check() returns True when premium binary already exists."""
        from installer.context import InstallContext
        from installer.steps.premium import PremiumStep
        from installer.ui import Console

        step = PremiumStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)

            # Create premium binary
            bin_dir = project_dir / ".claude" / "bin"
            bin_dir.mkdir(parents=True)
            (bin_dir / "ccp-premium").write_text("binary")

            ctx = InstallContext(
                project_dir=project_dir,
                premium_key="TEST-LICENSE-KEY",
                ui=Console(non_interactive=True),
            )

            assert step.check(ctx) is True


class TestPremiumHelpers:
    """Test premium helper functions."""

    def test_get_platform_binary_name_returns_string(self):
        """get_platform_binary_name returns platform-specific name."""
        from installer.steps.premium import get_platform_binary_name

        name = get_platform_binary_name()
        assert isinstance(name, str)
        assert "ccp-premium" in name

    def test_remove_premium_hooks_from_settings(self):
        """remove_premium_hooks_from_settings removes ccp-premium hooks."""
        from installer.steps.premium import remove_premium_hooks_from_settings

        with tempfile.TemporaryDirectory() as tmpdir:
            settings_file = Path(tmpdir) / "settings.local.json"

            # Create settings with premium hooks
            settings = {
                "hooks": {
                    "PreToolUse": [
                        {"hooks": [{"command": "ccp-premium tdd-enforcer"}]}
                    ],
                    "PostToolUse": [
                        {"hooks": [{"command": "ccp-premium context-monitor"}]}
                    ],
                    "Stop": [
                        {"hooks": [{"command": "ccp-premium rules-hook"}]}
                    ]
                }
            }
            settings_file.write_text(json.dumps(settings))

            result = remove_premium_hooks_from_settings(settings_file)
            assert result is True

            # Check hooks were removed
            updated = json.loads(settings_file.read_text())
            # All hook types should be empty/removed since only premium hooks existed
            assert "hooks" not in updated or not updated.get("hooks")


class TestPremiumRun:
    """Test PremiumStep.run()."""

    def test_run_removes_hooks_when_no_premium(self):
        """run() removes premium hooks for non-premium users."""
        from installer.context import InstallContext
        from installer.steps.premium import PremiumStep
        from installer.ui import Console

        step = PremiumStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            claude_dir = project_dir / ".claude"
            claude_dir.mkdir()

            # Create settings with premium hooks
            settings = {
                "hooks": {
                    "PreToolUse": [
                        {"hooks": [{"command": "ccp-premium tdd-enforcer"}]}
                    ]
                }
            }
            settings_file = claude_dir / "settings.local.json"
            settings_file.write_text(json.dumps(settings))

            ctx = InstallContext(
                project_dir=project_dir,
                premium_key=None,
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            # Check hooks were removed
            updated = json.loads(settings_file.read_text())
            assert "hooks" not in updated or not updated.get("hooks")

    def test_run_validates_license_key(self):
        """run() validates license key with API."""
        from installer.context import InstallContext
        from installer.steps.premium import PremiumStep
        from installer.ui import Console

        step = PremiumStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                premium_key="INVALID-KEY",
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            # Mock the license validation to fail
            with patch("installer.steps.premium.validate_license_key") as mock_validate:
                mock_validate.return_value = (False, "Invalid license key")
                step.run(ctx)

                mock_validate.assert_called_once_with("INVALID-KEY")

    def test_run_downloads_binary_on_valid_license(self):
        """run() downloads premium binary on valid license."""
        from installer.context import InstallContext
        from installer.steps.premium import PremiumStep
        from installer.ui import Console

        step = PremiumStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                premium_key="VALID-KEY",
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            # Mock validation and download
            with patch("installer.steps.premium.validate_license_key") as mock_validate:
                mock_validate.return_value = (True, "License valid")
                with patch("installer.steps.premium.download_premium_binary") as mock_download:
                    mock_download.return_value = (True, str(project_dir / ".claude" / "bin" / "ccp-premium"))
                    step.run(ctx)

                    mock_download.assert_called_once()

    def test_run_saves_license_to_env(self):
        """run() saves valid license to .env file."""
        from installer.context import InstallContext
        from installer.steps.premium import PremiumStep
        from installer.ui import Console

        step = PremiumStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir)
            ctx = InstallContext(
                project_dir=project_dir,
                premium_key="VALID-KEY",
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            # Mock validation and download
            with patch("installer.steps.premium.validate_license_key") as mock_validate:
                mock_validate.return_value = (True, "License valid")
                with patch("installer.steps.premium.download_premium_binary") as mock_download:
                    mock_download.return_value = (True, str(project_dir / ".claude" / "bin" / "ccp-premium"))
                    step.run(ctx)

                    # Check .env file
                    env_file = project_dir / ".env"
                    assert env_file.exists()
                    content = env_file.read_text()
                    assert "CCP_LICENSE_KEY=VALID-KEY" in content
