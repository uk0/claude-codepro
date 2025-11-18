"""
Dev Container Functions - Detection and installation of dev container setup

Provides dev container detection and installation capabilities.
"""

from __future__ import annotations

import sys
from pathlib import Path

from . import downloads, ui


def has_devcontainer(project_dir: Path) -> bool:
    """
    Check if dev container directory exists.

    Args:
        project_dir: Project directory path

    Returns:
        True if .devcontainer exists, False otherwise
    """
    return (project_dir / ".devcontainer").is_dir()


def is_in_devcontainer() -> bool:
    """
    Check if running inside a dev container.

    Returns:
        True if inside container, False otherwise
    """
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def install_devcontainer(
    project_dir: Path,
    config: downloads.DownloadConfig,
) -> None:
    """
    Install dev container configuration.

    Downloads .devcontainer directory from repo or copies from local.

    Args:
        project_dir: Project directory path
        config: Download configuration
    """
    ui.print_status("Installing dev container configuration...")

    devcontainer_files = [
        ".devcontainer/Dockerfile",
        ".devcontainer/devcontainer.json",
        ".devcontainer/postCreateCommand.sh",
    ]

    for file_path in devcontainer_files:
        dest_file = project_dir / file_path
        if downloads.download_file(file_path, dest_file, config):
            print(f"   ✓ {Path(file_path).name}")
        else:
            ui.print_warning(f"Failed to download {file_path}")

    post_create = project_dir / ".devcontainer" / "postCreateCommand.sh"
    if post_create.exists():
        post_create.chmod(0o755)

    ui.print_success("Dev container configuration installed")


def offer_devcontainer_setup(
    project_dir: Path,
    config: downloads.DownloadConfig,
    non_interactive: bool = False,
) -> None:
    """
    Offer dev container setup to user.

    If not in container and no .devcontainer exists, offer to install.

    Args:
        project_dir: Project directory path
        config: Download configuration
        non_interactive: Skip interactive prompts
    """

    if is_in_devcontainer():
        return

    if has_devcontainer(project_dir):
        return

    if non_interactive:
        return

    ui.print_section("Dev Container Setup (Recommended)")
    print("Claude CodePro can run in a VS Code Dev Container for:")
    print("  ✓ Complete isolation from your host system")
    print("  ✓ Pre-configured tools and extensions")
    print("  ✓ No interference with system packages or settings")
    print("  ✓ Consistent environment across machines")
    print("")
    print("Installing locally may interfere with:")
    print("  ✗ Existing Node.js, Python, or tool versions")
    print("  ✗ Shell configuration files (.bashrc, .zshrc)")
    print("  ✗ Global package installations")
    print("")

    if sys.stdin.isatty():
        reply = input("Install dev container configuration? (Y/n): ").strip()
    else:
        reply = input("Install dev container configuration? (Y/n): ").strip()

    print("")

    if not reply:
        reply = "Y"

    if reply.lower() not in ["y", "yes"]:
        ui.print_warning("Proceeding with local installation (may interfere with system packages)")
        print("")
        return

    install_devcontainer(project_dir, config)
    print("")

    ui.print_section("Dev Container Next Steps")
    print("The .devcontainer configuration has been installed.")
    print("")
    print("To use it:")
    print("  1. Install the 'Dev Containers' extension in VS Code/Cursor/Windsurf")
    print("     Extension ID: ms-vscode-remote.remote-containers")
    print("")
    print("  2. Open Command Palette (Cmd+Shift+P / Ctrl+Shift+P)")
    print("")
    print("  3. Run: 'Dev Containers: Reopen in Container'")
    print("")
    print("  4. Wait for container to build (first time takes ~5-10 minutes)")
    print("")
    print("  5. Installation will continue automatically inside the container")
    print("")
    print(f"{ui.YELLOW}Press Enter to exit and set up dev container, or Ctrl+C to continue local installation{ui.NC}")

    if sys.stdin.isatty():
        _ = input()
    else:
        _ = input()

    ui.print_success("Please reopen in dev container to continue installation")
    sys.exit(0)
