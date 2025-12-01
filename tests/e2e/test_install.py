"""Simple E2E test for installer - verifies basic installation works."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def test_installer_creates_claude_directory(project_root):
    """Test that installer runs and creates .claude directory with key files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)

        # Initialize git repo (required for installation)
        subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        (project_dir / ".gitignore").touch()
        subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

        # Run installer
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "installer",
                "install",
                "--local",
                "--local-repo-dir",
                str(project_root),
                "--non-interactive",
                "--skip-env",
            ],
            cwd=project_dir,
            env={**subprocess.os.environ, "PYTHONPATH": str(project_root)},
            capture_output=True,
            text=True,
        )

        # Check installer succeeded
        assert result.returncode == 0, f"Installer failed: {result.stderr}"

        # Verify key directories and files created
        assert (project_dir / ".claude").is_dir()
        assert (project_dir / ".claude" / "hooks").is_dir()
        assert (project_dir / ".claude" / "rules").is_dir()
        assert (project_dir / ".claude" / "settings.local.json").exists()
        assert (project_dir / ".nvmrc").exists()
        assert (project_dir / ".mcp.json").exists()
