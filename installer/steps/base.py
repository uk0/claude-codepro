"""Base classes and protocols for installation steps."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Protocol, runtime_checkable

if TYPE_CHECKING:
    from installer.context import InstallContext


@runtime_checkable
class Step(Protocol):
    """Protocol defining the interface for installation steps."""

    name: ClassVar[str]

    def check(self, ctx: InstallContext) -> bool:
        """Check if this step is already complete."""
        ...

    def run(self, ctx: InstallContext) -> None:
        """Execute the installation step."""
        ...

    def rollback(self, ctx: InstallContext) -> None:
        """Rollback changes made by this step."""
        ...


class BaseStep(ABC, Step):
    """Abstract base class for installation steps with default implementations."""

    name: ClassVar[str] = ""

    @abstractmethod
    def check(self, ctx: InstallContext) -> bool:
        """Check if this step is already complete."""
        ...

    @abstractmethod
    def run(self, ctx: InstallContext) -> None:
        """Execute the installation step."""
        ...

    def rollback(self, ctx: InstallContext) -> None:
        """Rollback changes made by this step. Default is no-op."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name!r})>"
