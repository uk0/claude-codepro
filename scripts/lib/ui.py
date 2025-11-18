"""
UI Functions - Colors and Print Utilities

Provides color-coded terminal output for user feedback.
"""

import sys

BLUE = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
NC = "\033[0m"


def print_status(message: str, file=None) -> None:
    """Print a status message in blue."""
    if file is None:
        file = sys.stdout
    print(f"{BLUE}{message}{NC}", file=file)


def print_success(message: str, file=None) -> None:
    """Print a success message in green with checkmark."""
    if file is None:
        file = sys.stdout
    print(f"{GREEN}✓ {message}{NC}", file=file)


def print_warning(message: str, file=None) -> None:
    """Print a warning message in yellow with warning symbol."""
    if file is None:
        file = sys.stdout
    print(f"{YELLOW}⚠ {message}{NC}", file=file)


def print_error(message: str, file=None) -> None:
    """Print an error message in red with X symbol."""
    if file is None:
        file = sys.stdout
    print(f"{RED}✗ {message}{NC}", file=file)


def print_section(title: str, file=None) -> None:
    """Print a section header with border."""
    if file is None:
        file = sys.stdout
    print("", file=file)
    print(f"{BLUE}═══════════════════════════════════════════════════════{NC}", file=file)
    print(f"{BLUE}  {title}{NC}", file=file)
    print(f"{BLUE}═══════════════════════════════════════════════════════{NC}", file=file)
    print("", file=file)


def supports_color() -> bool:
    """
    Check if the terminal supports color output.

    Returns True if:
    - stdout is a TTY
    - TERM environment variable is set and not 'dumb'
    """
    import os

    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    term = os.environ.get("TERM", "")
    return term != "dumb" and term != ""


def strip_colors(text: str) -> str:
    """Remove ANSI color codes from text."""
    import re

    ansi_escape = re.compile(r"\033\[[0-9;]*m")
    return ansi_escape.sub("", text)
