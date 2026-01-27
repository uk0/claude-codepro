"""User configuration persistence for installer preferences."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CONFIG_DIR = ".claude/config"
CONFIG_FILE = "ccp-config.json"


def get_config_path(project_dir: Path) -> Path:
    """Get the path to the config file."""
    return project_dir / CONFIG_DIR / CONFIG_FILE


def load_config(project_dir: Path) -> dict[str, Any]:
    """Load user configuration from .claude/config/ccp-config.json."""
    config_path = get_config_path(project_dir)
    if config_path.exists():
        try:
            return json.loads(config_path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_config(project_dir: Path, config: dict[str, Any]) -> bool:
    """Save user configuration to .claude/config/ccp-config.json."""
    config_path = get_config_path(project_dir)
    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(config, indent=2) + "\n")
        return True
    except OSError:
        return False
