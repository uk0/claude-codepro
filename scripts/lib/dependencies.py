"""
Dependency Installation Functions - Node.js, Python, and other tools

Handles installation of all required external tools and dependencies.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from . import ui, utils


def load_nvm() -> tuple[bool, str | None]:
    """
    Detect and load NVM from various locations.

    Returns:
        Tuple of (success, nvm_dir_path)
    """

    home = Path.home()
    nvm_locations = [
        home / ".nvm",
        Path("/usr/local/share/nvm"),
        Path(os.environ.get("NVM_DIR", "")),
    ]

    for nvm_dir in nvm_locations:
        if not nvm_dir:
            continue

        nvm_sh = nvm_dir / "nvm.sh"
        if nvm_sh.exists():
            os.environ["NVM_DIR"] = str(nvm_dir)
            return True, str(nvm_dir)

    return False, None


def install_nodejs() -> None:
    """
    Install Node.js via NVM.

    Installs NVM if not present, then installs Node.js 22.x.
    Exits on failure.
    """

    nvm_loaded, nvm_dir = load_nvm()

    if nvm_loaded:
        ui.print_success(f"NVM already installed at {nvm_dir}")
    else:
        ui.print_status("Installing NVM (Node Version Manager)...")

        try:
            install_cmd = "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash"
            result = subprocess.run(install_cmd, shell=True, check=True, capture_output=True, text=True)

            nvm_loaded, nvm_dir = load_nvm()
            if not nvm_loaded:
                ui.print_error("NVM installation failed or unable to load NVM")
                ui.print_error("Please install NVM manually: https://github.com/nvm-sh/nvm")
                sys.exit(1)

            ui.print_success(f"Installed NVM at {nvm_dir}")

        except subprocess.CalledProcessError:
            ui.print_error("NVM installation failed")
            ui.print_error("Please install NVM manually: https://github.com/nvm-sh/nvm")
            sys.exit(1)

    ui.print_status("Installing Node.js 22.x (required for Claude Context)...")

    nvm_commands = f"""
                    export NVM_DIR="{os.environ.get("NVM_DIR")}"
                    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
                    nvm install 22 2>/dev/null || nvm install 22
                    nvm use 22 2>/dev/null || nvm use 22
                    nvm alias default 22 2>/dev/null || nvm alias default 22
                    node --version
                    npm --version
                    """

    try:
        result = subprocess.run(
            nvm_commands,
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )

        if utils.command_exists("npm"):
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                node_version = lines[-2].strip()
                npm_version = lines[-1].strip()
                ui.print_success(f"Installed Node.js {node_version} and npm {npm_version}")

                if not node_version.startswith("v22."):
                    ui.print_warning(f"Warning: Expected Node.js 22.x but got {node_version}")
        else:
            ui.print_error("npm installation failed. Please install Node.js manually using NVM")
            sys.exit(1)

    except Exception as e:
        ui.print_error(f"Node.js installation failed: {e}")
        sys.exit(1)


def install_uv() -> None:
    """Install uv (Python package manager)."""
    if utils.command_exists("uv"):
        ui.print_success("uv already installed")
        return

    ui.print_status("Installing uv...")

    try:
        install_cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
        subprocess.run(install_cmd, shell=True, check=True, capture_output=True)

        cargo_bin = Path.home() / ".cargo" / "bin"
        os.environ["PATH"] = f"{cargo_bin}:{os.environ.get('PATH', '')}"

        ui.print_success("Installed uv")

    except subprocess.CalledProcessError as e:
        ui.print_error(f"uv installation failed: {e}")
        sys.exit(1)


def install_python_tools() -> None:
    """
    Install Python development tools.

    Installs: ruff, mypy, basedpyright
    Requires: uv must be installed first
    """
    ui.print_status("Installing Python tools globally...")

    tools = ["ruff", "mypy", "basedpyright"]

    for tool in tools:
        try:
            subprocess.run(
                ["uv", "tool", "install", tool],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError:
            ui.print_warning(f"Failed to install {tool}")

    ui.print_success("Installed Python tools (ruff, mypy, basedpyright)")


def install_qlty(project_dir: Path) -> None:
    """
    Install qlty (code quality tool).

    Args:
        project_dir: Project directory for qlty initialization
    """
    if utils.command_exists("qlty"):
        ui.print_success("qlty already installed")
        return

    ui.print_status("Installing qlty...")

    try:
        install_cmd = "curl -s https://qlty.sh | sh"
        subprocess.run(install_cmd, shell=True, check=True, capture_output=True)

        qlty_install = Path.home() / ".qlty"
        qlty_bin = qlty_install / "bin"
        os.environ["QLTY_INSTALL"] = str(qlty_install)
        os.environ["PATH"] = f"{qlty_bin}:{os.environ.get('PATH', '')}"

        # Configuration to add to shell profiles
        marker = "# qlty configuration"
        config_lines = [
            "",
            marker,
            f'export QLTY_INSTALL="{qlty_install}"',
            'export PATH="$QLTY_INSTALL/bin:$PATH"',
            "",
        ]
        config_text = "\n".join(config_lines)

        # Add to shell profiles (both zsh and bash for compatibility)
        for shell_rc in [".zshrc", ".bashrc"]:
            rc_file = Path.home() / shell_rc

            # Create file if it doesn't exist
            if not rc_file.exists():
                rc_file.touch()
                ui.print_status(f"Created {shell_rc}")

            rc_content = rc_file.read_text()

            # Add configuration if marker not present
            if marker not in rc_content:
                with open(rc_file, "a") as f:
                    f.write(config_text)
                ui.print_success(f"Added qlty to {shell_rc}")
            else:
                ui.print_status(f"qlty already configured in {shell_rc}")

        qlty_cmd = qlty_bin / "qlty"
        if qlty_cmd.exists():
            subprocess.run(
                [str(qlty_cmd), "check", "--install-only"],
                cwd=project_dir,
                check=True,
                capture_output=True,
            )

        ui.print_success("Installed qlty")
        ui.print_warning("Note: Restart your shell or run 'source ~/.zshrc' to use qlty in new terminals")

    except subprocess.CalledProcessError as e:
        ui.print_warning(f"qlty installation failed: {e}")


def install_claude_code() -> None:
    """Install Claude Code CLI."""
    if utils.command_exists("claude"):
        ui.print_success("Claude Code already installed")
        return

    ui.print_status("Installing Claude Code...")

    try:
        install_cmd = "curl -fsSL https://claude.ai/install.sh | bash"
        subprocess.run(install_cmd, shell=True, check=True, capture_output=True)

        ui.print_success("Installed Claude Code")

    except subprocess.CalledProcessError as e:
        ui.print_error(f"Claude Code installation failed: {e}")
        sys.exit(1)


def install_cipher() -> None:
    """
    Install Cipher (memory management for Claude).

    Requires: npm must be installed
    """
    if utils.command_exists("cipher"):
        ui.print_success("Cipher already installed")
        return

    ui.print_status("Installing Cipher...")

    try:
        subprocess.run(
            ["npm", "install", "-g", "@byterover/cipher"],
            check=True,
            capture_output=True,
            text=True,
        )

        if utils.command_exists("cipher"):
            ui.print_success("Installed Cipher")
        else:
            ui.print_warning("Cipher was installed but command not found in PATH")
            ui.print_warning("You may need to restart your shell or add npm global bin to PATH")
            print("   Run: npm config get prefix")
            print("   Then add <prefix>/bin to your PATH")

    except subprocess.CalledProcessError:
        ui.print_error("Failed to install Cipher")
        ui.print_warning("You can install it manually later with: npm install -g @byterover/cipher")


def install_newman() -> None:
    """
    Install Newman (Postman CLI).

    Requires: npm must be installed
    """
    if utils.command_exists("newman"):
        ui.print_success("Newman already installed")
        return

    ui.print_status("Installing Newman...")

    try:
        subprocess.run(
            ["npm", "install", "-g", "newman"],
            check=True,
            capture_output=True,
            text=True,
        )

        ui.print_success("Installed Newman")

    except subprocess.CalledProcessError as e:
        ui.print_warning(f"Newman installation failed: {e}")


def install_dotenvx() -> None:
    """
    Install dotenvx (environment variable management).

    Requires: npm must be installed
    """
    if utils.command_exists("dotenvx"):
        ui.print_success("dotenvx already installed")
        return

    ui.print_status("Installing dotenvx...")

    try:
        subprocess.run(
            ["npm", "install", "-g", "@dotenvx/dotenvx"],
            check=True,
            capture_output=True,
            text=True,
        )

        ui.print_success("Installed dotenvx")

    except subprocess.CalledProcessError as e:
        ui.print_warning(f"dotenvx installation failed: {e}")
