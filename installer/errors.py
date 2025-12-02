"""Custom exception hierarchy for installer."""

from __future__ import annotations


class InstallError(Exception):
    """Base exception for recoverable installation errors."""

    pass


class FatalInstallError(InstallError):
    """Fatal error that requires abort and rollback."""

    pass


class ConfigError(InstallError):
    """Configuration error."""

    pass
