"""E2E tests for build.py script."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_project():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir)
        yield project_dir


@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def setup_test_rules(test_dir: Path, project_root: Path) -> None:
    """Set up test rule structure."""
    # Create directory structure
    rules_dir = test_dir / ".claude" / "rules"
    rules_dir.mkdir(parents=True)

    # Copy build.py script
    build_script = project_root / ".claude" / "rules" / "build.py"
    (rules_dir / "build.py").write_text(build_script.read_text())
    (rules_dir / "build.py").chmod(0o755)


def run_build(project_dir: Path) -> subprocess.CompletedProcess:
    """Run build.py script."""
    return subprocess.run(
        ["python3", ".claude/rules/build.py"],
        cwd=project_dir,
        capture_output=True,
        text=True,
        check=False,
    )


class TestStandardStructure:
    """Test build with standard rule structure."""

    def test_loads_standard_rules(self, temp_project, project_root):
        """Test that standard rules are loaded correctly."""
        setup_test_rules(temp_project, project_root)

        # Create standard rules
        core_dir = temp_project / ".claude" / "rules" / "standard" / "core"
        core_dir.mkdir(parents=True)
        (core_dir / "test-rule-1.md").write_text("# Test Rule 1\nContent 1")
        (core_dir / "test-rule-2.md").write_text("# Test Rule 2\nContent 2")

        workflow_dir = temp_project / ".claude" / "rules" / "standard" / "workflow"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "test-workflow.md").write_text("# Test Workflow\nWorkflow content")

        # Create config.yaml
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard:
        - test-rule-1
        - test-workflow
      custom: []
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0, f"Build failed: {result.stderr}"
        assert "test-rule-1.md" in result.stderr
        assert "test-workflow.md" in result.stderr

    def test_creates_command_files(self, temp_project, project_root):
        """Test that command files are created."""
        setup_test_rules(temp_project, project_root)

        # Create minimal standard rule
        core_dir = temp_project / ".claude" / "rules" / "standard" / "core"
        core_dir.mkdir(parents=True)
        (core_dir / "test-rule.md").write_text("# Test Rule\nContent")

        # Create config.yaml
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard:
        - test-rule
      custom: []
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0

        # Verify command file created
        command_file = temp_project / ".claude" / "commands" / "test.md"
        assert command_file.exists()

        content = command_file.read_text()
        assert "description: Test command" in content
        assert "model: sonnet" in content
        assert "Test Rule" in content

    def test_discovers_skills(self, temp_project, project_root):
        """Test that skills are discovered from extended directory."""
        setup_test_rules(temp_project, project_root)

        # Create skill
        extended_dir = temp_project / ".claude" / "rules" / "standard" / "extended"
        extended_dir.mkdir(parents=True)
        (extended_dir / "test-skill.md").write_text("Test skill description\n\nSkill content")

        # Create config.yaml
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard: []
      custom: []
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0
        assert "@test-skill" in result.stderr

    def test_creates_skill_files(self, temp_project, project_root):
        """Test that skill files are created."""
        setup_test_rules(temp_project, project_root)

        # Create skill
        extended_dir = temp_project / ".claude" / "rules" / "standard" / "extended"
        extended_dir.mkdir(parents=True)
        skill_content = "Test skill description\n\nSkill content here"
        (extended_dir / "test-skill.md").write_text(skill_content)

        # Create config.yaml
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard: []
      custom: []
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0

        # Verify skill file created
        skill_file = temp_project / ".claude" / "skills" / "test-skill" / "SKILL.md"
        assert skill_file.exists()
        assert "Test skill description" in skill_file.read_text()

    def test_injects_skills_when_enabled(self, temp_project, project_root):
        """Test that skills are injected when inject_skills is true."""
        setup_test_rules(temp_project, project_root)

        # Create skill
        extended_dir = temp_project / ".claude" / "rules" / "standard" / "extended"
        extended_dir.mkdir(parents=True)
        (extended_dir / "backend-test.md").write_text("Backend test skill")
        (extended_dir / "frontend-test.md").write_text("Frontend test skill")

        # Create minimal rule
        core_dir = temp_project / ".claude" / "rules" / "standard" / "core"
        core_dir.mkdir(parents=True)
        (core_dir / "test-rule.md").write_text("# Test Rule")

        # Create config.yaml with inject_skills: true
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: true
    rules:
      standard:
        - test-rule
      custom: []
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0

        # Verify skills section in command file
        command_file = temp_project / ".claude" / "commands" / "test.md"
        content = command_file.read_text()
        assert "## Available Skills" in content
        assert "@backend-test" in content
        assert "@frontend-test" in content


class TestCustomRules:
    """Test build with custom rules."""

    def test_uses_custom_rules_when_selected(self, temp_project, project_root):
        """Test that custom rules are used when explicitly selected."""
        setup_test_rules(temp_project, project_root)

        # Create standard and custom versions
        standard_dir = temp_project / ".claude" / "rules" / "standard" / "core"
        standard_dir.mkdir(parents=True)
        (standard_dir / "test-rule.md").write_text("# Standard Version\nStandard content")

        custom_dir = temp_project / ".claude" / "rules" / "custom" / "core"
        custom_dir.mkdir(parents=True)
        (custom_dir / "test-rule.md").write_text("# Custom Version\nCustom content")

        # Create config selecting custom rule
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard: []
      custom:
        - test-rule
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0

        # Verify custom version is used
        command_file = temp_project / ".claude" / "commands" / "test.md"
        content = command_file.read_text()
        assert "Custom Version" in content
        assert "Standard Version" not in content

    def test_includes_both_standard_and_custom(self, temp_project, project_root):
        """Test that both standard and custom rules can be included."""
        setup_test_rules(temp_project, project_root)

        # Create standard and custom rules with same name
        standard_dir = temp_project / ".claude" / "rules" / "standard" / "core"
        standard_dir.mkdir(parents=True)
        (standard_dir / "mcp-tools.md").write_text("# Standard MCP\nStandard content")

        custom_dir = temp_project / ".claude" / "rules" / "custom" / "core"
        custom_dir.mkdir(parents=True)
        (custom_dir / "mcp-tools.md").write_text("# Custom MCP\nCustom content")

        # Create config selecting both
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard:
        - mcp-tools
      custom:
        - mcp-tools
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0

        # Verify both versions are included
        command_file = temp_project / ".claude" / "commands" / "test.md"
        content = command_file.read_text()
        assert "Standard MCP" in content
        assert "Custom MCP" in content
        # Both standard and custom content should be present
        assert content.count("Standard content") == 1
        assert content.count("Custom content") == 1


class TestBuildOutput:
    """Test build script output and error handling."""

    def test_warns_on_missing_rule(self, temp_project, project_root):
        """Test that build warns when rule is not found."""
        setup_test_rules(temp_project, project_root)

        # Create config referencing non-existent rule
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard:
        - nonexistent-rule
      custom: []
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0
        assert "nonexistent-rule" in result.stderr
        assert "not found" in result.stderr.lower()

    def test_cleans_old_commands(self, temp_project, project_root):
        """Test that old command files are removed."""
        setup_test_rules(temp_project, project_root)

        # Create old command file
        commands_dir = temp_project / ".claude" / "commands"
        commands_dir.mkdir(parents=True)
        old_command = commands_dir / "old-command.md"
        old_command.write_text("Old command content")

        # Create minimal config
        config = """commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: false
    rules:
      standard: []
      custom: []
"""
        (temp_project / ".claude" / "rules" / "config.yaml").write_text(config)

        result = run_build(temp_project)
        assert result.returncode == 0

        # Old command should be removed
        assert not old_command.exists()
        # New command should exist
        assert (commands_dir / "test.md").exists()
