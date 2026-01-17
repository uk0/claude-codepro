"""Cross-platform utilities for the installer."""

from __future__ import annotations

import shutil
from pathlib import Path


def is_in_devcontainer() -> bool:
    """Check if running inside a dev container."""
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def is_homebrew_available() -> bool:
    """Check if Homebrew is available."""
    return shutil.which("brew") is not None


def get_shell_config_files() -> list[Path]:
    """Get list of shell configuration files for the current user."""
    home = Path.home()
    configs = []

    bashrc = home / ".bashrc"
    bash_profile = home / ".bash_profile"
    if bashrc.exists():
        configs.append(bashrc)
    if bash_profile.exists():
        configs.append(bash_profile)

    zshrc = home / ".zshrc"
    if zshrc.exists():
        configs.append(zshrc)

    fish_config = home / ".config" / "fish" / "config.fish"
    if fish_config.exists():
        configs.append(fish_config)

    if not configs:
        configs = [bashrc, zshrc, fish_config]

    return configs
