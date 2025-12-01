"""Devcontainer setup step - offers devcontainer installation."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from installer.downloads import DownloadConfig, download_file
from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext


def is_in_devcontainer() -> bool:
    """Check if running inside a dev container."""
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def has_devcontainer(project_dir: Path) -> bool:
    """Check if .devcontainer directory exists."""
    return (project_dir / ".devcontainer").is_dir()


class DevcontainerStep(BaseStep):
    """Step that offers devcontainer setup to users not in a container."""

    name = "devcontainer"

    def check(self, ctx: InstallContext) -> bool:
        """Check if devcontainer setup is needed."""
        # Skip if already in a container
        if is_in_devcontainer():
            return True

        # Skip if .devcontainer already exists
        if has_devcontainer(ctx.project_dir):
            return True

        return False

    def run(self, ctx: InstallContext) -> None:
        """Offer devcontainer setup if applicable."""
        ui = ctx.ui

        # Skip in non-interactive mode
        if ctx.non_interactive:
            if ui:
                ui.status("Skipping devcontainer setup (non-interactive mode)")
            return

        # Skip if already in container
        if is_in_devcontainer():
            if ui:
                ui.status("Already running in container, skipping devcontainer setup")
            return

        # Skip if .devcontainer exists
        if has_devcontainer(ctx.project_dir):
            if ui:
                ui.status(".devcontainer already exists, skipping setup")
            return

        # Offer devcontainer setup
        if ui:
            ui.section("Dev Container Setup (Recommended)")
            ui.print()
            ui.status("Claude CodePro can run in a VS Code Dev Container for:")
            ui.print("  ✓ Complete isolation from your host system")
            ui.print("  ✓ Pre-configured tools and extensions")
            ui.print("  ✓ No interference with system packages or settings")
            ui.print("  ✓ Consistent environment across machines")
            ui.print()

            if not ui.confirm("Install dev container configuration?", default=True):
                ui.warning("Proceeding with local installation")
                return

            # Get container name
            default_name = ctx.project_dir.name
            container_name = ui.input(f"Container name (default: {default_name})", default=default_name)
            if not container_name:
                container_name = default_name

            # Install devcontainer files
            self._install_devcontainer(ctx, container_name)

    def _install_devcontainer(self, ctx: InstallContext, container_name: str) -> None:
        """Install devcontainer files."""
        ui = ctx.ui
        project_dir = ctx.project_dir

        if ui:
            ui.status("Installing dev container configuration...")

        config = DownloadConfig(
            repo_url="https://github.com/maxritter/claude-codepro",
            repo_branch="main",
            local_mode=ctx.local_mode,
            local_repo_dir=ctx.local_repo_dir,
        )

        devcontainer_files = [
            ".devcontainer/Dockerfile",
            ".devcontainer/devcontainer.json",
            ".devcontainer/postCreateCommand.sh",
        ]

        for file_path in devcontainer_files:
            dest_file = project_dir / file_path
            if download_file(file_path, dest_file, config):
                if ui:
                    ui.success(f"Installed {Path(file_path).name}")

        # Create slug from container name (lowercase, replace spaces with hyphens)
        container_slug = container_name.lower().replace(" ", "-").replace("_", "-")

        # Update devcontainer.json with custom name
        devcontainer_json = project_dir / ".devcontainer" / "devcontainer.json"
        if devcontainer_json.exists():
            content = devcontainer_json.read_text()
            content = content.replace("{{PROJECT_NAME}}", container_name)
            content = content.replace("{{PROJECT_SLUG}}", container_slug)
            devcontainer_json.write_text(content)

        # Make postCreateCommand.sh executable
        post_create = project_dir / ".devcontainer" / "postCreateCommand.sh"
        if post_create.exists():
            post_create.chmod(0o755)

        if ui:
            ui.success("Dev container configuration installed")
            ui.print()
            ui.status("To use it:")
            ui.print("  1. Install the 'Dev Containers' extension in VS Code")
            ui.print("  2. Open Command Palette (Cmd+Shift+P / Ctrl+Shift+P)")
            ui.print("  3. Run: 'Dev Containers: Reopen in Container'")

    def rollback(self, ctx: InstallContext) -> None:
        """Remove devcontainer directory."""
        import shutil

        devcontainer_dir = ctx.project_dir / ".devcontainer"
        if devcontainer_dir.exists():
            shutil.rmtree(devcontainer_dir)
