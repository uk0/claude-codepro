"""
Utility Functions - Cleanup, dependency checking, and helper utilities

Provides cleanup, platform detection, and dependency verification functions.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

from . import ui


def cleanup(temp_dir: Path | None = None) -> None:
    """
    Cleanup on exit.

    Removes temporary directory and restores cursor visibility.

    Args:
        temp_dir: Path to temporary directory to remove
    """
    if temp_dir and temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

    try:
        if sys.platform != "win32":
            _ = subprocess.run(["tput", "cnorm"], capture_output=True, check=False)
    except Exception:
        pass


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == "Darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == "Linux"


def is_wsl() -> bool:
    """Check if running in Windows Subsystem for Linux."""
    if not is_linux():
        return False
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except Exception:
        return False


def command_exists(command: str) -> bool:
    """
    Check if a command exists in PATH.

    Args:
        command: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    return shutil.which(command) is not None


def get_package_manager() -> str | None:
    """
    Detect the system package manager.

    Returns:
        Package manager name ('brew', 'apt-get', 'yum', 'dnf') or None
    """
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
    return None


def install_package(package: str, display_name: str | None = None) -> bool:
    """
    Install a package using the system package manager.

    Args:
        package: Package name to install
        display_name: Display name for user feedback (defaults to package)

    Returns:
        True if installation succeeded, False otherwise
    """
    if display_name is None:
        display_name = package

    pkg_manager = get_package_manager()

    if not pkg_manager:
        ui.print_error(f"No supported package manager found. Please install {display_name} manually")
        return False

    ui.print_status(f"Installing {display_name}...")

    try:
        if pkg_manager == "brew":
            result = subprocess.run(
                ["brew", "install", package],
                capture_output=True,
                text=True,
                check=False,
            )
        elif pkg_manager == "apt-get":
            _ = subprocess.run(["sudo", "apt-get", "update"], capture_output=True, check=False)
            result = subprocess.run(
                ["sudo", "apt-get", "install", "-y", package],
                capture_output=True,
                text=True,
                check=False,
            )
        elif pkg_manager == "yum":
            result = subprocess.run(
                ["sudo", "yum", "install", "-y", package],
                capture_output=True,
                text=True,
                check=False,
            )
        elif pkg_manager == "dnf":
            result = subprocess.run(
                ["sudo", "dnf", "install", "-y", package],
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            return False

        if result.returncode == 0:
            ui.print_success(f"Installed {display_name}")
            return True
        else:
            ui.print_warning(f"Failed to install {display_name}")
            return False

    except Exception as e:
        ui.print_error(f"Error installing {display_name}: {e}")
        return False


def check_required_dependencies() -> bool:
    """
    Check required system dependencies.

    Verifies that critical commands are available.

    Returns:
        True if all required dependencies available, False otherwise
    """
    missing: list[str] = []

    if not command_exists("curl"):
        missing.append("curl")

    for cmd in ["mkdir", "cp", "mv", "rm", "chmod", "find", "grep"]:
        if not command_exists(cmd):
            missing.append(cmd)

    if missing:
        ui.print_error(f"Missing required dependencies: {', '.join(missing)}")
        print("")
        print("Please install the missing dependencies and try again:")
        print("")

        if is_macos():
            print("  macOS: These tools should be pre-installed. Try reinstalling Command Line Tools:")
            print("  xcode-select --install")
        elif command_exists("apt-get"):
            print("  Ubuntu/Debian:")
            print("  sudo apt-get update && sudo apt-get install -y curl coreutils findutils")
        elif command_exists("yum"):
            print("  RHEL/CentOS:")
            print("  sudo yum install -y curl coreutils findutils")
        elif command_exists("dnf"):
            print("  Fedora:")
            print("  sudo dnf install -y curl coreutils findutils")

        return False

    return True


def run_command(
    cmd: list[str],
    check: bool = True,
    capture_output: bool = True,
    shell: bool = False,
    cwd: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run a shell command with consistent error handling.

    Args:
        cmd: Command and arguments as list
        check: Raise exception on non-zero exit code
        capture_output: Capture stdout/stderr
        shell: Run command through shell
        cwd: Working directory for command

    Returns:
        CompletedProcess instance with text output
    """
    return subprocess.run(cmd, check=check, capture_output=capture_output, text=True, shell=shell, cwd=cwd)


def get_python_version() -> str:
    """Get the current Python version as a string."""
    return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"


def is_python_version_compatible(min_version: str = "3.8") -> bool:
    """
    Check if current Python version meets minimum requirements.

    Args:
        min_version: Minimum required version (e.g., "3.8")

    Returns:
        True if version is compatible, False otherwise
    """
    min_parts = [int(x) for x in min_version.split(".")]
    current_parts = [sys.version_info.major, sys.version_info.minor]

    if len(min_parts) > 2:
        current_parts.append(sys.version_info.micro)

    return current_parts >= min_parts[: len(current_parts)]
