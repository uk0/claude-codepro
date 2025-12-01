"""Dependencies step - installs required tools and packages."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from installer.platform_utils import command_exists
from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext


def install_nodejs() -> bool:
    """Install Node.js via NVM if not present."""
    if command_exists("node"):
        return True

    try:
        # Install NVM if not present
        nvm_dir = Path.home() / ".nvm"
        if not nvm_dir.exists():
            subprocess.run(
                ["bash", "-c", "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash"],
                check=True,
                capture_output=True,
            )

        # Install Node.js via NVM
        subprocess.run(
            ["bash", "-c", "source ~/.nvm/nvm.sh && nvm install 22 && nvm use 22"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_uv() -> bool:
    """Install uv package manager if not present."""
    if command_exists("uv"):
        return True

    try:
        subprocess.run(
            ["bash", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_python_tools() -> bool:
    """Install Python development tools."""
    tools = ["ruff", "mypy", "basedpyright"]

    try:
        for tool in tools:
            if not command_exists(tool):
                subprocess.run(
                    ["uv", "tool", "install", tool],
                    check=True,
                    capture_output=True,
                )
        return True
    except subprocess.CalledProcessError:
        return False


def install_claude_code() -> bool:
    """Install Claude Code CLI via official installer."""
    try:
        subprocess.run(
            ["bash", "-c", "curl -fsSL https://claude.ai/install.sh | bash"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_qlty(project_dir: Path) -> bool:
    """Install qlty code quality tool."""
    try:
        subprocess.run(
            ["bash", "-c", "curl https://qlty.sh | bash"],
            check=True,
            capture_output=True,
            cwd=project_dir,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_cipher() -> bool:
    """Install Cipher memory tool."""
    try:
        subprocess.run(
            ["npm", "install", "-g", "@byterover/cipher"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_newman() -> bool:
    """Install Newman (Postman CLI)."""
    if command_exists("newman"):
        return True

    try:
        subprocess.run(
            ["npm", "install", "-g", "newman"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def install_dotenvx() -> bool:
    """Install dotenvx (environment variable management)."""
    if command_exists("dotenvx"):
        return True

    try:
        subprocess.run(
            ["npm", "install", "-g", "@dotenvx/dotenvx"],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def _install_with_spinner(ui: Any, name: str, install_fn: Any, *args: Any) -> bool:
    """Run an installation function with a spinner."""
    if ui:
        with ui.spinner(f"Installing {name}..."):
            result = install_fn(*args) if args else install_fn()
        if result:
            ui.success(f"{name} installed")
        else:
            ui.warning(f"Could not install {name} - please install manually")
        return result
    else:
        return install_fn(*args) if args else install_fn()


class DependenciesStep(BaseStep):
    """Step that installs all required dependencies."""

    name = "dependencies"

    def check(self, ctx: InstallContext) -> bool:
        """Always returns False - dependencies should always be checked."""
        return False

    def run(self, ctx: InstallContext) -> None:
        """Install all required dependencies."""
        ui = ctx.ui
        installed: list[str] = []

        # Install Node.js
        if _install_with_spinner(ui, "Node.js", install_nodejs):
            installed.append("nodejs")

        # Install Python tools if enabled
        if ctx.install_python:
            if _install_with_spinner(ui, "uv", install_uv):
                installed.append("uv")

            if _install_with_spinner(ui, "Python tools", install_python_tools):
                installed.append("python_tools")

        # Install Claude Code
        if _install_with_spinner(ui, "Claude Code", install_claude_code):
            installed.append("claude_code")

        # Install qlty
        if _install_with_spinner(ui, "qlty", install_qlty, ctx.project_dir):
            installed.append("qlty")

        # Install Cipher
        if _install_with_spinner(ui, "Cipher", install_cipher):
            installed.append("cipher")

        # Install Newman
        if _install_with_spinner(ui, "Newman", install_newman):
            installed.append("newman")

        # Install dotenvx
        if _install_with_spinner(ui, "dotenvx", install_dotenvx):
            installed.append("dotenvx")

        ctx.config["installed_dependencies"] = installed

    def rollback(self, ctx: InstallContext) -> None:
        """Dependencies are not rolled back (would be too disruptive)."""
        pass
