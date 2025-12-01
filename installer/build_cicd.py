#!/usr/bin/env python3
"""Build script for ccp-installer binary.

Builds standalone executables for distribution using PyInstaller.
Run from the repository root.

Usage:
    python -m installer.build_cicd         # Build for current platform
    python -m installer.build_cicd --clean # Clean build directory first
"""

from __future__ import annotations

import argparse
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

INSTALLER_DIR = Path(__file__).parent
BUILD_DIR = INSTALLER_DIR / "dist"
INIT_FILE = INSTALLER_DIR / "__init__.py"


def get_platform_suffix() -> str:
    """Get platform-specific binary suffix."""
    system = platform.system().lower()
    machine = platform.machine().lower()

    # Normalize architecture names
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64"):
        arch = "arm64"
    else:
        arch = machine

    return f"{system}-{arch}"


def set_build_timestamp() -> str:
    """Set build timestamp in __init__.py and return the timestamp."""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    content = f'''"""Claude CodePro Installer - Professional step-based installation pipeline."""

__version__ = "1.0.0"
__build__ = "{timestamp}"
'''
    INIT_FILE.write_text(content)
    return timestamp


def reset_build_timestamp() -> None:
    """Reset __init__.py to dev mode."""
    content = '''"""Claude CodePro Installer - Professional step-based installation pipeline."""

__version__ = "1.0.0"
__build__ = "dev"  # Updated by CI during release builds
'''
    INIT_FILE.write_text(content)


def build_with_pyinstaller() -> Path:
    """Build using PyInstaller."""
    print("Building with PyInstaller...")

    output_name = f"ccp-installer-{get_platform_suffix()}"
    if platform.system() == "Windows":
        output_name += ".exe"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        output_name,
        "--distpath",
        str(BUILD_DIR),
        "--workpath",
        str(BUILD_DIR / "build"),
        "--specpath",
        str(BUILD_DIR / "build"),
        "--clean",
        "--noconfirm",
        # Add hidden imports for dependencies
        "--hidden-import=rich",
        "--hidden-import=InquirerPy",
        "--hidden-import=httpx",
        "--hidden-import=typer",
        "--hidden-import=platformdirs",
        # Entry point
        str(INSTALLER_DIR / "cli.py"),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd)

    return BUILD_DIR / output_name


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build ccp-installer binary")
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directory before building",
    )
    args = parser.parse_args()

    if args.clean and BUILD_DIR.exists():
        print(f"Cleaning {BUILD_DIR}...")
        shutil.rmtree(BUILD_DIR)

    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    # Set build timestamp before building
    timestamp = set_build_timestamp()
    print(f"Build timestamp: {timestamp}")

    try:
        output = build_with_pyinstaller()

        print(f"\n✓ Built: {output}")
        print(f"  Size: {output.stat().st_size / 1024 / 1024:.1f} MB")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}", file=sys.stderr)
        return 1

    finally:
        # Reset to dev mode after build
        reset_build_timestamp()


if __name__ == "__main__":
    sys.exit(main())
