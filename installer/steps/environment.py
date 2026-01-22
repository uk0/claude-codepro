"""Environment step - sets up .env file with API keys."""

from __future__ import annotations

import os
from pathlib import Path

from installer.context import InstallContext
from installer.steps.base import BaseStep

OBSOLETE_ENV_KEYS = [
    "MILVUS_TOKEN",
    "MILVUS_ADDRESS",
    "VECTOR_STORE_USERNAME",
    "VECTOR_STORE_PASSWORD",
    "EXA_API_KEY",
    "GEMINI_API_KEY",
]


def remove_env_key(key: str, env_file: Path) -> bool:
    """Remove an environment key from .env file. Returns True if key was removed."""
    if not env_file.exists():
        return False

    lines = env_file.read_text().splitlines()
    new_lines = [line for line in lines if not line.strip().startswith(f"{key}=")]

    if len(new_lines) != len(lines):
        env_file.write_text("\n".join(new_lines) + "\n" if new_lines else "")
        return True
    return False


def cleanup_obsolete_env_keys(env_file: Path) -> list[str]:
    """Remove obsolete environment keys from .env file. Returns list of removed keys."""
    removed = []
    for key in OBSOLETE_ENV_KEYS:
        if remove_env_key(key, env_file):
            removed.append(key)
    return removed


def key_exists_in_file(key: str, env_file: Path) -> bool:
    """Check if key exists in .env file with a non-empty value."""
    if not env_file.exists():
        return False

    content = env_file.read_text()
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith(f"{key}="):
            value = line[len(key) + 1 :].strip()
            return bool(value)
    return False


def key_is_set(key: str, env_file: Path) -> bool:
    """Check if key exists in .env file OR is already set as environment variable."""
    if os.environ.get(key):
        return True
    return key_exists_in_file(key, env_file)


def add_env_key(key: str, value: str, env_file: Path) -> None:
    """Add environment key to .env file if it doesn't exist."""
    if key_exists_in_file(key, env_file):
        return

    with open(env_file, "a") as f:
        f.write(f"{key}={value}\n")


class EnvironmentStep(BaseStep):
    """Step that cleans up .env file (API keys are collected earlier in CLI)."""

    name = "environment"

    def check(self, ctx: InstallContext) -> bool:
        """Always returns False - environment step should always run for cleanup."""
        return False

    def run(self, ctx: InstallContext) -> None:
        """Clean up .env file - remove obsolete keys."""
        ui = ctx.ui
        env_file = ctx.project_dir / ".env"

        if ctx.skip_env or ctx.non_interactive:
            return

        if env_file.exists():
            removed_keys = cleanup_obsolete_env_keys(env_file)
            if removed_keys and ui:
                ui.print(f"  [dim]Cleaned up obsolete keys: {', '.join(removed_keys)}[/dim]")

    def rollback(self, ctx: InstallContext) -> None:
        """No rollback for environment setup."""
        pass
