"""
Migration Functions - Handle upgrades from older versions

Provides migration logic for upgrading from older Claude CodePro versions.
"""

from __future__ import annotations

import shutil
import sys
import time
from pathlib import Path

from . import ui


def needs_migration(project_dir: Path) -> bool:
    """
    Check if migration is needed.

    Args:
        project_dir: Project directory path

    Returns:
        True if migration needed, False otherwise
    """
    config_file = project_dir / ".claude" / "rules" / "config.yaml"

    if not config_file.exists():
        return False

    content = config_file.read_text()
    if "standard:" in content or "custom:" in content:
        return False

    return True


def run_migration(project_dir: Path, non_interactive: bool = False) -> None:
    """
    Run migration - backup old rules and wipe for fresh install.

    Args:
        project_dir: Project directory path
        non_interactive: Skip interactive prompts
    """
    if not needs_migration(project_dir):
        return

    rules_dir = project_dir / ".claude" / "rules"

    ui.print_section("Migration Required")

    print("We detected an older version of the rules configuration.")
    print("To ensure compatibility, we need to reinstall the rules folder.")
    print("")
    ui.print_warning("Your existing rules will be backed up before deletion.")
    print("")
    print("What will happen:")
    print("  1. Create backup at .claude/rules.backup.<timestamp>")
    print("  2. Delete current .claude/rules folder")
    print("  3. Fresh rules will be downloaded")
    print("")

    if not non_interactive:
        if sys.stdin.isatty():
            reply = input("Continue with migration? (Y/n): ").strip()
        else:
            reply = input("Continue with migration? (Y/n): ").strip()
    else:
        reply = "Y"

    print("")

    if not reply:
        reply = "Y"

    if reply.lower() not in ["y", "yes"]:
        ui.print_error("Migration cancelled.")
        print("")
        print("To migrate manually:")
        print("  1. Backup your .claude/rules folder")
        print("  2. Delete .claude/rules")
        print("  3. Re-run installation")
        sys.exit(1)

    timestamp = int(time.time())
    backup_dir = project_dir / ".claude" / f"rules.backup.{timestamp}"
    ui.print_status(f"Creating backup at {backup_dir.name}...")
    shutil.copytree(rules_dir, backup_dir)
    ui.print_success(f"Backup created at: {backup_dir}")

    ui.print_status("Removing old rules folder...")
    shutil.rmtree(rules_dir)
    ui.print_success("Old rules removed")

    print("")
    ui.print_success("Migration complete! Fresh rules will be installed.")
    print("")
