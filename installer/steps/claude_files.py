"""Claude files installation step - installs .claude directory files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from installer.downloads import DownloadConfig, download_file, get_repo_files
from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext


class ClaudeFilesStep(BaseStep):
    """Step that installs .claude directory files from the repository."""

    name = "claude_files"

    def check(self, ctx: InstallContext) -> bool:
        """Check if .claude files are already installed."""
        claude_dir = ctx.project_dir / ".claude"

        if not claude_dir.exists():
            return False

        # Check for key files that indicate installation
        key_files = [
            "settings.local.template.json",
            "rules/standard",
        ]

        for key_file in key_files:
            if not (claude_dir / key_file).exists():
                return False

        return True

    def run(self, ctx: InstallContext) -> None:
        """Install all .claude files from repository."""
        ui = ctx.ui

        # Build download config
        config = DownloadConfig(
            repo_url="https://github.com/maxritter/claude-codepro",
            repo_branch="main",
            local_mode=ctx.local_mode,
            local_repo_dir=ctx.local_repo_dir,
        )

        if ui:
            ui.status("Installing .claude files...")

        # Get list of files to install
        claude_files = get_repo_files(".claude", config)

        installed_files: list[str] = []
        file_count = 0

        for file_path in claude_files:
            if not file_path:
                continue

            # Skip settings.local.json (handled separately)
            if "settings.local.json" in file_path and "settings.local.template.json" not in file_path:
                continue

            # Skip Python files if not installing Python support
            if not ctx.install_python:
                if "file_checker_python.py" in file_path:
                    continue
                if "custom/python-rules.md" in file_path:
                    continue

            dest_file = ctx.project_dir / file_path
            if download_file(file_path, dest_file, config):
                file_count += 1
                installed_files.append(str(dest_file))
                if ui:
                    ui.print(f"   ✓ {Path(file_path).name}")

        # Store installed files for potential rollback
        ctx.config["installed_files"] = installed_files

        # Set executable permissions on hooks
        hooks_dir = ctx.project_dir / ".claude" / "hooks"
        if hooks_dir.exists():
            for hook_file in hooks_dir.glob("*.sh"):
                hook_file.chmod(0o755)
            for hook_file in hooks_dir.glob("*.py"):
                hook_file.chmod(0o755)

        # Create custom and skills directories if they don't exist
        custom_dir = ctx.project_dir / ".claude" / "rules" / "custom"
        if not custom_dir.exists():
            custom_dir.mkdir(parents=True, exist_ok=True)
            (custom_dir / ".gitkeep").touch()

        skills_dir = ctx.project_dir / ".claude" / "skills"
        if not skills_dir.exists():
            skills_dir.mkdir(parents=True, exist_ok=True)
            (skills_dir / ".gitkeep").touch()

        if ui:
            ui.success(f"Installed {file_count} .claude files")

    def rollback(self, ctx: InstallContext) -> None:
        """Remove installed files."""
        installed_files = ctx.config.get("installed_files", [])

        for file_path in installed_files:
            path = Path(file_path)
            if path.exists():
                try:
                    path.unlink()
                except (OSError, IOError):
                    pass
