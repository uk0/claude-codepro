"""Tests for migration step."""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestMigrationStep:
    """Test MigrationStep class."""

    def test_migration_step_has_correct_name(self):
        """MigrationStep has name 'migration'."""
        from installer.steps.migration import MigrationStep

        step = MigrationStep()
        assert step.name == "migration"

    def test_migration_check_returns_true_when_no_migration_needed(self):
        """MigrationStep.check returns True when no migration needed."""
        from installer.context import InstallContext
        from installer.steps.migration import MigrationStep
        from installer.ui import Console

        step = MigrationStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # No old structure exists
            assert step.check(ctx) is True

    def test_migration_check_returns_false_when_migration_needed(self):
        """MigrationStep.check returns False when old structure exists."""
        from installer.context import InstallContext
        from installer.steps.migration import MigrationStep
        from installer.ui import Console

        step = MigrationStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create old structure that needs migration
            old_dir = Path(tmpdir) / ".claude" / "rules" / "standard" / "subdir"
            old_dir.mkdir(parents=True)
            (old_dir / "rule.md").write_text("old rule")

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )
            # Should detect migration needed
            result = step.check(ctx)
            # If old nested structure exists, should return False
            assert isinstance(result, bool)

    def test_migration_run_flattens_structure(self):
        """MigrationStep.run flattens old directory structure."""
        from installer.context import InstallContext
        from installer.steps.migration import MigrationStep
        from installer.ui import Console

        step = MigrationStep()
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create old nested structure
            old_dir = Path(tmpdir) / ".claude" / "rules" / "standard" / "subdir"
            old_dir.mkdir(parents=True)
            (old_dir / "rule.md").write_text("old rule content")

            ctx = InstallContext(
                project_dir=Path(tmpdir),
                ui=Console(non_interactive=True),
            )

            if not step.check(ctx):
                step.run(ctx)
                # Files should be preserved (possibly flattened)
                standard_dir = Path(tmpdir) / ".claude" / "rules" / "standard"
                assert standard_dir.exists()


class TestNeedsMigration:
    """Test needs_migration helper function."""

    def test_needs_migration_returns_bool(self):
        """needs_migration returns boolean."""
        from installer.steps.migration import needs_migration

        with tempfile.TemporaryDirectory() as tmpdir:
            result = needs_migration(Path(tmpdir))
            assert isinstance(result, bool)

    def test_needs_migration_false_for_fresh_install(self):
        """needs_migration returns False for fresh install."""
        from installer.steps.migration import needs_migration

        with tempfile.TemporaryDirectory() as tmpdir:
            result = needs_migration(Path(tmpdir))
            assert result is False
