#!/bin/bash

# =============================================================================
# End-to-End Test for Migration Script
# Tests migration detection and backup/wipe functionality
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

# shellcheck disable=SC2329
print_success() {
	echo -e "${GREEN}✓ $1${NC}"
	((PASSED_TESTS++))
}

# shellcheck disable=SC2329
print_error() {
	echo -e "${RED}✗ $1${NC}"
	((FAILED_TESTS++))
}

print_info() {
	echo -e "${BLUE}ℹ $1${NC}"
}

# Source migration functions
source_migration() {
	local test_dir=$1
	export PROJECT_DIR="$test_dir"
	export TEMP_DIR="$test_dir/tmp"
	mkdir -p "$TEMP_DIR"

	# Source the libraries
	# shellcheck source=/dev/null
	source "$PROJECT_ROOT/scripts/lib/ui.sh"
	# shellcheck source=/dev/null
	source "$PROJECT_ROOT/scripts/lib/migration.sh"

	# Re-define our test print functions to restore counter functionality
	# (ui.sh overwrites them with non-counting versions)
	print_success() {
		echo -e "${GREEN}✓ $1${NC}"
		((PASSED_TESTS++))
	}

	print_error() {
		echo -e "${RED}✗ $1${NC}"
		((FAILED_TESTS++))
	}
}

# =============================================================================
# Test: Migration Detection
# =============================================================================

test_migration_detection() {
	print_section "Test: Migration Detection"

	# Test 1: Old config needs migration
	print_test "Old config format should be detected"
	local test_dir="$TEST_DIR/test-old-format"
	mkdir -p "$test_dir/.claude/rules"

	cat >"$test_dir/.claude/rules/config.yaml" <<'EOF'
commands:
  plan:
    description: Create plans
    rules:
      - plan
      - git-operations
EOF

	source_migration "$test_dir"

	if needs_migration; then
		print_success "Old format correctly detected as needing migration"
	else
		print_error "Old format should need migration"
		return 1
	fi

	# Test 2: New config with "standard:" doesn't need migration
	print_test "New config with standard: should NOT need migration"
	test_dir="$TEST_DIR/test-new-standard"
	mkdir -p "$test_dir/.claude/rules"

	cat >"$test_dir/.claude/rules/config.yaml" <<'EOF'
commands:
  plan:
    description: Create plans
    rules:
      standard:
        - plan
      custom: []
EOF

	source_migration "$test_dir"

	if ! needs_migration; then
		print_success "New format (standard:) correctly detected as NOT needing migration"
	else
		print_error "New format should NOT need migration"
		return 1
	fi

	# Test 3: New config with "custom:" doesn't need migration
	print_test "New config with custom: should NOT need migration"
	test_dir="$TEST_DIR/test-new-custom"
	mkdir -p "$test_dir/.claude/rules"

	cat >"$test_dir/.claude/rules/config.yaml" <<'EOF'
commands:
  plan:
    description: Create plans
    rules:
      custom:
        - my-rule
EOF

	source_migration "$test_dir"

	if ! needs_migration; then
		print_success "New format (custom:) correctly detected as NOT needing migration"
	else
		print_error "New format should NOT need migration"
		return 1
	fi

	# Test 4: No config.yaml doesn't need migration
	print_test "Missing config.yaml should NOT need migration"
	test_dir="$TEST_DIR/test-no-config"
	mkdir -p "$test_dir/.claude/rules"

	source_migration "$test_dir"

	if ! needs_migration; then
		print_success "Missing config correctly detected as NOT needing migration"
	else
		print_error "Missing config should NOT need migration"
		return 1
	fi

	print_success "All migration detection tests passed"
}

# =============================================================================
# Test: Migration Backup and Wipe (Non-Interactive)
# =============================================================================

test_migration_backup_wipe() {
	print_section "Test: Migration Backup and Wipe"

	local test_dir="$TEST_DIR/test-backup-wipe"
	mkdir -p "$test_dir/.claude/rules"
	cd "$test_dir"

	# Create old-style config and some test files
	print_test "Creating old config and test files"
	cat >"$test_dir/.claude/rules/config.yaml" <<'EOF'
commands:
  plan:
    rules:
      - plan
EOF

	mkdir -p "$test_dir/.claude/rules/core"
	echo "test content" >"$test_dir/.claude/rules/core/test-rule.md"
	echo "test content" >"$test_dir/.claude/rules/old-file.txt"

	print_success "Test files created"

	# Source migration and run it (simulating non-interactive mode)
	source_migration "$test_dir"

	# Override the interactive prompt by providing Y input
	print_test "Running migration with auto-accept"
	if printf "Y\n" | run_migration >migration.log 2>&1 && grep -q "Migration complete" migration.log; then
		print_success "Migration executed successfully"
	else
		print_error "Migration did not complete successfully"
		cat migration.log
		return 1
	fi

	# Verify backup was created
	print_test "Verifying backup was created"
	local backup_dir
	backup_dir=$(find "$test_dir/.claude" -maxdepth 1 -type d -name "rules.backup.*" 2>/dev/null | head -1)
	if [[ -d $backup_dir ]]; then
		print_success "Backup directory created: $(basename "$backup_dir")"
	else
		print_error "Backup directory was not created"
		return 1
	fi

	# Verify backup contains original files
	print_test "Verifying backup contains original files"
	if [[ -f "$backup_dir/config.yaml" ]] && [[ -f "$backup_dir/core/test-rule.md" ]]; then
		print_success "Backup contains original files"
	else
		print_error "Backup is missing original files"
		return 1
	fi

	# Verify old rules folder was deleted
	print_test "Verifying old rules folder was deleted"
	if [[ ! -d "$test_dir/.claude/rules" ]]; then
		print_success "Old rules folder successfully deleted"
	else
		print_error "Old rules folder still exists"
		return 1
	fi

	print_success "Backup and wipe test passed"
}

# =============================================================================
# Main Test Runner
# =============================================================================

main() {
	print_section "Migration Script E2E Tests"

	print_info "Project root: $PROJECT_ROOT"
	print_info "Test directory: $TEST_DIR"
	echo ""

	# Run all tests
	test_migration_detection || true
	test_migration_backup_wipe || true

	# Print summary
	print_section "Test Summary"

	echo -e "${GREEN}Passed: $PASSED_TESTS${NC}"
	echo -e "${RED}Failed: $FAILED_TESTS${NC}"
	echo ""

	if [[ $FAILED_TESTS -eq 0 ]]; then
		echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		echo -e "${GREEN}  ✓ All migration tests passed! 🎉${NC}"
		echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		exit 0
	else
		echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		echo -e "${RED}  ✗ Some migration tests failed${NC}"
		echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		exit 1
	fi
}

main "$@"
