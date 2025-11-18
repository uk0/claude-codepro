"""Pytest configuration for E2E tests."""

from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure(config):
    """Configure pytest for E2E tests."""
    # Add project root to Python path so we can import modules
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
