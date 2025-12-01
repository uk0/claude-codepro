"""Migration step - handles upgrades from older versions."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext


def needs_migration(project_dir: Path) -> bool:
    """Check if migration from old structure is needed."""
    claude_dir = project_dir / ".claude"

    if not claude_dir.exists():
        return False

    # Check for old nested directory structure
    standard_dir = claude_dir / "rules" / "standard"
    if not standard_dir.exists():
        return False

    # Check if there are nested subdirectories (old structure)
    for item in standard_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            # Check if subdirectory contains .md files
            if list(item.glob("*.md")):
                return True

    return False


def flatten_directory(source_dir: Path, dest_dir: Path) -> int:
    """Flatten nested directory structure, preserving files."""
    count = 0
    dest_dir.mkdir(parents=True, exist_ok=True)

    for item in source_dir.rglob("*"):
        if item.is_file():
            # For nested files, prefix with parent dir name
            relative = item.relative_to(source_dir)
            if len(relative.parts) > 1:
                # Nested file - flatten name
                new_name = "-".join(relative.parts)
            else:
                new_name = item.name

            dest_file = dest_dir / new_name
            if not dest_file.exists():
                shutil.copy2(item, dest_file)
                count += 1

    return count


class MigrationStep(BaseStep):
    """Migration step that handles upgrades from older versions."""

    name = "migration"

    def check(self, ctx: InstallContext) -> bool:
        """Returns True if no migration needed."""
        return not needs_migration(ctx.project_dir)

    def run(self, ctx: InstallContext) -> None:
        """Execute migration from old structure."""
        ui = ctx.ui
        claude_dir = ctx.project_dir / ".claude"
        standard_dir = claude_dir / "rules" / "standard"

        if not standard_dir.exists():
            return

        if ui:
            ui.section("Migration Required")
            ui.status("Migrating from old directory structure...")

        # Create backup of standard rules
        backup_dir = claude_dir / "rules" / ".standard_backup"
        if standard_dir.exists() and not backup_dir.exists():
            shutil.copytree(standard_dir, backup_dir)
            ctx.config["migration_backup"] = str(backup_dir)

        # Flatten nested directories
        migrated_count = 0
        temp_dir = claude_dir / "rules" / ".migration_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        for item in standard_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Flatten this subdirectory
                for md_file in item.rglob("*.md"):
                    relative = md_file.relative_to(item)
                    if len(relative.parts) > 1:
                        new_name = f"{item.name}-{'-'.join(relative.parts)}"
                    else:
                        new_name = f"{item.name}-{md_file.name}"
                    dest_file = temp_dir / new_name
                    shutil.copy2(md_file, dest_file)
                    migrated_count += 1
            elif item.is_file():
                # Keep root-level files
                shutil.copy2(item, temp_dir / item.name)
                migrated_count += 1

        # Replace standard dir with flattened version
        if migrated_count > 0:
            shutil.rmtree(standard_dir)
            shutil.move(str(temp_dir), str(standard_dir))

            if ui:
                ui.success(f"Migrated {migrated_count} files")
        else:
            # Clean up temp if nothing migrated
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

        if ui:
            ui.success("Migration complete")

    def rollback(self, ctx: InstallContext) -> None:
        """Restore from migration backup."""
        backup_path = ctx.config.get("migration_backup")
        if backup_path:
            backup = Path(backup_path)
            standard_dir = ctx.project_dir / ".claude" / "rules" / "standard"

            if backup.exists():
                if standard_dir.exists():
                    shutil.rmtree(standard_dir)
                shutil.move(str(backup), str(standard_dir))
