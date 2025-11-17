#!/bin/bash

# =============================================================================
# End-to-End Test for Rule Builder Script
# Tests build-rules.sh functionality with standard/custom structure
# =============================================================================

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

# Test configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR=$(mktemp -d)
FAILED_TESTS=0
PASSED_TESTS=0

# Cleanup function
# shellcheck disable=SC2329
cleanup() {
	if [[ -d $TEST_DIR ]]; then
		rm -rf "$TEST_DIR"
	fi
}

trap cleanup EXIT

# Print functions
print_section() {
	echo ""
	echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
	echo -e "${BLUE}  $1${NC}"
	echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
	echo ""
}

print_test() {
	echo -e "${YELLOW}▶ Testing: $1${NC}"
}

print_success() {
	echo -e "${GREEN}✓ $1${NC}"
	((PASSED_TESTS++))
}

print_error() {
	echo -e "${RED}✗ $1${NC}"
	((FAILED_TESTS++))
}

print_info() {
	echo -e "${BLUE}ℹ $1${NC}"
}

# =============================================================================
# Test: Rule Builder with Standard Structure
# =============================================================================

test_build_rules_standard() {
	print_section "Test: Rule Builder with Standard Structure"

	local test_dir="$TEST_DIR/test-standard"
	mkdir -p "$test_dir/.claude/rules/standard/"{core,workflow,extended}
	mkdir -p "$test_dir/.claude/rules/custom/"{core,workflow,extended}
	mkdir -p "$test_dir/scripts"

	# Copy build-rules.sh script
	cp "$PROJECT_ROOT/scripts/build-rules.sh" "$test_dir/scripts/"
	chmod +x "$test_dir/scripts/build-rules.sh"

	# Create test rules
	print_test "Creating test rules in standard structure"

	cat >"$test_dir/.claude/rules/standard/core/test-core.md" <<'EOF'
# Test Core Rule
This is a test core rule.
EOF

	cat >"$test_dir/.claude/rules/standard/workflow/test-workflow.md" <<'EOF'
# Test Workflow Rule
This is a test workflow rule.
EOF

	cat >"$test_dir/.claude/rules/standard/extended/test-skill.md" <<'EOF'
# Test Skill
This is a test skill description.
EOF

	# Create config.yaml
	cat >"$test_dir/.claude/rules/config.yaml" <<'EOF'
commands:
  test:
    description: Test command
    model: sonnet
    inject_skills: true
    rules:
      standard:
        - test-core
        - test-workflow
      custom: []
EOF

	print_success "Test files created"

	# Run build-rules.sh
	print_test "Running build-rules.sh"
	cd "$test_dir"
	if bash scripts/build-rules.sh >build.log 2>&1; then
		print_success "Build completed without errors"
	else
		print_error "Build failed"
		cat build.log
		return 1
	fi

	# Verify rules were loaded
	print_test "Verifying rules were loaded"
	if grep -q "Total: 3 rules" build.log; then
		print_success "Correct number of rules loaded (3)"
	else
		print_error "Wrong number of rules loaded"
		grep "Total:.*rules" build.log
		return 1
	fi

	# Verify skills were discovered
	print_test "Verifying skills were discovered"
	if grep -q "Total: 1 skills" build.log; then
		print_success "Correct number of skills discovered (1)"
	else
		print_error "Wrong number of skills discovered"
		grep "Total:.*skills" build.log
		return 1
	fi

	# Verify command file was created
	print_test "Verifying command file was created"
	if [[ -f "$test_dir/.claude/commands/test.md" ]]; then
		print_success "Command file created: test.md"
	else
		print_error "Command file not created"
		return 1
	fi

	# Verify skill file was created
	print_test "Verifying skill file was created"
	if [[ -f "$test_dir/.claude/skills/test-skill/SKILL.md" ]]; then
		print_success "Skill file created: test-skill/SKILL.md"
	else
		print_error "Skill file not created"
		return 1
	fi

	# Verify command contains rule content
	print_test "Verifying command contains rule content"
	if grep -q "Test Core Rule" "$test_dir/.claude/commands/test.md" &&
		grep -q "Test Workflow Rule" "$test_dir/.claude/commands/test.md"; then
		print_success "Command contains correct rule content"
	else
		print_error "Command missing rule content"
		cat "$test_dir/.claude/commands/test.md"
		return 1
	fi

	print_success "Standard structure test passed"
}

# =============================================================================
# Test: Rule Builder with Custom Rules Override
# =============================================================================

test_build_rules_custom_override() {
	print_section "Test: Rule Builder with Custom Rules Override"

	local test_dir="$TEST_DIR/test-custom"
	mkdir -p "$test_dir/.claude/rules/standard/core"
	mkdir -p "$test_dir/.claude/rules/custom/core"
	mkdir -p "$test_dir/scripts"

	# Copy build-rules.sh script
	cp "$PROJECT_ROOT/scripts/build-rules.sh" "$test_dir/scripts/"
	chmod +x "$test_dir/scripts/build-rules.sh"

	# Create standard rule
	cat >"$test_dir/.claude/rules/standard/core/override-test.md" <<'EOF'
# Standard Version
This is the standard rule.
EOF

	# Create custom rule with same name (should override)
	cat >"$test_dir/.claude/rules/custom/core/override-test.md" <<'EOF'
# Custom Version
This is the custom rule that overrides standard.
EOF

	# Create config.yaml
	cat >"$test_dir/.claude/rules/config.yaml" <<'EOF'
commands:
  test:
    description: Test command
    rules:
      standard:
        - override-test
      custom: []
EOF

	print_test "Running build with custom override"
	cd "$test_dir"
	bash scripts/build-rules.sh >/dev/null 2>&1

	# Verify custom rule overrode standard
	print_test "Verifying custom rule overrides standard"
	if grep -q "Custom Version" "$test_dir/.claude/commands/test.md" &&
		! grep -q "Standard Version" "$test_dir/.claude/commands/test.md"; then
		print_success "Custom rule correctly overrides standard rule"
	else
		print_error "Custom rule did not override standard"
		cat "$test_dir/.claude/commands/test.md"
		return 1
	fi

	print_success "Custom override test passed"
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
	print_section "Rule Builder E2E Tests"

	print_info "Project root: $PROJECT_ROOT"
	print_info "Test directory: $TEST_DIR"
	echo ""

	# Run all tests
	test_build_rules_standard || true
	test_build_rules_custom_override || true

	# Print summary
	print_section "Test Summary"

	echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
	echo -e "${RED}Failed: $FAILED_TESTS${NC}"
	echo ""

	if [[ $FAILED_TESTS -eq 0 ]]; then
		echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		echo -e "${GREEN}  ✓ All rule builder tests passed! 🎉${NC}"
		echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		exit 0
	else
		echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		echo -e "${RED}  ✗ Some rule builder tests failed${NC}"
		echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		exit 1
	fi
}

main "$@"
