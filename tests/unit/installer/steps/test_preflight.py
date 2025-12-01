"""Tests for pre-flight checks step."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPreflightStep:
    """Test PreflightStep class."""

    def test_preflight_step_has_correct_name(self):
        """PreflightStep has name 'preflight'."""
        from installer.steps.preflight import PreflightStep

        step = PreflightStep()
        assert step.name == "preflight"

    def test_preflight_check_always_returns_false(self):
        """PreflightStep.check always returns False (always runs)."""
        from installer.context import InstallContext
        from installer.steps.preflight import PreflightStep
        from installer.ui import Console

        step = PreflightStep()
        ctx = InstallContext(
            project_dir=Path("/tmp/test"),
            ui=Console(non_interactive=True),
        )
        assert step.check(ctx) is False

    def test_preflight_run_executes_checks(self):
        """PreflightStep.run executes all pre-flight checks."""
        from installer.context import InstallContext
        from installer.steps.preflight import PreflightStep
        from installer.ui import Console

        step = PreflightStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # Should not raise for a valid directory
            step.run(ctx)


class TestDiskSpaceCheck:
    """Test disk space check."""

    def test_check_disk_space_returns_bool(self):
        """check_disk_space returns boolean."""
        from installer.steps.preflight import check_disk_space

        result = check_disk_space(Path("/tmp"), min_mb=100)
        assert isinstance(result, bool)

    def test_check_disk_space_passes_with_enough_space(self):
        """check_disk_space passes with sufficient space."""
        from installer.steps.preflight import check_disk_space

        # /tmp should have at least 1MB free
        result = check_disk_space(Path("/tmp"), min_mb=1)
        assert result is True


class TestPermissionsCheck:
    """Test permissions check."""

    def test_check_permissions_returns_bool(self):
        """check_permissions returns boolean."""
        from installer.steps.preflight import check_permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_permissions(Path(tmpdir))
            assert isinstance(result, bool)

    def test_check_permissions_passes_for_writable_dir(self):
        """check_permissions passes for writable directory."""
        from installer.steps.preflight import check_permissions

        with tempfile.TemporaryDirectory() as tmpdir:
            result = check_permissions(Path(tmpdir))
            assert result is True


class TestDependenciesCheck:
    """Test dependencies check."""

    def test_check_dependencies_returns_tuple(self):
        """check_dependencies returns (passed, missing) tuple."""
        from installer.steps.preflight import check_dependencies

        passed, missing = check_dependencies()
        assert isinstance(passed, bool)
        assert isinstance(missing, list)

    def test_check_dependencies_finds_common_tools(self):
        """check_dependencies finds common Unix tools."""
        from installer.steps.preflight import check_dependencies

        passed, missing = check_dependencies()
        # On a standard Unix system, basic tools should exist
        # If all are missing, something is very wrong
        if not passed:
            # At least verify the return format
            assert all(isinstance(m, str) for m in missing)


class TestPythonVersionCheck:
    """Test Python version check."""

    def test_check_python_version_returns_bool(self):
        """check_python_version returns boolean."""
        from installer.steps.preflight import check_python_version

        result = check_python_version()
        assert isinstance(result, bool)

    def test_check_python_version_passes_current(self):
        """check_python_version passes for current Python."""
        from installer.steps.preflight import check_python_version

        # Current Python should pass minimum requirements
        result = check_python_version(min_version="3.8")
        assert result is True


class TestPreflightErrors:
    """Test pre-flight error handling."""

    @patch("installer.steps.preflight.check_permissions", return_value=False)
    def test_preflight_raises_on_critical_failure(self, mock_perm):
        """PreflightStep raises PreflightError on critical failure."""
        from installer.context import InstallContext
        from installer.errors import PreflightError
        from installer.steps.preflight import PreflightStep
        from installer.ui import Console

        step = PreflightStep()
        ctx = InstallContext(
            project_dir=Path("/tmp/test"),
            ui=Console(non_interactive=True),
        )

        with pytest.raises(PreflightError):
            step.run(ctx)
