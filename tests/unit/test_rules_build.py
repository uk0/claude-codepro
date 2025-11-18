"""Unit tests for .claude/rules/build.py."""

from __future__ import annotations

import sys
import tempfile
from io import StringIO
from pathlib import Path

import pytest

# Import the module under test
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".claude" / "rules"))
from build import (
    Command,
    RuleBuilderConfig,
    Skill,
    build_commands,
    build_skills,
    discover_skills,
    format_skills_section,
    load_rules,
    log_info,
    log_success,
    log_warning,
    parse_yaml_commands,
)


class TestSkillNamedTuple:
    """Test Skill NamedTuple."""

    def test_skill_creation_with_valid_data_creates_skill_object(self):
        """Test that Skill can be created with name and description."""
        skill = Skill(name="test-skill", description="Test description")

        assert skill.name == "test-skill"
        assert skill.description == "Test description"


class TestCommandNamedTuple:
    """Test Command NamedTuple."""

    def test_command_creation_with_all_fields_creates_command_object(self):
        """Test that Command can be created with all required fields."""
        rules = [("standard", "rule1"), ("custom", "rule2")]
        command = Command(
            name="test",
            description="Test command",
            model="sonnet",
            inject_skills=True,
            rules=rules,
        )

        assert command.name == "test"
        assert command.description == "Test command"
        assert command.model == "sonnet"
        assert command.inject_skills is True
        assert command.rules == rules


class TestRuleBuilderConfigNamedTuple:
    """Test RuleBuilderConfig NamedTuple."""

    def test_config_creation_with_path_objects_creates_config(self):
        """Test that RuleBuilderConfig can be created with Path objects."""
        claude_dir = Path("/test/claude")
        rules_dir = Path("/test/rules")
        commands_dir = Path("/test/commands")
        skills_dir = Path("/test/skills")

        config = RuleBuilderConfig(
            claude_dir=claude_dir,
            rules_dir=rules_dir,
            commands_dir=commands_dir,
            skills_dir=skills_dir,
        )

        assert config.claude_dir == claude_dir
        assert config.rules_dir == rules_dir
        assert config.commands_dir == commands_dir
        assert config.skills_dir == skills_dir


class TestLogFunctions:
    """Test logging functions."""

    def test_log_info_outputs_message_with_blue_color_to_stderr(self, capsys):
        """Test that log_info outputs colored message to stderr."""
        log_info("Test message")

        captured = capsys.readouterr()
        assert "Test message" in captured.err
        assert "\033[0;36m" in captured.err  # Blue color code
        assert "\033[0m" in captured.err  # Reset code

    def test_log_success_outputs_message_with_green_checkmark_to_stderr(self, capsys):
        """Test that log_success outputs colored message with checkmark to stderr."""
        log_success("Success message")

        captured = capsys.readouterr()
        assert "Success message" in captured.err
        assert "✓" in captured.err
        assert "\033[0;32m" in captured.err  # Green color code
        assert "\033[0m" in captured.err  # Reset code

    def test_log_warning_outputs_message_with_yellow_warning_to_stderr(self, capsys):
        """Test that log_warning outputs colored message with warning symbol to stderr."""
        log_warning("Warning message")

        captured = capsys.readouterr()
        assert "Warning message" in captured.err
        assert "⚠" in captured.err
        assert "\033[1;33m" in captured.err  # Yellow color code
        assert "\033[0m" in captured.err  # Reset code


