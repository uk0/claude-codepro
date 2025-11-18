"""E2E tests for config merge functionality."""

from __future__ import annotations

import sys
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


def setup_files_module(project_dir: Path, project_root: Path) -> None:
    """Set up files module for testing."""
    # Copy required modules
    lib_dir = project_dir / "scripts" / "lib"
    lib_dir.mkdir(parents=True)

    for module in ["files.py", "ui.py", "utils.py"]:
        src = project_root / "scripts" / "lib" / module
        dst = lib_dir / module
        dst.write_text(src.read_text())


class TestConfigMerge:
    """Test config.yaml merge functionality."""

    def test_preserves_custom_rules(self, temp_project, project_root):
        """Test that custom rules are preserved during merge."""
        setup_files_module(temp_project, project_root)

        # Create existing config with custom rules
        existing_config = """commands:
  plan:
    description: Old description
    model: opus
    inject_skills: true
    rules:
      standard:
        - old-rule-1
        - old-rule-2
      custom:
        - my-custom-rule
        - another-custom-rule
  implement:
    description: Old implement
    model: sonnet
    rules:
      standard:
        - old-implement
      custom:
        - custom-impl
"""

        # Create new config (simulating download from repo)
        new_config = """commands:
  plan:
    description: New description
    model: opus
    inject_skills: true
    rules:
      standard:
        - new-rule-1
        - new-rule-2
        - new-rule-3
      custom: []
  implement:
    description: New implement
    model: sonnet
    rules:
      standard:
        - new-implement-1
        - new-implement-2
      custom: []
"""

        existing_path = temp_project / "existing-config.yaml"
        new_path = temp_project / "new-config.yaml"
        existing_path.write_text(existing_config)
        new_path.write_text(new_config)

        # Run merge
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import files

        result = files.merge_yaml_config(new_path, existing_path)
        assert result is True

        # Verify custom rules were preserved
        merged_content = existing_path.read_text()
        assert "my-custom-rule" in merged_content
        assert "another-custom-rule" in merged_content
        assert "custom-impl" in merged_content

    def test_updates_standard_rules(self, temp_project, project_root):
        """Test that standard rules are updated during merge."""
        setup_files_module(temp_project, project_root)

        # Create existing config
        existing_config = """commands:
  plan:
    description: Old description
    model: opus
    rules:
      standard:
        - old-rule-1
        - old-rule-2
      custom:
        - my-custom-rule
"""

        # Create new config
        new_config = """commands:
  plan:
    description: New description
    model: opus
    rules:
      standard:
        - new-rule-1
        - new-rule-2
        - new-rule-3
      custom: []
"""

        existing_path = temp_project / "existing-config.yaml"
        new_path = temp_project / "new-config.yaml"
        existing_path.write_text(existing_config)
        new_path.write_text(new_config)

        # Run merge
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import files

        files.merge_yaml_config(new_path, existing_path)

        # Verify standard rules were updated
        merged_content = existing_path.read_text()
        assert "new-rule-1" in merged_content
        assert "new-rule-2" in merged_content
        assert "new-rule-3" in merged_content

    def test_removes_old_standard_rules(self, temp_project, project_root):
        """Test that old standard rules are removed during merge."""
        setup_files_module(temp_project, project_root)

        # Create existing config
        existing_config = """commands:
  plan:
    description: Old description
    model: opus
    rules:
      standard:
        - old-rule-1
        - old-rule-2
      custom:
        - my-custom-rule
"""

        # Create new config
        new_config = """commands:
  plan:
    description: New description
    model: opus
    rules:
      standard:
        - new-rule-1
      custom: []
"""

        existing_path = temp_project / "existing-config.yaml"
        new_path = temp_project / "new-config.yaml"
        existing_path.write_text(existing_config)
        new_path.write_text(new_config)

        # Run merge
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import files

        files.merge_yaml_config(new_path, existing_path)

        # Verify old standard rules were removed
        merged_content = existing_path.read_text()
        assert "old-rule-1" not in merged_content
        assert "old-rule-2" not in merged_content

        # But custom rules are preserved
        assert "my-custom-rule" in merged_content

    def test_produces_valid_yaml(self, temp_project, project_root):
        """Test that merged config is valid YAML."""
        setup_files_module(temp_project, project_root)

        # Create configs
        existing_config = """commands:
  plan:
    description: Old description
    model: opus
    rules:
      standard:
        - old-rule
      custom:
        - my-custom-rule
"""

        new_config = """commands:
  plan:
    description: New description
    model: opus
    rules:
      standard:
        - new-rule
      custom: []
"""

        existing_path = temp_project / "existing-config.yaml"
        new_path = temp_project / "new-config.yaml"
        existing_path.write_text(existing_config)
        new_path.write_text(new_config)

        # Run merge
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import files

        files.merge_yaml_config(new_path, existing_path)

        # Verify it's valid YAML
        try:
            import yaml

            with open(existing_path) as f:
                data = yaml.safe_load(f)
            assert data is not None
            assert "commands" in data
            assert "plan" in data["commands"]
        except Exception as e:
            pytest.fail(f"Merged YAML is invalid: {e}")

    def test_handles_multiple_commands(self, temp_project, project_root):
        """Test that merge handles multiple commands correctly."""
        setup_files_module(temp_project, project_root)

        # Create existing config with multiple commands
        existing_config = """commands:
  plan:
    description: Plan desc
    rules:
      standard:
        - old-plan
      custom:
        - custom-plan
  implement:
    description: Implement desc
    rules:
      standard:
        - old-implement
      custom:
        - custom-implement
  verify:
    description: Verify desc
    rules:
      standard:
        - old-verify
      custom:
        - custom-verify
"""

        # Create new config
        new_config = """commands:
  plan:
    description: New plan desc
    rules:
      standard:
        - new-plan
      custom: []
  implement:
    description: New implement desc
    rules:
      standard:
        - new-implement
      custom: []
  verify:
    description: New verify desc
    rules:
      standard:
        - new-verify
      custom: []
"""

        existing_path = temp_project / "existing-config.yaml"
        new_path = temp_project / "new-config.yaml"
        existing_path.write_text(existing_config)
        new_path.write_text(new_config)

        # Run merge
        sys.path.insert(0, str(temp_project / "scripts"))
        from lib import files

        files.merge_yaml_config(new_path, existing_path)

        # Verify all custom rules were preserved
        merged_content = existing_path.read_text()
        assert "custom-plan" in merged_content
        assert "custom-implement" in merged_content
        assert "custom-verify" in merged_content

        # Verify all standard rules were updated
        assert "new-plan" in merged_content
        assert "new-implement" in merged_content
        assert "new-verify" in merged_content
        assert "old-plan" not in merged_content
        assert "old-implement" not in merged_content
        assert "old-verify" not in merged_content
