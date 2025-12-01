"""Cross-platform utilities for the installer."""

from __future__ import annotations

import platform
import shutil
from pathlib import Path

import platformdirs


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == "Linux"


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == "Windows"


def is_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux."""
    if not is_linux():
        return False
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except (OSError, IOError):
        return False


def command_exists(command: str) -> bool:
    """Check if a command exists in PATH."""
    return shutil.which(command) is not None


def get_package_manager() -> str | None:
    """Detect the system package manager."""
    if is_macos():
        if command_exists("brew"):
            return "brew"
    elif is_linux() or is_wsl():
        if command_exists("apt-get"):
            return "apt-get"
        elif command_exists("dnf"):
            return "dnf"
        elif command_exists("yum"):
            return "yum"
        elif command_exists("pacman"):
            return "pacman"
    return None


def get_config_dir() -> Path:
    """Get the user configuration directory using platformdirs."""
    return Path(platformdirs.user_config_dir("claude-codepro"))


def get_data_dir() -> Path:
    """Get the user data directory using platformdirs."""
    return Path(platformdirs.user_data_dir("claude-codepro"))


def get_shell_config_files() -> list[Path]:
    """Get list of shell configuration files for the current user."""
    home = Path.home()
    configs = []

    # Bash
    bashrc = home / ".bashrc"
    bash_profile = home / ".bash_profile"
    if bashrc.exists():
        configs.append(bashrc)
    if bash_profile.exists():
        configs.append(bash_profile)

    # Zsh
    zshrc = home / ".zshrc"
    if zshrc.exists():
        configs.append(zshrc)

    # Fish
    fish_config = home / ".config" / "fish" / "config.fish"
    if fish_config.exists():
        configs.append(fish_config)

    # If no configs found, return common defaults
    if not configs:
        configs = [bashrc, zshrc, fish_config]

    return configs


def get_platform_suffix() -> str:
    """Get platform suffix for binary names (e.g., 'linux-x86_64', 'darwin-arm64')."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize machine names
    if machine in ("amd64", "x86_64"):
        machine = "x86_64"
    elif machine in ("arm64", "aarch64"):
        machine = "arm64"

    return f"{system}-{machine}"


def add_to_path(path: Path) -> None:
    """Add directory to PATH in shell configs."""
    export_line = f'export PATH="{path}:$PATH"'
    fish_line = f'set -gx PATH "{path}" $PATH'

    for config_file in get_shell_config_files():
        if not config_file.exists():
            continue

        content = config_file.read_text()

        # Skip if already present
        if str(path) in content:
            continue

        # Use fish syntax for fish config
        if "fish" in config_file.name:
            line_to_add = fish_line
        else:
            line_to_add = export_line

        # Append to config
        with open(config_file, "a") as f:
            f.write(f"\n{line_to_add}\n")
