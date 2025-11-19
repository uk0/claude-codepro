"""
File Management Functions - Install and manage Claude CodePro files

Provides file installation and configuration merging capabilities.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

from . import downloads, ui


def _ensure_pyyaml_installed() -> bool:
    """
    Ensure PyYAML is installed and importable in the current Python environment.

    Returns:
        True if PyYAML is available, False otherwise
    """
    # Try importing yaml first
    try:
        import yaml  # type: ignore[import-untyped]

        return True
    except ImportError:
        pass

    # PyYAML not available, attempt installation
    ui.print_status("PyYAML not found, installing...")

    # Always use the current Python executable's pip for consistency
    # This ensures we install to the same environment we're running in
    install_cmd = [sys.executable, "-m", "pip", "install", "pyyaml"]
    package_manager = "pip"

    try:
        # Try standard installation first
        result = subprocess.run(
            install_cmd,
            capture_output=True,
            text=True,
            check=False,
        )

        # If that fails, try with --user flag (for systems without write access)
        if result.returncode != 0:
            ui.print_status("Retrying with --user flag...")
            install_cmd_user = install_cmd + ["--user"]
            result = subprocess.run(
                install_cmd_user,
                capture_output=True,
                text=True,
                check=False,
            )

        # Check if installation succeeded
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            ui.print_warning(f"Failed to install PyYAML: {error_msg[:200]}")
            return False

        ui.print_success(f"Installed PyYAML using {package_manager}")

        # Verify the import works after installation
        try:
            import importlib

            importlib.import_module("yaml")
            return True
        except ImportError:
            # Installation succeeded but import failed - this can happen when
            # installing to --user location that's not yet in sys.path
            ui.print_warning("PyYAML installed but not immediately importable")
            return False

    except Exception as e:
        ui.print_warning(f"Failed to install PyYAML: {e}")
        return False


def install_directory(
    repo_dir: str,
    dest_base: Path,
    config: downloads.DownloadConfig,
) -> int:
    """
    Install all files from a repository directory.

    Args:
        repo_dir: Repository directory path (e.g., ".claude")
        dest_base: Destination base directory
        config: Download configuration

    Returns:
        Number of files installed
    """
    ui.print_status(f"Installing {repo_dir} files...")

    file_count = 0
    files = downloads.get_repo_files(repo_dir, config)

    for file_path in files:
        if not file_path:
            continue

        dest_file = dest_base / file_path

        if downloads.download_file(file_path, dest_file, config):
            file_count += 1
            print(f"   ✓ {Path(file_path).name}")

    ui.print_success(f"Installed {file_count} files")
    return file_count


def install_file(
    repo_file: str,
    dest_file: Path,
    config: downloads.DownloadConfig,
) -> bool:
    """
    Install a single file from repository.

    Args:
        repo_file: Repository file path
        dest_file: Destination file path
        config: Download configuration

    Returns:
        True on success, False on failure
    """
    if downloads.download_file(repo_file, dest_file, config):
        ui.print_success(f"Installed {repo_file}")
        return True
    else:
        ui.print_warning(f"Failed to install {repo_file}")
        return False


def merge_mcp_config(
    repo_file: str,
    dest_file: Path,
    config: downloads.DownloadConfig,
    temp_dir: Path,
) -> bool:
    """
    Merge MCP configuration files.

    Preserves existing server configurations while adding new ones.

    Args:
        repo_file: Repository file path (e.g., ".mcp.json")
        dest_file: Destination file path
        config: Download configuration
        temp_dir: Temporary directory for downloads

    Returns:
        True on success, False on failure
    """
    ui.print_status("Installing MCP configuration...")

    temp_file = temp_dir / "mcp-temp.json"

    if not downloads.download_file(repo_file, temp_file, config):
        ui.print_warning(f"Failed to download {repo_file}")
        return False

    if not dest_file.exists():
        _ = shutil.copy2(temp_file, dest_file)
        ui.print_success(f"Created {repo_file}")
        return True

    try:
        with open(dest_file, "r") as f:
            existing_config = json.load(f)

        with open(temp_file, "r") as f:
            new_config = json.load(f)

        server_key = None
        if "mcpServers" in existing_config:
            server_key = "mcpServers"
        elif "servers" in existing_config:
            server_key = "servers"
        elif "mcpServers" in new_config:
            server_key = "mcpServers"
        elif "servers" in new_config:
            server_key = "servers"

        if server_key:
            existing_servers = existing_config.get(server_key, {})
            new_servers = new_config.get(server_key, {})

            merged_servers = {**new_servers, **existing_servers}

            merged_config = {**new_config, **existing_config}
            merged_config[server_key] = merged_servers
        else:
            merged_config = {**new_config, **existing_config}

        with open(dest_file, "w") as f:
            json.dump(merged_config, f, indent=2)
            _ = f.write("\n")

        ui.print_success("Merged MCP servers (preserved existing configuration)")
        return True

    except Exception as e:
        ui.print_warning(f"Failed to merge MCP configuration: {e}, preserving existing")
        return False


def merge_yaml_config(
    new_config_path: Path,
    existing_config_path: Path,
) -> bool:
    """
    Merge YAML rules config, preserving custom sections.

    This function merges config.yaml files, taking the new standard rules
    while preserving the user's custom rules.

    Args:
        new_config_path: Path to new config file
        existing_config_path: Path to existing config file to update

    Returns:
        True on success, False on failure
    """
    try:
        # Ensure PyYAML is installed
        if not _ensure_pyyaml_installed():
            # PyYAML unavailable - fallback to simple copy
            ui.print_warning("PyYAML unavailable - copying new config.yaml (custom rules may need manual merge)")
            shutil.copy2(new_config_path, existing_config_path)
            return True

        # Import after ensuring it's installed
        import yaml  # type: ignore[import-untyped]

        # Load both configurations
        with open(new_config_path, "r") as f:
            new_config = yaml.safe_load(f)

        with open(existing_config_path, "r") as f:
            existing_config = yaml.safe_load(f)

        # Merge: preserve custom rules from existing config
        if "commands" in new_config and "commands" in existing_config:
            for cmd_name, cmd_config in new_config["commands"].items():
                if cmd_name in existing_config["commands"]:
                    # Extract custom rules from existing config
                    old_custom = existing_config["commands"][cmd_name].get("rules", {}).get("custom", [])

                    # Add custom rules to new config
                    if "rules" not in cmd_config:
                        cmd_config["rules"] = {}
                    cmd_config["rules"]["custom"] = old_custom

        # Write merged configuration
        with open(existing_config_path, "w") as f:
            yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)

        ui.print_success("Merged config.yaml (preserved custom rules)")
        return True

    except Exception as e:
        ui.print_error(f"Failed to merge YAML config: {e}")
        return False
