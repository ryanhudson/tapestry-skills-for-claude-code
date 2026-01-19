#!/bin/bash

# Tapestry Skills for Claude Code - Installation Script
# This script installs UV, syncs dependencies, and links skills to Claude

set -e

SKILLS_DIR="$HOME/.claude/skills"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Tapestry Skills for Claude Code - Installer"
echo "============================================"
echo ""

# Step 1: Check for UV (required)
echo "Step 1: Checking for UV..."
if ! command -v uv &> /dev/null; then
    echo "UV is required but not installed."
    echo ""
    echo "Install UV with one of:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  brew install uv"
    echo "  pipx install uv"
    echo ""
    read -p "Install UV now? (y/n) " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing UV..."
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # Source shell config to get uv in PATH
        export PATH="$HOME/.local/bin:$PATH"

        if ! command -v uv &> /dev/null; then
            echo ""
            echo "ERROR: UV installed but not in PATH."
            echo "Please restart your terminal and run this script again."
            exit 1
        fi
        echo "UV installed successfully!"
    else
        echo "Cannot proceed without UV."
        exit 1
    fi
else
    echo "UV found: $(uv --version)"
fi

echo ""

# Step 2: Verify Python version
echo "Step 2: Checking Python version..."
PYTHON_VERSION=$(uv run python --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$MAJOR" -lt 3 ] || { [ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]; }; then
    echo "ERROR: Python 3.10+ required (found $PYTHON_VERSION)"
    echo "UV will handle Python installation, but you may need to configure it."
    exit 1
fi

echo "Python: $PYTHON_VERSION"
echo ""

# Step 3: Install/sync dependencies
echo "Step 3: Installing dependencies..."
cd "$SCRIPT_DIR"
uv sync

echo "Dependencies installed"
echo ""

# Step 4: Verify utilities work
echo "Step 4: Verifying installation..."
if uv run tapestry-validate-url "https://example.com" > /dev/null 2>&1; then
    echo "tapestry-validate-url: OK"
else
    echo "ERROR: tapestry-validate-url failed"
    exit 1
fi

if uv run tapestry-sanitize-filename "Test: File/Name" > /dev/null 2>&1; then
    echo "tapestry-sanitize-filename: OK"
else
    echo "ERROR: tapestry-sanitize-filename failed"
    exit 1
fi

echo ""

# Step 5: Create skills directory and symlink skills
echo "Step 5: Installing skills to Claude..."
mkdir -p "$SKILLS_DIR"

SKILLS=(tapestry youtube-transcript article-extractor ship-learn-next)

for skill in "${SKILLS[@]}"; do
    if [ -e "$SKILLS_DIR/$skill" ]; then
        echo "Skill '$skill' already exists"
        read -p "  Overwrite? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "  Skipped $skill"
            continue
        fi
        rm -rf "$SKILLS_DIR/$skill"
    fi

    # Symlink to source directory (so uv run works from project root)
    ln -sfn "$SCRIPT_DIR/skills/$skill" "$SKILLS_DIR/$skill"
    echo "Installed: $skill"
done

echo ""

# Step 6: Create .tapestry-root marker for skills to find project
echo "Step 6: Creating project marker..."
touch "$SCRIPT_DIR/.tapestry-root"
echo "Project marker created"

echo ""
echo "============================================"
echo "Installation complete!"
echo ""
echo "Skills installed to: $SKILLS_DIR"
echo "Project root: $SCRIPT_DIR"
echo ""
echo "Available skills:"
echo "  - tapestry: Unified workflow (extract + plan)"
echo "  - youtube-transcript: Download YouTube transcripts"
echo "  - article-extractor: Extract clean article content"
echo "  - ship-learn-next: Turn content into action plans"
echo ""
echo "Test the installation:"
echo "  cd $SCRIPT_DIR"
echo "  uv run tapestry-validate-url https://example.com"
echo "  uv run tapestry-sanitize-filename 'My: Test/File'"
echo ""
echo "Usage:"
echo "  Open Claude Code and start using the skills!"
echo "  Quick start: 'tapestry [URL]'"
echo ""
