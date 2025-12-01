"""Shell config step - adds ccp alias to shell configuration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from installer.platform_utils import get_shell_config_files
from installer.steps.base import BaseStep

if TYPE_CHECKING:
    from installer.context import InstallContext

CCP_ALIAS_MARKER = "# Claude CodePro alias"


def get_alias_line(shell_type: str) -> str:
    """Get the alias line for the given shell type.

    Creates an alias that:
    1. If current dir is CCP project (.claude/rules/build.py exists) → use it
    2. If in devcontainer (/workspaces exists) → find CCP project there
    3. Otherwise → show error

    The alias:
    - Uses nvm to set Node.js 22
    - Runs build.py to compile rules
    - Clears screen
    - Uses dotenvx to load environment variables before running claude
    """
    if shell_type == "fish":
        # Fish shell uses 'and' instead of '&&' and different syntax
        return (
            f"{CCP_ALIAS_MARKER}\n"
            "alias ccp='"
            "if test -f .claude/rules/build.py; "
            "nvm use 22; and python3 .claude/rules/build.py &>/dev/null; and clear; and dotenvx run claude; "
            "else if test -d /workspaces; "
            'set ccp_dir ""; for d in /workspaces/*/; test -f "$d.claude/rules/build.py"; and set ccp_dir "$d"; and break; end; '
            'if test -n "$ccp_dir"; cd "$ccp_dir"; and nvm use 22; and python3 .claude/rules/build.py &>/dev/null; and clear; and dotenvx run claude; '
            'else; echo "Error: No CCP project found in /workspaces"; end; '
            "else; "
            'echo "Error: Not a Claude CodePro project. Please cd to a CCP-enabled project first."; '
            "end'"
        )
    else:
        # Bash/Zsh syntax
        return (
            f"{CCP_ALIAS_MARKER}\n"
            "alias ccp='"
            "if [ -f .claude/rules/build.py ]; then "
            "nvm use 22 && python3 .claude/rules/build.py &>/dev/null && clear && dotenvx run claude; "
            "elif [ -d /workspaces ]; then "
            'ccp_dir=""; for d in /workspaces/*/; do [ -f "$d.claude/rules/build.py" ] && ccp_dir="$d" && break; done; '
            'if [ -n "$ccp_dir" ]; then cd "$ccp_dir" && nvm use 22 && python3 .claude/rules/build.py &>/dev/null && clear && dotenvx run claude; '
            'else echo "Error: No CCP project found in /workspaces"; fi; '
            "else "
            'echo "Error: Not a Claude CodePro project. Please cd to a CCP-enabled project first."; '
            "fi'"
        )


def alias_exists_in_file(config_file: Path) -> bool:
    """Check if ccp alias already exists in config file."""
    if not config_file.exists():
        return False
    content = config_file.read_text()
    return "alias ccp" in content or CCP_ALIAS_MARKER in content


class ShellConfigStep(BaseStep):
    """Step that configures shell aliases."""

    name = "shell_config"

    def check(self, ctx: InstallContext) -> bool:
        """Check if alias already exists in shell configs."""
        config_files = get_shell_config_files()
        for config_file in config_files:
            if alias_exists_in_file(config_file):
                return True
        return False

    def run(self, ctx: InstallContext) -> None:
        """Add ccp alias to shell configuration files."""
        ui = ctx.ui
        config_files = get_shell_config_files()
        modified_files: list[str] = []

        if ui:
            ui.status("Configuring shell alias...")

        for config_file in config_files:
            if not config_file.exists():
                continue

            if alias_exists_in_file(config_file):
                if ui:
                    ui.status(f"Alias already exists in {config_file.name}")
                continue

            # Determine shell type
            shell_type = "fish" if "fish" in config_file.name else "bash"
            alias_line = get_alias_line(shell_type)

            # Append alias to config
            try:
                with open(config_file, "a") as f:
                    f.write(f"\n{alias_line}\n")
                modified_files.append(str(config_file))
                if ui:
                    ui.success(f"Added alias to {config_file.name}")
            except (OSError, IOError) as e:
                if ui:
                    ui.warning(f"Could not modify {config_file.name}: {e}")

        ctx.config["modified_shell_configs"] = modified_files

        if ui and modified_files:
            ui.print()
            ui.status("To use the 'ccp' command, reload your shell:")
            ui.print("  source ~/.bashrc  # or ~/.zshrc")

    def rollback(self, ctx: InstallContext) -> None:
        """Remove alias from modified config files."""
        modified_files = ctx.config.get("modified_shell_configs", [])

        for file_path in modified_files:
            config_file = Path(file_path)
            if not config_file.exists():
                continue

            try:
                content = config_file.read_text()
                # Remove alias block
                lines = content.split("\n")
                new_lines = []
                skip_next = False

                for line in lines:
                    if CCP_ALIAS_MARKER in line:
                        skip_next = True
                        continue
                    if skip_next and line.startswith("alias ccp"):
                        skip_next = False
                        continue
                    skip_next = False
                    new_lines.append(line)

                config_file.write_text("\n".join(new_lines))
            except (OSError, IOError):
                pass
