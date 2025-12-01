"""Step registry for installation pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import Step

# Registry of all available steps, populated by step modules
STEP_REGISTRY: dict[str, type[Step]] = {}


def register_step(step_class: type[Step]) -> type[Step]:
    """Decorator to register a step class in the registry."""
    STEP_REGISTRY[step_class.name] = step_class
    return step_class


def get_step(name: str) -> type[Step] | None:
    """Get a step class by name from the registry."""
    return STEP_REGISTRY.get(name)


def get_all_steps() -> list[type[Step]]:
    """Get all registered step classes in order."""
    return list(STEP_REGISTRY.values())
