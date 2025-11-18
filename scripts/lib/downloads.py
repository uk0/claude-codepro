"""
Download Functions - GitHub file downloads and API interactions

Provides file download capabilities from GitHub repositories with local mode support.
"""

from __future__ import annotations

import json
import shutil
import urllib.request
from pathlib import Path

from . import ui


class DownloadConfig:
    """Configuration for download operations."""

    def __init__(
        self,
        repo_url: str,
        repo_branch: str,
        local_mode: bool = False,
        local_repo_dir: Path | None = None,
    ):
        self.repo_url = repo_url
        self.repo_branch = repo_branch
        self.local_mode = local_mode
        self.local_repo_dir = local_repo_dir


def download_file(
    repo_path: str,
    dest_path: Path,
    config: DownloadConfig,
) -> bool:
    """
    Download a file from the repository (or copy if in local mode).

    Args:
        repo_path: Repository path (e.g., "scripts/install.sh")
        dest_path: Destination path on local filesystem
        config: Download configuration

    Returns:
        True on success, False on failure
    """

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if config.local_mode and config.local_repo_dir:
        source_file = config.local_repo_dir / repo_path
        if source_file.is_file():
            try:
                if source_file.resolve() == dest_path.resolve():
                    return True
                shutil.copy2(source_file, dest_path)
                return True
            except Exception:
                return False
        else:
            return False
    else:
        file_url = f"{config.repo_url}/raw/{config.repo_branch}/{repo_path}"
        try:
            with urllib.request.urlopen(file_url) as response:
                if response.status == 200:
                    dest_path.write_bytes(response.read())
                    return True
                else:
                    return False
        except Exception:
            return False


def get_repo_files(dir_path: str, config: DownloadConfig) -> list[str]:
    """
    Get all files from a repository directory (using GitHub API or local find).

    Args:
        dir_path: Directory path in repository (e.g., ".claude")
        config: Download configuration

    Returns:
        List of file paths relative to repository root
    """

    if config.local_mode and config.local_repo_dir:
        source_dir = config.local_repo_dir / dir_path
        if source_dir.is_dir():
            files = []
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(config.local_repo_dir)
                    files.append(str(rel_path))
            return files
        return []

    try:
        repo_path = config.repo_url.replace("https://github.com/", "")
        tree_url = f"https://api.github.com/repos/{repo_path}/git/trees/{config.repo_branch}?recursive=true"

        with urllib.request.urlopen(tree_url) as response:
            if response.status != 200:
                ui.print_error("Failed to fetch repository tree from GitHub API")
                return []

            data = json.loads(response.read().decode())

            files = []
            if "tree" in data:
                for item in data["tree"]:
                    if item.get("type") == "blob":
                        path = item.get("path", "")
                        if path.startswith(dir_path):
                            files.append(path)

            return files

    except Exception as e:
        ui.print_error(f"Error fetching repository files: {e}")
        return []


def download_directory(
    repo_dir: str,
    dest_dir: Path,
    config: DownloadConfig,
    exclude_patterns: list[str] | None = None,
) -> int:
    """
    Download an entire directory from the repository.

    Args:
        repo_dir: Directory path in repository
        dest_dir: Destination directory on local filesystem
        config: Download configuration
        exclude_patterns: List of patterns to exclude (e.g., ["*.pyc", "__pycache__"])

    Returns:
        Number of files successfully downloaded
    """
    if exclude_patterns is None:
        exclude_patterns = []

    files = get_repo_files(repo_dir, config)
    count = 0

    for file_path in files:
        if any(pattern in file_path for pattern in exclude_patterns):
            continue

        rel_path = Path(file_path).relative_to(repo_dir)
        dest_path = dest_dir / rel_path

        if download_file(file_path, dest_path, config):
            count += 1

    return count
