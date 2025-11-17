#!/bin/bash

# =============================================================================
# End-to-End Test for Config Merge Functionality
# Tests that custom rules are preserved during install/update
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
# shellcheck disable=SC2329  # Called via trap on EXIT
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

# shellcheck disable=SC2329
print_success() {
	echo -e "${GREEN}✓ $1${NC}"
	((PASSED_TESTS++))
}

# shellcheck disable=SC2329  # Redefined after sourcing ui.sh to restore counter functionality
print_error() {
	echo -e "${RED}✗ $1${NC}"
	((FAILED_TESTS++))
}

# shellcheck disable=SC2329  # Used indirectly via main function
print_info() {
	echo -e "${BLUE}ℹ $1${NC}"
}

# =============================================================================
# Test: Config Merge with yq
# =============================================================================

test_config_merge_with_yq() {
	print_section "Test: Config Merge with yq"

	local test_dir="$TEST_DIR/test-yq"
	mkdir -p "$test_dir"
	export PROJECT_DIR="$test_dir"
	export TEMP_DIR="$test_dir/tmp"
	mkdir -p "$TEMP_DIR"

	# Source required libraries
	# shellcheck source=/dev/null
	source "$PROJECT_ROOT/scripts/lib/ui.sh"
	# shellcheck source=/dev/null
	source "$PROJECT_ROOT/scripts/lib/utils.sh"

	# Re-define print functions to restore counter functionality
	print_success() {
		echo -e "${GREEN}✓ $1${NC}"
		((PASSED_TESTS++))
	}

	print_error() {
		echo -e "${RED}✗ $1${NC}"
		((FAILED_TESTS++))
	}

	# Extract just the merge_rules_config function from install.sh
	eval "$(sed -n '/^merge_rules_config() {/,/^}/p' "$PROJECT_ROOT/scripts/install.sh")"

	# Create existing config with custom rules
	print_test "Creating existing config with custom rules"
	cat >"$test_dir/existing-config.yaml" <<'EOF'
commands:
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
EOF

	# Create new config (simulating download from repo)
	cat >"$test_dir/new-config.yaml" <<'EOF'
commands:
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
EOF

	print_success "Test configs created"

	# Run merge
	print_test "Running config merge"
	if merge_rules_config "$test_dir/new-config.yaml" "$test_dir/existing-config.yaml" >merge.log 2>&1 && grep -q "preserved custom rules" merge.log; then
		print_success "Merge completed successfully"
	else
		print_error "Merge did not complete"
		cat merge.log
		return 1
	fi

	# Verify standard rules were updated
	print_test "Verifying standard rules were updated"
	if grep -q "new-rule-1" "$test_dir/existing-config.yaml" &&
		grep -q "new-rule-2" "$test_dir/existing-config.yaml" &&
		grep -q "new-rule-3" "$test_dir/existing-config.yaml"; then
		print_success "Standard rules updated correctly"
	else
		print_error "Standard rules not updated"
		cat "$test_dir/existing-config.yaml"
		return 1
	fi

	# Verify old standard rules were removed
	print_test "Verifying old standard rules were removed"
	if ! grep -q "old-rule-1" "$test_dir/existing-config.yaml"; then
		print_success "Old standard rules removed correctly"
	else
		print_error "Old standard rules still present"
		return 1
	fi

	# Verify custom rules were preserved
	print_test "Verifying custom rules were preserved"
	if grep -q "my-custom-rule" "$test_dir/existing-config.yaml" &&
		grep -q "another-custom-rule" "$test_dir/existing-config.yaml" &&
		grep -q "custom-impl" "$test_dir/existing-config.yaml"; then
		print_success "Custom rules preserved correctly"
	else
		print_error "Custom rules were lost!"
		cat "$test_dir/existing-config.yaml"
		return 1
	fi

	# Verify structure is valid YAML
	print_test "Verifying merged config is valid YAML"
	if command -v yq &>/dev/null; then
		if yq eval . "$test_dir/existing-config.yaml" >/dev/null 2>&1; then
			print_success "Merged config is valid YAML"
		else
			print_error "Merged config is invalid YAML"
			cat "$test_dir/existing-config.yaml"
			return 1
		fi
	else
		print_info "yq not available, skipping YAML validation"
	fi

	print_success "Config merge with yq test passed"
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
	print_section "Config Merge E2E Tests"

	print_info "Project root: $PROJECT_ROOT"
	print_info "Test directory: $TEST_DIR"
	echo ""

	# Run all tests
	test_config_merge_with_yq || true

	# Print summary
	print_section "Test Summary"

	echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
	echo -e "${RED}Failed: $FAILED_TESTS${NC}"
	echo ""

	if [[ $FAILED_TESTS -eq 0 ]]; then
		echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		echo -e "${GREEN}  ✓ All config merge tests passed! 🎉${NC}"
		echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		exit 0
	else
		echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		echo -e "${RED}  ✗ Some config merge tests failed${NC}"
		echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		exit 1
	fi
}

main "$@"
