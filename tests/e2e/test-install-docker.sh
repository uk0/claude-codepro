#!/bin/bash

# =============================================================================
# Docker-based E2E Test for Claude CodePro Installation Script
# Tests install.sh in clean container environments
# =============================================================================

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

print_section() {
	echo ""
	echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
	echo -e "${BLUE}  $1${NC}"
	echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
	echo ""
}

print_success() {
	echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
	echo -e "${RED}✗ $1${NC}"
}

print_info() {
	echo -e "${BLUE}ℹ $1${NC}"
}

# =============================================================================
# Docker Test Runner
# =============================================================================

run_docker_test() {
	local platform=$1
	local image=$2

	print_section "Testing on $platform ($image)"

	# Create Dockerfile for this test
	cat >"$PROJECT_ROOT/tests/e2e/Dockerfile.test" <<EOF
FROM $image

# Install required tools for testing
RUN if command -v apt-get &>/dev/null; then \\
        apt-get update && apt-get install -y curl git bash ca-certificates jq && apt-get clean; \\
    elif command -v apk &>/dev/null; then \\
        apk add --no-cache curl git bash ca-certificates jq; \\
    fi

# Create test directory
WORKDIR /test

# Copy project files
COPY . /test/

# Make scripts executable
RUN chmod +x /test/scripts/install.sh
RUN chmod +x /test/tests/e2e/test-install.sh

# Run E2E tests
CMD ["/test/tests/e2e/test-install.sh"]
EOF

	# Build and run test container
	print_info "Building test container for $platform..."
	if ! docker build -f "$PROJECT_ROOT/tests/e2e/Dockerfile.test" -t "claude-codepro-test-$platform" "$PROJECT_ROOT" 2>&1 | grep -E "^(Step|Successfully|ERROR)"; then
		print_error "Docker build failed for $platform"
		return 1
	fi

	print_info "Running tests in container..."
	if docker run --rm "claude-codepro-test-$platform"; then
		print_success "Tests passed on $platform"
		return 0
	else
		print_error "Tests failed on $platform"
		return 1
	fi
}

# =============================================================================
# Main
# =============================================================================

main() {
	print_section "Claude CodePro Docker E2E Tests"

	# Check if Docker is available
	if ! command -v docker &>/dev/null; then
		print_error "Docker is not installed. Please install Docker to run these tests."
		exit 1
	fi

	print_info "Project root: $PROJECT_ROOT"
	echo ""

	# Test on different platforms
	local failed=0

	# Ubuntu (most common Linux distribution)
	if run_docker_test "ubuntu" "ubuntu:22.04"; then
		:
	else
		((failed++))
	fi

	# Cleanup
	rm -f "$PROJECT_ROOT/tests/e2e/Dockerfile.test"
	docker image prune -f &>/dev/null || true

	# Summary
	print_section "Docker Test Summary"

	if [[ $failed -eq 0 ]]; then
		echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		echo -e "${GREEN}  ✓ All Docker tests passed! 🎉${NC}"
		echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		exit 0
	else
		echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		echo -e "${RED}  ✗ $failed platform(s) failed${NC}"
		echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
		exit 1
	fi
}

main "$@"
