"""Tests for install.sh bootstrap script."""

from __future__ import annotations

from pathlib import Path


def test_install_sh_runs_python_installer():
    """Verify install.sh runs the Python installer module."""
    install_sh = Path(__file__).parent.parent.parent / "install.sh"
    content = install_sh.read_text()

    # The script must run the Python installer module
    assert "python3 -m installer" in content, "install.sh must run Python installer module"

    # Check that it passes the install command
    assert "install" in content, "install.sh must pass 'install' command"

    # Check for local-system flag support
    assert "--local-system" in content, "install.sh must support --local-system flag"


def test_install_sh_downloads_installer_files():
    """Verify install.sh downloads the installer Python package dynamically."""
    install_sh = Path(__file__).parent.parent.parent / "install.sh"
    content = install_sh.read_text()

    # Must have download_installer function
    assert "download_installer" in content, "install.sh must have download_installer function"

    # Must use GitHub API to dynamically discover files
    assert "api.github.com" in content, "Must use GitHub API for file discovery"
    assert "git/trees" in content, "Must use git trees API endpoint"

    # Must filter for Python files in installer directory
    assert "installer/" in content, "Must filter for installer directory"
    assert ".py" in content, "Must filter for Python files"


def test_install_sh_downloads_ccp_binary():
    """Verify install.sh downloads the CCP binary."""
    install_sh = Path(__file__).parent.parent.parent / "install.sh"
    content = install_sh.read_text()

    # Must download CCP binary
    assert "download_ccp_binary" in content, "install.sh must have download_ccp_binary function"
    assert "ccp-" in content, "Must reference ccp binary name"
    assert ".claude/bin/ccp" in content, "Must install to .claude/bin/ccp"


def test_install_sh_ensures_python_for_local_mode():
    """Verify install.sh ensures Python is available for local mode."""
    install_sh = Path(__file__).parent.parent.parent / "install.sh"
    content = install_sh.read_text()

    # Must check for Python
    assert "check_python" in content, "install.sh must have check_python function"
    assert "install_python" in content, "install.sh must have install_python function"
    assert "python3" in content, "Must reference python3"


def test_install_sh_ensures_homebrew_for_local_mode():
    """Verify install.sh ensures Homebrew is available for local mode."""
    install_sh = Path(__file__).parent.parent.parent / "install.sh"
    content = install_sh.read_text()

    # Must check for Homebrew
    assert "check_homebrew" in content, "install.sh must have check_homebrew function"
    assert "install_homebrew" in content, "install.sh must have install_homebrew function"


def test_install_sh_is_executable_bash_script():
    """Verify install.sh has proper shebang."""
    install_sh = Path(__file__).parent.parent.parent / "install.sh"
    content = install_sh.read_text()

    assert content.startswith("#!/bin/bash"), "install.sh must start with bash shebang"


def test_install_sh_has_devcontainer_support():
    """Verify install.sh supports dev container mode."""
    install_sh = Path(__file__).parent.parent.parent / "install.sh"
    content = install_sh.read_text()

    assert "is_in_container" in content, "Must have container detection"
    assert "setup_devcontainer" in content, "Must have devcontainer setup"
    assert ".devcontainer" in content, "Must reference .devcontainer directory"


def test_install_sh_sets_pythonpath():
    """Verify install.sh sets PYTHONPATH for the installer."""
    install_sh = Path(__file__).parent.parent.parent / "install.sh"
    content = install_sh.read_text()

    assert "PYTHONPATH" in content, "Must set PYTHONPATH for installer module"
    assert ".claude/installer" in content, "Must reference installer directory"
