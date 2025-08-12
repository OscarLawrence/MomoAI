#!/bin/bash
"""
Setup script to make the 'mo' command available globally.

This script sets up the mo command to be accessible from anywhere in the system.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the workspace root (where this script is located)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(dirname "$SCRIPT_DIR")"
MO_SCRIPT="$WORKSPACE_ROOT/mo"

echo -e "${BLUE}🔧 Setting up mo command for MomoAI workspace${NC}"
echo -e "Workspace: ${WORKSPACE_ROOT}"

# Check if mo script exists
if [[ ! -f "$MO_SCRIPT" ]]; then
    echo -e "${RED}❌ mo script not found at: $MO_SCRIPT${NC}"
    exit 1
fi

# Make sure mo script is executable
chmod +x "$MO_SCRIPT"

# Method 1: Add to local bin (recommended for development)
LOCAL_BIN="$HOME/.local/bin"
if [[ ! -d "$LOCAL_BIN" ]]; then
    echo -e "${BLUE}📁 Creating $LOCAL_BIN directory${NC}"
    mkdir -p "$LOCAL_BIN"
fi

# Create symlink
if [[ -L "$LOCAL_BIN/mo" ]]; then
    echo -e "${YELLOW}⚠️  Existing mo symlink found, removing${NC}"
    rm "$LOCAL_BIN/mo"
elif [[ -f "$LOCAL_BIN/mo" ]]; then
    echo -e "${YELLOW}⚠️  Existing mo file found, backing up${NC}"
    mv "$LOCAL_BIN/mo" "$LOCAL_BIN/mo.backup.$(date +%s)"
fi

ln -s "$MO_SCRIPT" "$LOCAL_BIN/mo"
echo -e "${GREEN}✅ Created symlink: $LOCAL_BIN/mo -> $MO_SCRIPT${NC}"

# Check if ~/.local/bin is in PATH
if [[ ":$PATH:" != *":$LOCAL_BIN:"* ]]; then
    echo -e "${YELLOW}⚠️  $LOCAL_BIN is not in your PATH${NC}"
    echo -e "${BLUE}Add this to your shell profile (.bashrc, .zshrc, etc.):${NC}"
    echo -e "export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo
fi

# Method 2: Project-specific alias (alternative)
echo -e "${BLUE}💡 Alternative: Add project alias to your shell profile:${NC}"
echo -e "alias mo='$MO_SCRIPT'"
echo

# Test the command
echo -e "${BLUE}🧪 Testing mo command...${NC}"
if command -v mo >/dev/null 2>&1; then
    echo -e "${GREEN}✅ mo command is available globally${NC}"
    mo --help | head -5
else
    echo -e "${YELLOW}⚠️  mo command not found in PATH${NC}"
    echo -e "You may need to:"
    echo -e "1. Restart your terminal"
    echo -e "2. Add ~/.local/bin to your PATH"
    echo -e "3. Or use the full path: $MO_SCRIPT"
fi

echo
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo -e "${BLUE}Usage examples:${NC}"
echo -e "  mo create idea \"implement new feature\""
echo -e "  mo test module-name"
echo -e "  mo validate system"