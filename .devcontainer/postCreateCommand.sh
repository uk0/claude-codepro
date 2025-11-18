#!/usr/bin/env bash

set -e

# =============================================================================
# Dev Container Post-Create Setup
# Runs automatically after dev container is created
# =============================================================================

echo "=================================================="
echo "Dev Container Post-Create Setup"
echo "=================================================="
echo ""

# Install zsh fzf
echo "Configuring zsh with fzf..."
echo -e "\nsource <(fzf --zsh)" >>~/.zshrc

# Enable dotenv plugin for automatic .env loading
# This will auto-load .env files when you cd into directories
if ! grep -q "plugins=.*dotenv" ~/.zshrc; then
    # Add dotenv to plugins array if not already present
    sed -i 's/plugins=(/plugins=(dotenv /' ~/.zshrc

    # Disable prompt for auto-loading .env (trust dev container environment)
    echo -e "\n# Auto-load .env files without prompting" >>~/.zshrc
    echo 'export ZSH_DOTENV_PROMPT=false' >>~/.zshrc
fi

# Make zsh the default shell
chsh -s $(which zsh)

echo "✓ Shell configuration complete"
echo ""

# =============================================================================
# Run Claude CodePro Installation
# =============================================================================

echo "Starting Claude CodePro installation..."
echo ""

# Check if install script exists
if [[ ! -f "scripts/install.py" ]]; then
    echo "ERROR: scripts/install.py not found"
    echo "Please ensure the repository is properly cloned"
    exit 1
fi

# Run installation in non-interactive mode
# Skip environment setup initially (user can run manually later)
python3 scripts/install.py --non-interactive --local

echo ""
echo "=================================================="
echo "Dev Container Setup Complete!"
echo "=================================================="
