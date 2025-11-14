#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Get workspace root dynamically
WORKSPACE_ROOT="${containerWorkspaceFolder:-$(pwd)}"
if [[ -d "$WORKSPACE_ROOT" ]]; then
	cd "$WORKSPACE_ROOT" || exit 1
fi

# Find THE most recently modified file (excluding cache/build dirs)
if [[ "$OSTYPE" == "darwin"* ]]; then
	# macOS version
	files=$(find . -type f -not -path '*/.ruff_cache/*' -not -path '*/__pycache__/*' -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/.git/*' -exec stat -f '%m %N' {} \; 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
else
	# Linux version
	files=$(find . -type f -not -path '*/.ruff_cache/*' -not -path '*/__pycache__/*' -not -path '*/node_modules/*' -not -path '*/.venv/*' -not -path '*/dist/*' -not -path '*/build/*' -not -path '*/.git/*' -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)
fi

# Exit if no files found, not Python, or test files
[[ -z $files ]] && exit 0
[[ $files != *.py ]] && exit 0
[[ $files == *test* || $files == *spec* ]] && exit 0

# Get absolute path
file_abs_path=$(realpath "$files")

# Define tools with global paths (installed via uv tool install)
declare -A TOOLS=(
	[ruff]="$(command -v ruff 2>/dev/null || true)"
	[basedpyright]="$(command -v basedpyright 2>/dev/null || true)"
	[mypy]="$(command -v mypy 2>/dev/null || true)"
)

# Exit if no tools found
[[ -z ${TOOLS[ruff]} && -z ${TOOLS[basedpyright]} && -z ${TOOLS[mypy]} ]] && exit 0

# Auto-format before checks
if [[ -x ${TOOLS[ruff]} ]]; then
	${TOOLS[ruff]} check --select I,RUF022 --fix "$files" >/dev/null 2>&1 || true
	${TOOLS[ruff]} format "$files" >/dev/null 2>&1 || true
fi

# Run tool check and store results
run_check() {
	local tool=$1
	local bin=${TOOLS[$tool]}
	[[ ! -x $bin ]] && return 1

	case $tool in
	ruff)
		output=$($bin check "$files" 2>&1 || true)
		[[ -n $output && $output != *"All checks passed"* ]]
		;;
	basedpyright)
		output=$($bin --outputjson "$file_abs_path" 2>&1 || true)
		echo "$output" | grep -qE '"errorCount":\s*[1-9]|" error"'
		;;
	mypy)
		output=$($bin "$file_abs_path" 2>&1 || true)
		echo "$output" | grep -qE 'error:' && [[ $output != *"Success:"* ]]
		;;
	esac
}

# Display tool results
display_result() {
	local tool=$1
	local emoji icon error_count

	case $tool in
	ruff)
		emoji="🔧"
		icon="Ruff"
		error_count=$(echo "$output" | grep -c "^F[0-9]\|^E[0-9]\|^W[0-9]" 2>/dev/null || echo "0")
		[[ $error_count -eq 1 ]] && plural="issue" || plural="issues"
		echo "" >&2
		echo "$emoji $icon: $error_count $plural" >&2
		echo "───────────────────────────────────────" >&2
		echo "$output" | grep -E "^(F[0-9]|E[0-9]|W[0-9])" | while IFS= read -r line; do
			code=$(echo "$line" | grep -oE "^[FEW][0-9]+")
			msg=$(echo "$line" | sed -E "s/^[FEW][0-9]+\s+(\[\*\]\s+)?//")
			echo "  $code: $msg" >&2
		done
		;;
	basedpyright)
		emoji="🐍"
		icon="BasedPyright"
		error_count=$(echo "$output" | grep -oE '"errorCount":[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -1)
		[[ -z $error_count ]] && error_count=0
		[[ $error_count -eq 1 ]] && plural="issue" || plural="issues"
		echo "" >&2
		echo "$emoji $icon: $error_count $plural" >&2
		echo "───────────────────────────────────────" >&2
		echo "$output" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for diag in data.get('generalDiagnostics', []):
    file = diag.get('file', '').split('/')[-1]
    line = diag.get('range', {}).get('start', {}).get('line', 0)
    msg = diag.get('message', '').split('\n')[0]
    print(f'  {file}:{line} - {msg}')
" >&2
		;;
	mypy)
		emoji="🔍"
		icon="Mypy"
		error_count=$(echo "$output" | grep -c "error:" 2>/dev/null || echo "0")
		[[ $error_count -eq 1 ]] && plural="issue" || plural="issues"
		echo "" >&2
		echo "$emoji $icon: $error_count $plural" >&2
		echo "───────────────────────────────────────" >&2
		echo "$output" | grep "error:" >&2
		;;
	esac

	echo "" >&2
}

# Run all checks
has_issues=false
declare -A results
for tool in ruff basedpyright mypy; do
	if run_check "$tool"; then
		has_issues=true
		results[$tool]="$output"
	fi
done

# Display results
if [[ $has_issues == true ]]; then
	echo "" >&2
	echo -e "${RED}🛑 Python Issues found in: $files${NC}" >&2
	echo "" >&2

	for tool in ruff basedpyright mypy; do
		if [[ -n ${results[$tool]} ]]; then
			output="${results[$tool]}"
			display_result "$tool"
		fi
	done

	echo -e "${RED}Fix Python issues above before continuing${NC}" >&2
	exit 2
else
	echo "" >&2
	echo -e "${GREEN}✅ Python: All checks passed${NC}" >&2
	exit 2
fi
