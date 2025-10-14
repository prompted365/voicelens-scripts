#!/bin/bash
#
# Setup script for automatic documentation concatenation
# Installs Git pre-commit hook and runs initial documentation generation
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up VoiceLens Documentation Auto-Update System${NC}"

# Get the repository root
REPO_ROOT=$(git rev-parse --show-toplevel)
SCRIPTS_DIR="$REPO_ROOT/scripts"
HOOKS_DIR="$REPO_ROOT/.git/hooks"
DOCS_SCRIPT="$SCRIPTS_DIR/concat_docs.py"
HOOK_SCRIPT="$SCRIPTS_DIR/pre-commit-docs"
HOOK_TARGET="$HOOKS_DIR/pre-commit"

echo -e "${BLUE}📂 Repository Root: $REPO_ROOT${NC}"

# Check if we're in a git repository
if [ ! -d "$REPO_ROOT/.git" ]; then
    echo -e "${RED}❌ Not in a git repository!${NC}"
    exit 1
fi

# Create hooks directory if it doesn't exist
mkdir -p "$HOOKS_DIR"

# Check if documentation script exists
if [ ! -f "$DOCS_SCRIPT" ]; then
    echo -e "${RED}❌ Documentation script not found: $DOCS_SCRIPT${NC}"
    exit 1
fi

# Make documentation script executable
chmod +x "$DOCS_SCRIPT"
echo -e "${GREEN}✅ Made documentation script executable${NC}"

# Check if pre-commit hook source exists
if [ ! -f "$HOOK_SCRIPT" ]; then
    echo -e "${RED}❌ Pre-commit hook script not found: $HOOK_SCRIPT${NC}"
    exit 1
fi

# Install the pre-commit hook
if [ -f "$HOOK_TARGET" ]; then
    echo -e "${YELLOW}⚠️  Existing pre-commit hook found${NC}"
    echo -e "${YELLOW}📄 Backing up existing hook to pre-commit.backup${NC}"
    cp "$HOOK_TARGET" "$HOOK_TARGET.backup"
fi

# Copy the hook
cp "$HOOK_SCRIPT" "$HOOK_TARGET"
chmod +x "$HOOK_TARGET"

echo -e "${GREEN}✅ Pre-commit hook installed${NC}"

# Run initial documentation generation
echo -e "${BLUE}📚 Running initial documentation concatenation...${NC}"
if python3 "$DOCS_SCRIPT"; then
    echo -e "${GREEN}✅ Initial documentation generated successfully${NC}"
else
    echo -e "${RED}❌ Failed to generate initial documentation${NC}"
    exit 1
fi

# Check if LLM-DOCS-FULL.md exists and show info
OUTPUT_FILE="$REPO_ROOT/LLM-DOCS-FULL.md"
if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(wc -c < "$OUTPUT_FILE")
    FILE_SIZE_KB=$((FILE_SIZE / 1024))
    echo -e "${GREEN}📄 Generated: LLM-DOCS-FULL.md (${FILE_SIZE_KB} KB)${NC}"
else
    echo -e "${RED}❌ LLM-DOCS-FULL.md was not created${NC}"
fi

echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 What happens now:${NC}"
echo -e "   • ${GREEN}✅${NC} Pre-commit hook is installed"
echo -e "   • ${GREEN}✅${NC} LLM-DOCS-FULL.md will be auto-updated on commits"
echo -e "   • ${GREEN}✅${NC} Only triggers when .md files are changed"
echo -e "   • ${GREEN}✅${NC} Updated file is automatically added to commits"
echo ""
echo -e "${YELLOW}💡 Manual update command:${NC}"
echo -e "   python3 scripts/concat_docs.py"
echo ""
echo -e "${YELLOW}📖 Generated file:${NC}"
echo -e "   LLM-DOCS-FULL.md (complete project documentation)"
