"""Environment step - sets up .env file with API keys."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext


class EnvironmentStep(BaseStep):
    """Step that sets up the .env file for API keys."""

    name = "environment"

    def check(self, ctx: InstallContext) -> bool:
        """Check if .env file exists."""
        env_file = ctx.project_dir / ".env"
        return env_file.exists()

    def run(self, ctx: InstallContext) -> None:
        """Set up .env file with API keys."""
        ui = ctx.ui
        env_file = ctx.project_dir / ".env"

        if ctx.non_interactive:
            if ui:
                ui.status("Skipping .env setup (non-interactive mode)")
            return

        if ui:
            ui.section("Environment Setup")
            ui.status("Setting up API keys...")

        # Read existing content if any
        existing_content = ""
        if env_file.exists():
            existing_content = env_file.read_text()

        new_entries: list[str] = []

        # Prompt for each API key if not already set
        api_keys = [
            ("ZILLIZ_API_KEY", "Zilliz Cloud API Key (for Cipher memory)"),
            ("OPENAI_API_KEY", "OpenAI API Key (for embeddings)"),
            ("EXA_API_KEY", "Exa API Key (for web search)"),
        ]

        for key, description in api_keys:
            if key not in existing_content:
                if ui:
                    value = ui.input(f"{description}:", default="")
                    if value:
                        new_entries.append(f"{key}={value}")

        # Append new entries
        if new_entries:
            with open(env_file, "a") as f:
                if existing_content and not existing_content.endswith("\n"):
                    f.write("\n")
                f.write("\n".join(new_entries) + "\n")
            if ui:
                ui.success(f"Added {len(new_entries)} API keys to .env")
        else:
            if ui:
                ui.success("Environment setup complete")

    def rollback(self, ctx: InstallContext) -> None:
        """No rollback for environment setup."""
        pass
