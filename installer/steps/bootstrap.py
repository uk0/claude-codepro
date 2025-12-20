"""Bootstrap step - initial setup and directory creation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext


class BootstrapStep(BaseStep):
    """Bootstrap step that prepares for installation."""

    name = "bootstrap"

    def check(self, ctx: InstallContext) -> bool:
        """Always returns False - bootstrap always runs."""
        return False

    def run(self, ctx: InstallContext) -> None:
        """Set up installation environment."""
        ui = ctx.ui
        claude_dir = ctx.project_dir / ".claude"

        is_upgrade = claude_dir.exists()
        ctx.config["is_upgrade"] = is_upgrade

        if is_upgrade:
            if ui:
                ui.status("Updating existing installation...")
        else:
            if ui:
                ui.status("Fresh installation detected")

        claude_dir.mkdir(parents=True, exist_ok=True)

        subdirs = [
            "rules/standard",
            "rules/custom",
            "hooks",
            "commands",
            "skills",
        ]

        for subdir in subdirs:
            (claude_dir / subdir).mkdir(parents=True, exist_ok=True)

        if ui:
            ui.success("Directory structure ready")

    def rollback(self, ctx: InstallContext) -> None:
        """No rollback needed - files are merged, not replaced."""
        pass
