#!/usr/bin/env bash
# dy Library Manager - Shelf Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/cdordelly/dyLib/dev/install.sh | bash

SHELF_URL="https://raw.githubusercontent.com/cdordelly/dyLib/dev/toolbar/dy_install_libs.shelf"
SHELF_NAME="dy_install_libs.shelf"
INSTALLED=()
FAILED=()

# Colors
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
GRAY='\033[0;37m'
NC='\033[0m'

echo ""
echo -e "  ${CYAN}dy Install Libs - Shelf Installer${NC}"
echo -e "  ${CYAN}======================================${NC}"
echo ""

# -----------------------------------------------------------------------
# Download shelf file
# -----------------------------------------------------------------------

echo -e "  ${GRAY}Downloading ${SHELF_NAME}...${NC}"

TMP_FILE=$(mktemp)
if ! curl -fsSL "$SHELF_URL" -o "$TMP_FILE"; then
    echo -e "  ${RED}ERROR: Failed to download shelf file.${NC}"
    echo ""
    rm -f "$TMP_FILE"
    exit 1
fi

echo -e "  ${GREEN}Download OK.${NC}"
echo ""

# -----------------------------------------------------------------------
# Find Houdini directories
# -----------------------------------------------------------------------

# Linux: ~/houdiniXX.X  |  macOS: ~/Library/Preferences/houdini/XX.X
# Both also commonly use ~/houdiniXX.X - check both locations

SEARCH_DIRS=("$HOME")

if [[ "$(uname)" == "Darwin" ]]; then
    SEARCH_DIRS+=("$HOME/Library/Preferences/houdini")
fi

HOUDINI_DIRS=()

for SEARCH in "${SEARCH_DIRS[@]}"; do
    if [[ -d "$SEARCH" ]]; then
        while IFS= read -r -d '' DIR; do
            HOUDINI_DIRS+=("$DIR")
        done < <(find "$SEARCH" -maxdepth 1 -type d -name "houdini[0-9]*.[0-9]*" -print0 2>/dev/null)
    fi
done

# macOS pref dir style: ~/Library/Preferences/houdini/XX.X
if [[ "$(uname)" == "Darwin" ]]; then
    PREF_BASE="$HOME/Library/Preferences/houdini"
    if [[ -d "$PREF_BASE" ]]; then
        while IFS= read -r -d '' DIR; do
            HOUDINI_DIRS+=("$DIR")
        done < <(find "$PREF_BASE" -maxdepth 1 -type d -name "[0-9]*.[0-9]*" -print0 2>/dev/null)
    fi
fi

if [[ ${#HOUDINI_DIRS[@]} -eq 0 ]]; then
    echo -e "  ${YELLOW}No Houdini directories found.${NC}"
    echo ""
    echo -e "  ${GRAY}Expected locations:${NC}"
    echo -e "  ${GRAY}  Linux:  ~/houdiniXX.X${NC}"
    echo -e "  ${GRAY}  macOS:  ~/houdiniXX.X  or  ~/Library/Preferences/houdini/XX.X${NC}"
    echo ""
    rm -f "$TMP_FILE"
    exit 0
fi

echo -e "  ${GRAY}Found Houdini directories:${NC}"
for DIR in "${HOUDINI_DIRS[@]}"; do
    echo -e "  ${GRAY}  $(basename "$DIR")${NC}"
done
echo ""

# -----------------------------------------------------------------------
# Deploy to each Houdini directory
# -----------------------------------------------------------------------

for DIR in "${HOUDINI_DIRS[@]}"; do
    TOOLBAR_DIR="$DIR/toolbar"
    DEST_FILE="$TOOLBAR_DIR/$SHELF_NAME"

    mkdir -p "$TOOLBAR_DIR"

    if cp "$TMP_FILE" "$DEST_FILE"; then
        INSTALLED+=("$(basename "$DIR")")
        echo -e "  ${GREEN}[OK]${NC} $(basename "$DIR")/toolbar/$SHELF_NAME"
    else
        FAILED+=("$(basename "$DIR")")
        echo -e "  ${RED}[FAIL]${NC} $(basename "$DIR")"
    fi
done

rm -f "$TMP_FILE"

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------

echo ""
echo -e "  ${CYAN}======================================${NC}"

if [[ ${#INSTALLED[@]} -gt 0 ]]; then
    echo -e "  ${GREEN}Installed to ${#INSTALLED[@]} Houdini version(s): $(IFS=', '; echo "${INSTALLED[*]}")${NC}"
fi
if [[ ${#FAILED[@]} -gt 0 ]]; then
    echo -e "  ${RED}Failed for ${#FAILED[@]} version(s): $(IFS=', '; echo "${FAILED[*]}")${NC}"
fi

echo ""
echo -e "  ${CYAN}Restart Houdini and look for the 'dy Install Libs' shelf tab.${NC}"
echo ""