class TestFormatSkillsSection:
    """Test format_skills_section function."""

    def test_format_skills_section_with_empty_list_returns_empty_string(self):
        """Test that empty skills list returns empty string."""
        result = format_skills_section([])

        assert result == ""

    def test_format_skills_section_with_testing_skills_returns_testing_section(self):
        """Test that testing skills are formatted in Testing section."""
        skills = [
            Skill("testing-anti-patterns", "Prevent testing anti-patterns"),
            Skill("testing-writing-guidelines", "Writing guidelines"),
        ]

        result = format_skills_section(skills)

        assert "## Available Skills" in result
        assert "**Testing:**" in result
        assert "@testing-anti-patterns" in result
        assert "@testing-writing-guidelines" in result

    def test_format_skills_section_with_global_skills_returns_global_section(self):
        """Test that global skills are formatted in Global section."""
        skills = [
            Skill("global-standards", "Global standards"),
        ]

        result = format_skills_section(skills)

        assert "**Global:**" in result
        assert "@global-standards" in result

    def test_format_skills_section_with_backend_skills_returns_backend_section(self):
        """Test that backend skills are formatted in Backend section."""
        skills = [
            Skill("backend-api-standards", "API standards"),
            Skill("backend-python-standards", "Python standards"),
        ]

        result = format_skills_section(skills)

        assert "**Backend:**" in result
        assert "@backend-api-standards" in result
        assert "@backend-python-standards" in result

    def test_format_skills_section_with_frontend_skills_returns_frontend_section(self):
        """Test that frontend skills are formatted in Frontend section."""
        skills = [
            Skill("frontend-css-standards", "CSS standards"),
        ]

        result = format_skills_section(skills)

        assert "**Frontend:**" in result
        assert "@frontend-css-standards" in result

    def test_format_skills_section_with_mixed_skills_returns_all_sections(self):
        """Test that mixed skills are formatted in appropriate sections."""
        skills = [
            Skill("testing-anti-patterns", "Testing"),
            Skill("global-standards", "Global"),
            Skill("backend-api-standards", "Backend API"),
            Skill("frontend-css-standards", "Frontend CSS"),
        ]

        result = format_skills_section(skills)

        assert "**Testing:**" in result
        assert "**Global:**" in result
        assert "**Backend:**" in result
        assert "**Frontend:**" in result
        assert "@testing-anti-patterns" in result
        assert "@global-standards" in result
        assert "@backend-api-standards" in result
        assert "@frontend-css-standards" in result

    def test_format_skills_section_skills_separated_by_pipe_in_same_category(self):
        """Test that multiple skills in same category are pipe-separated."""
        skills = [
            Skill("backend-api-standards", "API"),
            Skill("backend-python-standards", "Python"),
        ]

        result = format_skills_section(skills)

        assert "@backend-api-standards | @backend-python-standards" in result


