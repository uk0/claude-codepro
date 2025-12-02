"""Tests for InstallContext and error hierarchy."""

from __future__ import annotations

from pathlib import Path

import pytest


class TestInstallContext:
    """Test InstallContext dataclass."""

    def test_context_requires_project_dir(self):
        """InstallContext requires project_dir."""
        from installer.context import InstallContext

        ctx = InstallContext(project_dir=Path("/tmp/test"))
        assert ctx.project_dir == Path("/tmp/test")

    def test_context_has_default_values(self):
        """InstallContext has sensible defaults."""
        from installer.context import InstallContext

        ctx = InstallContext(project_dir=Path("/tmp/test"))
        assert ctx.install_python is True
        assert ctx.premium_key is None
        assert ctx.non_interactive is False
        assert ctx.local_mode is False
        assert ctx.local_repo_dir is None
        assert ctx.completed_steps == []
        assert ctx.config == {}

    def test_mark_completed_adds_step(self):
        """mark_completed adds step to completed_steps."""
        from installer.context import InstallContext

        ctx = InstallContext(project_dir=Path("/tmp/test"))
        ctx.mark_completed("bootstrap")
        assert "bootstrap" in ctx.completed_steps

    def test_mark_completed_is_idempotent(self):
        """mark_completed doesn't add duplicates."""
        from installer.context import InstallContext

        ctx = InstallContext(project_dir=Path("/tmp/test"))
        ctx.mark_completed("bootstrap")
        ctx.mark_completed("bootstrap")
        assert ctx.completed_steps.count("bootstrap") == 1

    def test_is_completed_returns_correct_value(self):
        """is_completed checks if step is done."""
        from installer.context import InstallContext

        ctx = InstallContext(project_dir=Path("/tmp/test"))
        assert ctx.is_completed("bootstrap") is False
        ctx.mark_completed("bootstrap")
        assert ctx.is_completed("bootstrap") is True

    def test_needs_rollback_when_steps_completed(self):
        """needs_rollback returns True when steps completed."""
        from installer.context import InstallContext

        ctx = InstallContext(project_dir=Path("/tmp/test"))
        assert ctx.needs_rollback() is False
        ctx.mark_completed("bootstrap")
        assert ctx.needs_rollback() is True


class TestErrorHierarchy:
    """Test custom exception hierarchy."""

    def test_install_error_is_exception(self):
        """InstallError is a base exception."""
        from installer.errors import InstallError

        assert issubclass(InstallError, Exception)

    def test_fatal_install_error_is_install_error(self):
        """FatalInstallError inherits from InstallError."""
        from installer.errors import FatalInstallError, InstallError

        assert issubclass(FatalInstallError, InstallError)

    def test_config_error_is_install_error(self):
        """ConfigError inherits from InstallError."""
        from installer.errors import ConfigError, InstallError

        assert issubclass(ConfigError, InstallError)

    def test_errors_have_message(self):
        """All errors can have a message."""
        from installer.errors import (
            ConfigError,
            FatalInstallError,
            InstallError,
        )

        for exc_class in [InstallError, FatalInstallError, ConfigError]:
            exc = exc_class("test message")
            assert str(exc) == "test message"
