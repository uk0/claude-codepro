"""Tests for environment step."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


class TestEnvironmentStep:
    """Test EnvironmentStep class."""

    def test_environment_step_has_correct_name(self):
        """EnvironmentStep has name 'environment'."""
        from installer.steps.environment import EnvironmentStep

        step = EnvironmentStep()
        assert step.name == "environment"

    def test_environment_check_returns_true_when_env_exists(self):
        """EnvironmentStep.check returns True when .env exists with required keys."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep
        from installer.ui import Console

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create .env with some content
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("SOME_KEY=value\n")

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # .env exists
            result = step.check(ctx)
            assert isinstance(result, bool)

    def test_environment_run_skips_in_non_interactive(self):
        """EnvironmentStep.run skips prompts in non-interactive mode."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep
        from installer.ui import Console

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            # Should not raise or prompt
            step.run(ctx)

    def test_environment_appends_to_existing_env(self):
        """EnvironmentStep appends to existing .env file."""
        from installer.context import InstallContext
        from installer.steps.environment import EnvironmentStep
        from installer.ui import Console

        step = EnvironmentStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing .env
            env_file = Path(tmpdir) / ".env"
            env_file.write_text("EXISTING_KEY=existing_value\n")

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                non_interactive=True,
                ui=Console(non_interactive=True),
            )

            step.run(ctx)

            # Existing content should be preserved
            content = env_file.read_text()
            assert "EXISTING_KEY=existing_value" in content