@pytest.fixture
def temp_rules_dir():
    """Create a temporary rules directory structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        rules_dir = Path(tmpdir)
        yield rules_dir


@pytest.fixture
def config_with_rules(temp_rules_dir):
    """Create a RuleBuilderConfig with temporary directories."""
    claude_dir = temp_rules_dir.parent
    commands_dir = claude_dir / "commands"
    skills_dir = claude_dir / "skills"

    return RuleBuilderConfig(
        claude_dir=claude_dir,
        rules_dir=temp_rules_dir,
        commands_dir=commands_dir,
        skills_dir=skills_dir,
    )


class TestLoadRules:
    """Test load_rules function."""

    def test_load_rules_with_no_rules_returns_empty_dicts(self, config_with_rules):
        """Test that load_rules returns empty dicts when no rules exist."""
        rules, standard_count, custom_count = load_rules(config_with_rules)

        assert rules == {"standard": {}, "custom": {}}
        assert standard_count == 0
        assert custom_count == 0

    def test_load_rules_with_standard_core_rules_returns_rules_dict(self, config_with_rules):
        """Test that load_rules loads standard core rules."""
        # Create standard core rule
        core_dir = config_with_rules.rules_dir / "standard" / "core"
        core_dir.mkdir(parents=True)
        (core_dir / "test-rule.md").write_text("# Test Rule\n\nTest content")

        rules, standard_count, custom_count = load_rules(config_with_rules)

        assert "test-rule" in rules["standard"]
        assert rules["standard"]["test-rule"] == "# Test Rule\n\nTest content"
        assert standard_count == 1
        assert custom_count == 0

    def test_load_rules_with_custom_workflow_rules_returns_rules_dict(self, config_with_rules):
        """Test that load_rules loads custom workflow rules."""
        # Create custom workflow rule
        workflow_dir = config_with_rules.rules_dir / "custom" / "workflow"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "custom-workflow.md").write_text("# Custom Workflow")

        rules, standard_count, custom_count = load_rules(config_with_rules)

        assert "custom-workflow" in rules["custom"]
        assert rules["custom"]["custom-workflow"] == "# Custom Workflow"
        assert standard_count == 0
        assert custom_count == 1

    def test_load_rules_with_mixed_rules_returns_all_rules(self, config_with_rules):
        """Test that load_rules loads both standard and custom rules."""
        # Create standard core rule
        core_dir = config_with_rules.rules_dir / "standard" / "core"
        core_dir.mkdir(parents=True)
        (core_dir / "standard-rule.md").write_text("Standard")

        # Create custom extended rule
        extended_dir = config_with_rules.rules_dir / "custom" / "extended"
        extended_dir.mkdir(parents=True)
        (extended_dir / "custom-rule.md").write_text("Custom")

        rules, standard_count, custom_count = load_rules(config_with_rules)

        assert "standard-rule" in rules["standard"]
        assert "custom-rule" in rules["custom"]
        assert standard_count == 1
        assert custom_count == 1


class TestDiscoverSkills:
    """Test discover_skills function."""

    def test_discover_skills_with_no_extended_rules_returns_empty_list(self, config_with_rules):
        """Test that discover_skills returns empty list when no extended rules exist."""
        skills = discover_skills(config_with_rules)

        assert skills == []

    def test_discover_skills_with_standard_extended_rule_returns_skill(self, config_with_rules):
        """Test that discover_skills finds skills in standard/extended."""
        extended_dir = config_with_rules.rules_dir / "standard" / "extended"
        extended_dir.mkdir(parents=True)
        (extended_dir / "testing-anti-patterns.md").write_text(
            "Prevent common testing anti-patterns.\n\nMore content here."
        )

        skills = discover_skills(config_with_rules)

        assert len(skills) == 1
        assert skills[0].name == "testing-anti-patterns"
        assert skills[0].description == "Prevent common testing anti-patterns."

    def test_discover_skills_extracts_first_non_heading_line_as_description(self, config_with_rules):
        """Test that discover_skills extracts first non-heading line as description."""
        extended_dir = config_with_rules.rules_dir / "standard" / "extended"
        extended_dir.mkdir(parents=True)
        (extended_dir / "backend-api-standards.md").write_text(
            "# API Standards\n\nDesign RESTful APIs.\n\nMore details."
        )

        skills = discover_skills(config_with_rules)

        assert skills[0].description == "Design RESTful APIs."

    def test_discover_skills_with_custom_extended_rules_returns_skills(self, config_with_rules):
        """Test that discover_skills finds custom extended skills."""
        extended_dir = config_with_rules.rules_dir / "custom" / "extended"
        extended_dir.mkdir(parents=True)
        (extended_dir / "custom-skill.md").write_text("Custom skill description")

        skills = discover_skills(config_with_rules)

        assert len(skills) == 1
        assert skills[0].name == "custom-skill"


class TestParseYamlCommands:
    """Test parse_yaml_commands function."""

    def test_parse_yaml_commands_with_empty_file_returns_empty_list(self, config_with_rules):
        """Test that parse_yaml_commands returns empty list for empty config."""
        config_file = config_with_rules.rules_dir / "config.yaml"
        config_file.write_text("")

        commands = parse_yaml_commands(config_with_rules)

        assert commands == []

    def test_parse_yaml_commands_with_simple_command_returns_command(self, config_with_rules):
        """Test that parse_yaml_commands parses a simple command."""
        config_file = config_with_rules.rules_dir / "config.yaml"
        config_file.write_text(
            """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard:
        - rule1
"""
        )

        commands = parse_yaml_commands(config_with_rules)

        assert len(commands) == 1
        assert commands[0].name == "test"
        assert commands[0].description == "Test command"
        assert commands[0].model == "sonnet"
        assert commands[0].inject_skills is False
        assert commands[0].rules == [("standard", "rule1")]

    def test_parse_yaml_commands_with_inject_skills_true_sets_flag(self, config_with_rules):
        """Test that inject_skills: true is parsed correctly."""
        config_file = config_with_rules.rules_dir / "config.yaml"
        config_file.write_text(
            """commands:
  plan:
    description: Plan tasks
    model: haiku
    inject_skills: true
    rules:
      standard:
        - planning
