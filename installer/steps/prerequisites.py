"""Prerequisites installation step for local installations."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from installer.platform_utils import command_exists, is_homebrew_available, is_in_devcontainer
from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext

HOMEBREW_PACKAGES = [
    "git",
    "gh",
    "python@3.12",
    "node@22",
    "nvm",
    "pnpm",
    "bun",
    "uv",
]


def _add_bun_tap() -> bool:
    """Add the bun tap to Homebrew."""
    try:
        result = subprocess.run(
            ["brew", "tap", "oven-sh/bun"],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0 or b"already tapped" in result.stderr.lower()
    except (subprocess.SubprocessError, OSError):
        return False


def _install_homebrew_package(package: str) -> bool:
    """Install a single Homebrew package."""
    try:
        result = subprocess.run(
            ["brew", "install", package],
            capture_output=True,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def _get_command_for_package(package: str) -> str:
    """Get the command name to check for a given Homebrew package."""
    package_to_command = {
        "python@3.12": "python3",
        "node@22": "node",
        "gh": "gh",
        "git": "git",
        "nvm": "nvm",
        "pnpm": "pnpm",
        "bun": "bun",
        "uv": "uv",
    }
    return package_to_command.get(package, package)


class PrerequisitesStep(BaseStep):
    """Step that installs prerequisite packages for local installations."""

    name = "prerequisites"

    def check(self, ctx: InstallContext) -> bool:
        """Check if this step should be skipped.

        Returns True (skip) if:
        - Running in a dev container
        - Not a local installation
        - All packages are already installed
        """
        if is_in_devcontainer():
            return True

        if not ctx.is_local_install:
            return True

        if not is_homebrew_available():
            return False

        for package in HOMEBREW_PACKAGES:
            cmd = _get_command_for_package(package)
            if not command_exists(cmd):
                return False

        return True

    def run(self, ctx: InstallContext) -> None:
        """Install missing prerequisite packages via Homebrew."""
        ui = ctx.ui

        _add_bun_tap()

        for package in HOMEBREW_PACKAGES:
            cmd = _get_command_for_package(package)

            if command_exists(cmd):
                if ui:
                    ui.info(f"{package} already installed")
                continue

            if ui:
                with ui.spinner(f"Installing {package}..."):
                    success = _install_homebrew_package(package)
                if success:
                    ui.success(f"{package} installed")
                else:
                    ui.warning(f"Could not install {package} - please install manually")
            else:
                _install_homebrew_package(package)

    def rollback(self, ctx: InstallContext) -> None:
        """Prerequisite packages are not rolled back (would be too disruptive)."""
        pass
