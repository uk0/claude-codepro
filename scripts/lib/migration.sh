#!/bin/bash
# =============================================================================
# Migration Functions - Handle upgrades from older versions
# =============================================================================

# Check if migration is needed
# Returns: 0 if migration needed, 1 otherwise
needs_migration() {
	local config_file="$PROJECT_DIR/.claude/rules/config.yaml"

	# If config.yaml doesn't exist, no migration needed
	[[ ! -f $config_file ]] && return 1

	# Check if config.yaml has new format (standard: or custom:)
	if grep -q "standard:" "$config_file" || grep -q "custom:" "$config_file"; then
		return 1 # Already migrated
	fi

	return 0 # Migration needed
}

# Run migration - backup old rules and wipe for fresh install
run_migration() {
	if ! needs_migration; then
		return 0
	fi

	local rules_dir="$PROJECT_DIR/.claude/rules"

	print_section "Migration Required"

	echo "We detected an older version of the rules configuration."
	echo "To ensure compatibility, we need to reinstall the rules folder."
	echo ""
	print_warning "Your existing rules will be backed up before deletion."
	echo ""
	echo "What will happen:"
	echo "  1. Create backup at .claude/rules.backup.<timestamp>"
	echo "  2. Delete current .claude/rules folder"
	echo "  3. Fresh rules will be downloaded"
	echo ""

	# Check if stdin is a terminal (interactive) or piped (non-interactive)
	if [ -t 0 ]; then
		read -r -p "Continue with migration? (Y/n): " -n 1 </dev/tty
	else
		read -r -p "Continue with migration? (Y/n): " -n 1
	fi
	echo ""
	echo ""

	# Default to Y
	REPLY=${REPLY:-Y}

	if [[ ! $REPLY =~ ^[Yy]$ ]]; then
		print_error "Migration cancelled."
		echo ""
		echo "To migrate manually:"
		echo "  1. Backup your .claude/rules folder"
		echo "  2. Delete .claude/rules"
		echo "  3. Re-run installation"
		exit 1
	fi

	# Create backup
	local timestamp
	timestamp=$(date +%s)
	local backup_dir="$PROJECT_DIR/.claude/rules.backup.$timestamp"
	print_status "Creating backup at $(basename "$backup_dir")..."
	cp -r "$rules_dir" "$backup_dir"
	print_success "Backup created at: $backup_dir"

	# Delete old rules folder
	print_status "Removing old rules folder..."
	rm -rf "$rules_dir"
	print_success "Old rules removed"

	echo ""
	print_success "Migration complete! Fresh rules will be installed."
	echo ""
}
