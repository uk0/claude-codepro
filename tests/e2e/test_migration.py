"""E2E tests for migration functionality."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        yield project_dir


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def setup_migration_module(project_dir: Path, project_root: Path) -> None:
    """Set up migration module for testing."""
    # Copy migration module
    lib_dir = project_dir / "scripts" / "lib"
    lib_dir.mkdir(parents=True)

    # Copy required modules
    for module in ["migration.py", "ui.py", "utils.py", "files.py"]:
        src = project_root / "scripts" / "lib" / module
        dst = lib_dir / module
        dst.write_text(src.read_text())


class TestMigrationDetection:
    """Test migration detection logic."""

    def test_detects_old_config_format(self, temp_project, project_root):
        """Test that old config format is detected as needing migration."""
        setup_migration_module(temp_project, project_root)

        # Create old format config
        rules_dir = temp_project / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        old_config = """commands:
  plan:
    description: Old description
    model: opus
    rules:
      - old-rule-1
      - old-rule-2
"""
        (rules_dir / "config.yaml").write_text(old_config)

        # Import and test migration detection
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import migration

        result = migration.needs_migration(temp_project)
        assert result is True

    def test_new_format_not_needing_migration(self, temp_project, project_root):
        """Test that new format (standard:) is not detected as needing migration."""
        setup_migration_module(temp_project, project_root)

        # Create new format config
        rules_dir = temp_project / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        new_config = """commands:
  plan:
    description: New description
    model: opus
    rules:
      standard:
        - rule-1
        - rule-2
      custom: []
"""
        (rules_dir / "config.yaml").write_text(new_config)

        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import migration

        result = migration.needs_migration(temp_project)
        assert result is False

    def test_new_format_with_custom_not_needing_migration(self, temp_project, project_root):
        """Test that new format (custom:) is not detected as needing migration."""
        setup_migration_module(temp_project, project_root)

        # Create new format config with custom rules
        rules_dir = temp_project / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        new_config = """commands:
  plan:
    description: New description
    model: opus
    rules:
      standard: []
      custom:
        - my-rule
"""
        (rules_dir / "config.yaml").write_text(new_config)

        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import migration

        result = migration.needs_migration(temp_project)
        assert result is False

    def test_missing_config_not_needing_migration(self, temp_project, project_root):
        """Test that missing config is not detected as needing migration."""
        setup_migration_module(temp_project, project_root)

        # Create rules directory but no config
        rules_dir = temp_project / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import migration

        result = migration.needs_migration(temp_project)
        assert result is False


class TestMigrationExecution:
    """Test migration execution."""

    def test_creates_backup_directory(self, temp_project, project_root):
        """Test that migration creates backup directory."""
        setup_migration_module(temp_project, project_root)

        # Create old config and test files
        rules_dir = temp_project / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        old_config = """commands:
  plan:
    description: Old description
    rules:
      - rule-1
"""
        (rules_dir / "config.yaml").write_text(old_config)

        # Create test files in rules directory
        core_dir = rules_dir / "core"
        core_dir.mkdir()
        (core_dir / "test-rule.md").write_text("Test content")
        (rules_dir / "old-file.txt").write_text("Old file")

        # Run migration
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import migration

        migration.run_migration(temp_project, non_interactive=True)

        # Check backup was created
        backups = list((temp_project / ".claude").glob("rules.backup.*"))
        assert len(backups) == 1
        assert backups[0].is_dir()

    def test_backup_contains_original_files(self, temp_project, project_root):
        """Test that backup contains original files."""
        setup_migration_module(temp_project, project_root)

        # Create old config and test files
        rules_dir = temp_project / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        old_config = """commands:
  plan:
    description: Old description
    rules:
      - rule-1
"""
        (rules_dir / "config.yaml").write_text(old_config)

        core_dir = rules_dir / "core"
        core_dir.mkdir()
        (core_dir / "test-rule.md").write_text("Test rule content")

        # Run migration
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import migration

        migration.run_migration(temp_project, non_interactive=True)

        # Find backup directory
        backups = list((temp_project / ".claude").glob("rules.backup.*"))
        backup_dir = backups[0]

        # Verify files are in backup
        assert (backup_dir / "config.yaml").exists()
        assert (backup_dir / "core" / "test-rule.md").exists()
        assert (backup_dir / "core" / "test-rule.md").read_text() == "Test rule content"

    def test_deletes_old_rules_folder(self, temp_project, project_root):
        """Test that old rules folder is deleted after backup."""
        setup_migration_module(temp_project, project_root)

        # Create old config
        rules_dir = temp_project / ".claude" / "rules"
        rules_dir.mkdir(parents=True)

        old_config = """commands:
  plan:
    description: Old description
    rules:
      - rule-1
"""
        (rules_dir / "config.yaml").write_text(old_config)

        # Create old structure that should be deleted
        core_dir = rules_dir / "core"
        core_dir.mkdir()
        (core_dir / "test-rule.md").write_text("Test content")

        # Run migration
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import migration

        migration.run_migration(temp_project, non_interactive=True)

        # Old structure should be gone (migration deletes entire rules directory)
        assert not (rules_dir / "core").exists()
        assert not (rules_dir / "core" / "test-rule.md").exists()

        # Migration deletes the entire rules directory - it will be recreated by install
        # Just verify the rules directory was removed
        assert not rules_dir.exists()
