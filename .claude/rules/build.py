#!/usr/bin/env python3
"""
Rule Builder - Assembles slash commands and skills from markdown rules

Reads rules from .claude/rules/ and generates:
- Slash commands in .claude/commands/
- Skills in .claude/skills/*/SKILL.md
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path
from typing import NamedTuple


class RuleBuilderConfig(NamedTuple):
    """Configuration paths for rule builder."""

    claude_dir: Path
    rules_dir: Path
    commands_dir: Path
    skills_dir: Path


class Command(NamedTuple):
    """Command configuration from config.yaml."""

    name: str
    description: str
    model: str
    inject_skills: bool
    rules: list[tuple[str, str]]  # List of (source, rule_id) tuples


class Skill(NamedTuple):
    """Skill metadata."""

    name: str
    description: str


# Color codes
BLUE = "\033[0;36m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
NC = "\033[0m"


def log_info(message: str) -> None:
    """Log info message."""
    print(f"{BLUE}{message}{NC}", file=sys.stderr)


def log_success(message: str) -> None:
    """Log success message."""
    print(f"{GREEN}✓ {message}{NC}", file=sys.stderr)


def log_warning(message: str) -> None:
    """Log warning message."""
    print(f"{YELLOW}⚠ {message}{NC}", file=sys.stderr)


def log_source_header(source: str, is_first: bool) -> None:
    """Log source header (Standard or Custom) with appropriate formatting."""
    if is_first and source == "standard":
        log_info("  📦 Standard Rules:")
    elif is_first and source == "custom":
        log_info("")
        log_info("  🎨 Custom Rules:")


def extract_description_from_markdown(content: str) -> str:
    """Extract first non-heading line from markdown content as description."""
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return "No description"


def load_rules(config: RuleBuilderConfig) -> tuple[dict[str, dict[str, str]], int, int]:
    """
    Load rules from standard and custom directories.

    Returns:
        Tuple of (rules dict, standard_count, custom_count)
        rules dict format: {source: {rule_id: content}}
    """
    log_info("Loading rules...")
    log_info("")

    rules: dict[str, dict[str, str]] = {"standard": {}, "custom": {}}
    standard_count = 0
    custom_count = 0

    for source in ["standard", "custom"]:
        source_loaded = False

        for category in ["core", "workflow", "extended"]:
            category_dir = config.rules_dir / source / category
            if not category_dir.exists():
                continue

            for md_file in sorted(category_dir.glob("*.md")):
                if not source_loaded:
                    log_source_header(source, True)
                    source_loaded = True

                rule_id = md_file.stem
                rules[source][rule_id] = md_file.read_text()
                log_success(f"    {category}/{md_file.name}")

                if source == "standard":
                    standard_count += 1
                else:
                    custom_count += 1

    log_info("")
    log_info(f"Total: {standard_count + custom_count} rules ({standard_count} standard, {custom_count} custom)")

    return rules, standard_count, custom_count


def discover_skills(config: RuleBuilderConfig) -> list[Skill]:
    """
    Discover skills from extended directories.

    Returns:
        List of Skill objects
    """
    log_info("Discovering skills...")
    log_info("")

    skills: list[Skill] = []
    standard_count = 0
    custom_count = 0

    for source in ["standard", "custom"]:
        extended_dir = config.rules_dir / source / "extended"
        if not extended_dir.exists():
            continue

        source_has_skills = False

        for md_file in sorted(extended_dir.glob("*.md")):
            if not source_has_skills:
                log_source_header(source, True)
                source_has_skills = True

            skill_name = md_file.stem
            description = extract_description_from_markdown(md_file.read_text())

            skills.append(Skill(skill_name, description))
            log_success(f"    @{skill_name}")

            if source == "standard":
                standard_count += 1
            else:
                custom_count += 1

    log_info("")
    log_info(f"Total: {len(skills)} skills ({standard_count} standard, {custom_count} custom)")

    return skills


def format_skills_section(skills: list[Skill]) -> str:
    """Format skills section for command files."""
    if not skills:
        return ""

    lines = ["## Available Skills", ""]

    testing = [f"@{s.name}" for s in skills if s.name.startswith("testing-")]
    global_skills = [f"@{s.name}" for s in skills if s.name.startswith("global-")]
    backend = [f"@{s.name}" for s in skills if s.name.startswith("backend-")]
    frontend = [f"@{s.name}" for s in skills if s.name.startswith("frontend-")]

    if testing:
        lines.append(f"**Testing:** {' | '.join(testing)}")
    if global_skills:
        lines.append(f"**Global:** {' | '.join(global_skills)}")
    if backend:
        lines.append(f"**Backend:** {' | '.join(backend)}")
    if frontend:
        lines.append(f"**Frontend:** {' | '.join(frontend)}")

    lines.append("")
    return "\n".join(lines)


def parse_yaml_commands(config: RuleBuilderConfig) -> list[Command]:
    """
    Parse commands from config.yaml.

    Returns:
        List of Command objects
    """
    config_file = config.rules_dir / "config.yaml"
    commands: list[Command] = []

    current_command: str | None = None
    description = ""
    model = "sonnet"
    inject_skills = False
    rules_list: list[tuple[str, str]] = []
    in_commands = False
    in_rules = False
    in_standard = False
    in_custom = False

    for line in config_file.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        if line == "commands:":
            in_commands = True
            continue

        if in_commands:
            if line == "rules:":
                in_rules = True
                in_standard = False
                in_custom = False

            elif line == "standard:":
                in_standard = True
                in_custom = False

            elif line == "custom:":
                in_standard = False
                in_custom = True

            elif match := re.match(r"^([a-z_-]+):$", line):
                if line not in ["rules:", "standard:", "custom:"]:
                    if current_command:
                        commands.append(Command(current_command, description, model, inject_skills, rules_list[:]))

                    current_command = match.group(1)
                    description = ""
                    model = "sonnet"
                    inject_skills = False
                    rules_list = []
                    in_rules = False
                    in_standard = False
                    in_custom = False

            elif match := re.match(r"^description:\s*(.+)$", line):
                description = match.group(1)

            elif match := re.match(r"^model:\s*(.+)$", line):
                model = match.group(1)

            elif match := re.match(r"^inject_skills:\s*(true|false)$", line):
                inject_skills = match.group(1) == "true"

            elif match := re.match(r"^-\s*(.+)$", line):
                if in_rules:
                    rule_name = match.group(1)
                    if in_standard:
                        rules_list.append(("standard", rule_name))
                    elif in_custom:
                        rules_list.append(("custom", rule_name))
                    else:
                        rules_list.append(("standard", rule_name))

    if current_command:
        commands.append(Command(current_command, description, model, inject_skills, rules_list))

    return commands


def build_commands(config: RuleBuilderConfig, rules: dict[str, dict[str, str]], skills: list[Skill]) -> int:
    """
    Build command files from config.yaml and rules.

    Returns:
        Number of commands built
    """
    log_info("")
    log_info("Building commands...")

    if config.commands_dir.exists():
        shutil.rmtree(config.commands_dir)
    config.commands_dir.mkdir(parents=True)

    commands = parse_yaml_commands(config)
    command_count = 0

    for cmd in commands:
        command_file = config.commands_dir / f"{cmd.name}.md"

        content = [
            "---",
            f"description: {cmd.description}",
            f"model: {cmd.model}",
            "---",
        ]

        for source, rule_id in cmd.rules:
            if rule_id in rules[source]:
                content.append(rules[source][rule_id])
                content.append("")
            else:
                log_warning(f"Rule '{rule_id}' not found in {source}/")

        if cmd.inject_skills:
            content.append(format_skills_section(skills))

        command_file.write_text("\n".join(content))

        if cmd.inject_skills:
            log_success(f"Generated {cmd.name}.md (with skills)")
        else:
            log_success(f"Generated {cmd.name}.md")

        command_count += 1

    return command_count


def build_skills(config: RuleBuilderConfig, rules: dict[str, dict[str, str]]) -> int:
    """
    Build skill files from extended rules.

    Returns:
        Number of skills built
    """
    log_info("")
    log_info("Building skills...")

    if config.skills_dir.exists():
        shutil.rmtree(config.skills_dir)
    config.skills_dir.mkdir(parents=True)

    skill_count = 0

    for source in ["standard", "custom"]:
        extended_dir = config.rules_dir / source / "extended"
        if not extended_dir.exists():
            continue

        for md_file in sorted(extended_dir.glob("*.md")):
            rule_id = md_file.stem

            if rule_id in rules[source]:
                skill_dir = config.skills_dir / rule_id
                skill_dir.mkdir(parents=True)

                skill_file = skill_dir / "SKILL.md"
                skill_file.write_text(rules[source][rule_id])

                log_success(f"Generated {rule_id}/SKILL.md")
                skill_count += 1

    return skill_count


def main() -> None:
    """Main entry point."""
    script_dir = Path(__file__).parent.resolve()
    claude_dir = script_dir.parent

    config = RuleBuilderConfig(
        claude_dir=claude_dir,
        rules_dir=script_dir,
        commands_dir=claude_dir / "commands",
        skills_dir=claude_dir / "skills",
    )

    log_info("═══════════════════════════════════════════════════════")
    log_info("  Claude CodePro Rule Builder")
    log_info("═══════════════════════════════════════════════════════")
    log_info("")

    if not config.rules_dir.exists():
        print(f"Error: Rules directory not found at {config.rules_dir}")
        sys.exit(1)

    rules, _, _ = load_rules(config)
    skills = discover_skills(config)

    command_count = build_commands(config, rules, skills)
    skill_count = build_skills(config, rules)

    log_info("")
    log_info("═══════════════════════════════════════════════════════")
    log_success("Claude CodePro Build Complete!")
    log_info(f"   Commands: {command_count} files")
    log_info(f"   Skills: {skill_count} files")
    log_info(f"   Available skills: {len(skills)}")
    log_info("═══════════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