"""
        )

        commands = parse_yaml_commands(config_with_rules)

        assert commands[0].inject_skills is True

    def test_parse_yaml_commands_with_custom_rules_includes_custom_source(self, config_with_rules):
        """Test that custom rules are parsed with correct source."""
        config_file = config_with_rules.rules_dir / "config.yaml"
        config_file.write_text(
            """commands:
  custom_cmd:
    description: Custom command
    rules:
      custom:
        - custom-rule
"""
        )

        commands = parse_yaml_commands(config_with_rules)

        assert commands[0].rules == [("custom", "custom-rule")]

    def test_parse_yaml_commands_with_multiple_commands_returns_all(self, config_with_rules):
        """Test that multiple commands are parsed."""
        config_file = config_with_rules.rules_dir / "config.yaml"
        config_file.write_text(
            "commands:\n"
            "  first:\n"
            "    description: First\n"
            "    rules:\n"
            "      standard:\n"
            "        - rule1\n"
            "  second:\n"
            "    description: Second\n"
            "    rules:\n"
            "      standard:\n"
            "        - rule2\n"
        )

        commands = parse_yaml_commands(config_with_rules)

        assert len(commands) == 2
        assert commands[0].name == "first"
        assert commands[1].name == "second"


class TestBuildCommands:
    """Test build_commands function."""

    def test_build_commands_creates_command_files(self, config_with_rules):
        """Test that build_commands creates command files."""
        # Setup rules
        core_dir = config_with_rules.rules_dir / "standard" / "core"
        core_dir.mkdir(parents=True)
        (core_dir / "test-rule.md").write_text("# Test Rule Content")

        # Setup config
        config_file = config_with_rules.rules_dir / "config.yaml"
        config_file.write_text(
            """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard:
        - test-rule
"""
        )

        rules = {"standard": {"test-rule": "# Test Rule Content"}, "custom": {}}
        skills = []

        count = build_commands(config_with_rules, rules, skills)

        assert count == 1
        command_file = config_with_rules.commands_dir / "test.md"
        assert command_file.exists()
        content = command_file.read_text()
        assert "description: Test command" in content
        assert "model: sonnet" in content
        assert "# Test Rule Content" in content

    def test_build_commands_with_inject_skills_includes_skills_section(self, config_with_rules):
        """Test that build_commands includes skills section when inject_skills is true."""
        # Setup config
        config_file = config_with_rules.rules_dir / "config.yaml"
        config_file.write_text(
            """commands:
  plan:
    description: Plan command
    model: sonnet
    inject_skills: true
    rules:
      standard: []
"""
        )

        rules = {"standard": {}, "custom": {}}
        skills = [Skill("testing-anti-patterns", "Testing patterns")]

        count = build_commands(config_with_rules, rules, skills)

        command_file = config_with_rules.commands_dir / "plan.md"
        content = command_file.read_text()
        assert "## Available Skills" in content
        assert "@testing-anti-patterns" in content


class TestBuildSkills:
    """Test build_skills function."""

    def test_build_skills_creates_skill_directories(self, config_with_rules):
        """Test that build_skills creates SKILL.md files in skill directories."""
        # Setup extended rules
        extended_dir = config_with_rules.rules_dir / "standard" / "extended"
        extended_dir.mkdir(parents=True)
        (extended_dir / "testing-anti-patterns.md").write_text("# Testing Anti-patterns\n\nContent")

        rules = {"standard": {"testing-anti-patterns": "# Testing Anti-patterns\n\nContent"}, "custom": {}}

        count = build_skills(config_with_rules, rules)

        assert count == 1
        skill_file = config_with_rules.skills_dir / "testing-anti-patterns" / "SKILL.md"
        assert skill_file.exists()
        assert skill_file.read_text() == "# Testing Anti-patterns\n\nContent"

    def test_build_skills_with_custom_extended_creates_custom_skills(self, config_with_rules):
        """Test that build_skills creates custom skill files."""
        # Setup custom extended rule
        extended_dir = config_with_rules.rules_dir / "custom" / "extended"
        extended_dir.mkdir(parents=True)
        (extended_dir / "custom-skill.md").write_text("Custom content")

        rules = {"standard": {}, "custom": {"custom-skill": "Custom content"}}

        count = build_skills(config_with_rules, rules)

        assert count == 1
        skill_file = config_with_rules.skills_dir / "custom-skill" / "SKILL.md"
        assert skill_file.exists()
