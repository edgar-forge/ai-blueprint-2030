#!/bin/bash
# =============================================================================
# Personal Palantir — One-Click Install Script
# =============================================================================
# Obsidian + Claude MCP + Nightly Synapse + Backup/Sync automation
#
# Usage:
#   chmod +x setup.sh && ./setup.sh
#
# What this does:
#   1. Copies MCP server (Python) to ~/obsidian-mcp-server/
#   2. Copies Nightly Synapse (Node.js) to <vault>/scripts/nightly-synapse/
#   3. Copies backup/sync scripts to ~/ObsidianBackup/
#   4. Creates ~/.claude/.mcp.json
#   5. Creates macOS LaunchAgents for automation
#   6. Runs first indexing
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
info()    { echo -e "${BLUE}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[OK]${NC}    $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "${RED}[ERROR]${NC} $1"; }
step()    { echo -e "\n${BOLD}==> Step $1: $2${NC}"; }

die() {
    error "$1"
    exit 1
}

# ---------------------------------------------------------------------------
# Resolve script directory (where the repo source files live)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_MCP_DIR="${SCRIPT_DIR}/obsidian-mcp-server"
REPO_SYNAPSE_DIR="${SCRIPT_DIR}/nightly-synapse"
REPO_BACKUP_DIR="${SCRIPT_DIR}/backup"

HOME_DIR="$HOME"

# ---------------------------------------------------------------------------
# Step 0: Interactive inputs
# ---------------------------------------------------------------------------
step "0" "Gathering configuration"

# Vault path
read -r -p "Obsidian Vault path [${HOME_DIR}/Documents/Obsidian Vault]: " INPUT_VAULT
VAULT_PATH="${INPUT_VAULT:-${HOME_DIR}/Documents/Obsidian Vault}"

# Normalize: expand ~ if user typed it
VAULT_PATH="${VAULT_PATH/#\~/$HOME_DIR}"

if [ ! -d "$VAULT_PATH" ]; then
    warn "Vault directory does not exist: ${VAULT_PATH}"
    read -r -p "Create it? (y/N): " CREATE_VAULT
    if [[ "$CREATE_VAULT" =~ ^[Yy]$ ]]; then
        mkdir -p "$VAULT_PATH"
        success "Created vault directory"
    else
        die "Vault directory is required. Aborting."
    fi
fi

# Ground Truth file path (relative to vault, used by classifier.js)
echo ""
echo "The classifier needs a 'Ground Truth' file — your note classification rules."
echo "This is a relative path inside your vault."
echo "Example: 2. Area of Responsibility/AI 설정/AI_세컨드브레인_Ground_Truth.md"
read -r -p "Ground Truth relative path: " GROUND_TRUTH_REL

if [ -z "$GROUND_TRUTH_REL" ]; then
    warn "No Ground Truth path provided. classifier.js will use an empty string."
    warn "You can edit it later in <vault>/scripts/nightly-synapse/classifier.js"
fi

# Verify the file exists (non-blocking warning)
if [ -n "$GROUND_TRUTH_REL" ] && [ ! -f "${VAULT_PATH}/${GROUND_TRUTH_REL}" ]; then
    warn "Ground Truth file not found at: ${VAULT_PATH}/${GROUND_TRUTH_REL}"
    warn "Continuing anyway — you can create it later."
fi

# ---------------------------------------------------------------------------
# Step 1: Check prerequisites
# ---------------------------------------------------------------------------
step "1" "Checking prerequisites"

MISSING=()

check_cmd() {
    if command -v "$1" &>/dev/null; then
        success "$1 found: $(command -v "$1")"
    else
        error "$1 not found"
        MISSING+=("$1")
    fi
}

check_cmd python3
check_cmd node
check_cmd npm
check_cmd git

# Claude CLI is optional but recommended
if command -v claude &>/dev/null; then
    success "claude CLI found: $(command -v claude)"
else
    warn "claude CLI not found — Nightly Synapse and MCP features require it."
    warn "Install: https://docs.anthropic.com/en/docs/claude-code"
fi

if [ ${#MISSING[@]} -gt 0 ]; then
    die "Missing required tools: ${MISSING[*]}. Install them and re-run."
fi

# Check Python version (need 3.9+)
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    die "Python 3.9+ required. Found: ${PY_VERSION}"
fi
success "Python version: ${PY_VERSION}"

# Check Node version (need 18+)
NODE_VERSION=$(node -v | sed 's/v//' | cut -d. -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    die "Node.js 18+ required. Found: $(node -v)"
fi
success "Node version: $(node -v)"

# ---------------------------------------------------------------------------
# Step 2: Install MCP server (Python)
# ---------------------------------------------------------------------------
step "2" "Setting up MCP server at ~/obsidian-mcp-server/"

MCP_DEST="${HOME_DIR}/obsidian-mcp-server"
mkdir -p "$MCP_DEST"

# Copy Python files from repo, replacing {VAULT_PATH} placeholder
if [ ! -d "$REPO_MCP_DIR" ]; then
    die "Source directory not found: ${REPO_MCP_DIR}"
fi

for pyfile in "$REPO_MCP_DIR"/*.py; do
    [ -f "$pyfile" ] || continue
    BASENAME=$(basename "$pyfile")
    sed "s|{여기에_본인_볼트_절대경로}|${VAULT_PATH}|g" "$pyfile" > "${MCP_DEST}/${BASENAME}"
    success "Copied ${BASENAME}"
done

# Create Python venv
info "Creating Python virtual environment..."
if [ ! -d "${MCP_DEST}/venv" ]; then
    python3 -m venv "${MCP_DEST}/venv"
    success "Virtual environment created"
else
    warn "Virtual environment already exists — skipping creation"
fi

# Install dependencies
info "Installing Python dependencies (this may take a few minutes)..."
"${MCP_DEST}/venv/bin/pip" install --upgrade pip --quiet 2>/dev/null
"${MCP_DEST}/venv/bin/pip" install sentence-transformers lancedb "mcp[cli]" --quiet 2>/dev/null
success "Python dependencies installed"

# ---------------------------------------------------------------------------
# Step 3: Install Nightly Synapse (Node.js)
# ---------------------------------------------------------------------------
step "3" "Setting up Nightly Synapse at <vault>/scripts/nightly-synapse/"

SYNAPSE_DEST="${VAULT_PATH}/scripts/nightly-synapse"
mkdir -p "$SYNAPSE_DEST"

if [ ! -d "$REPO_SYNAPSE_DIR" ]; then
    die "Source directory not found: ${REPO_SYNAPSE_DIR}"
fi

# Copy JS files, replacing placeholders
for jsfile in "$REPO_SYNAPSE_DIR"/*.js "$REPO_SYNAPSE_DIR"/*.json; do
    [ -f "$jsfile" ] || continue
    BASENAME=$(basename "$jsfile")
    sed \
        -e "s|{여기에_본인_볼트_절대경로}|${VAULT_PATH}|g" \
        -e "s|{VAULT_PATH}|${VAULT_PATH}|g" \
        -e "s|{분류_기준_문서_경로}|${GROUND_TRUTH_REL}|g" \
        "$jsfile" > "${SYNAPSE_DEST}/${BASENAME}"
    success "Copied ${BASENAME}"
done

# npm install
info "Installing Node.js dependencies..."
(cd "$SYNAPSE_DEST" && npm install --silent 2>/dev/null)
success "Node.js dependencies installed"

# ---------------------------------------------------------------------------
# Step 4: Install backup & sync scripts
# ---------------------------------------------------------------------------
step "4" "Setting up backup scripts at ~/ObsidianBackup/"

BACKUP_DEST="${HOME_DIR}/ObsidianBackup"
mkdir -p "$BACKUP_DEST"

if [ ! -d "$REPO_BACKUP_DIR" ]; then
    die "Source directory not found: ${REPO_BACKUP_DIR}"
fi

LOG_PATH="${BACKUP_DEST}/sync.log"

for shfile in "$REPO_BACKUP_DIR"/*.sh; do
    [ -f "$shfile" ] || continue
    BASENAME=$(basename "$shfile")
    sed \
        -e "s|{VAULT_PATH}|${VAULT_PATH}|g" \
        -e "s|{여기에_본인_볼트_절대경로}|${VAULT_PATH}|g" \
        -e "s|{LOG_PATH}|${LOG_PATH}|g" \
        -e "s|{여기에_로그파일_경로}|${LOG_PATH}|g" \
        -e "s|{BACKUP_DIR}|${BACKUP_DEST}|g" \
        -e "s|{여기에_백업_폴더_경로}|${BACKUP_DEST}|g" \
        "$shfile" > "${BACKUP_DEST}/${BASENAME}"
    chmod +x "${BACKUP_DEST}/${BASENAME}"
    success "Copied ${BASENAME}"
done

# ---------------------------------------------------------------------------
# Step 5: Create ~/.claude/.mcp.json
# ---------------------------------------------------------------------------
step "5" "Configuring Claude MCP server registration"

CLAUDE_DIR="${HOME_DIR}/.claude"
MCP_JSON="${CLAUDE_DIR}/.mcp.json"
mkdir -p "$CLAUDE_DIR"

# If .mcp.json already exists, back it up
if [ -f "$MCP_JSON" ]; then
    BACKUP_NAME=".mcp.json.backup.$(date +%Y%m%d%H%M%S)"
    cp "$MCP_JSON" "${CLAUDE_DIR}/${BACKUP_NAME}"
    warn "Existing .mcp.json backed up as ${BACKUP_NAME}"
fi

cat > "$MCP_JSON" << MCPEOF
{
  "mcpServers": {
    "obsidian-search": {
      "command": "${HOME_DIR}/obsidian-mcp-server/venv/bin/python",
      "args": ["${HOME_DIR}/obsidian-mcp-server/server.py"],
      "cwd": "${HOME_DIR}/obsidian-mcp-server"
    }
  }
}
MCPEOF

success "Created ${MCP_JSON}"

# ---------------------------------------------------------------------------
# Step 6: Create macOS LaunchAgent plist files
# ---------------------------------------------------------------------------
step "6" "Creating macOS LaunchAgents"

LAUNCH_DIR="${HOME_DIR}/Library/LaunchAgents"
mkdir -p "$LAUNCH_DIR"

NODE_PATH=$(which node)

# 6a. GitHub sync (every 30 minutes)
SYNC_PLIST="${LAUNCH_DIR}/com.user.obsidian-github-sync.plist"
cat > "$SYNC_PLIST" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.obsidian-github-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>${HOME_DIR}/ObsidianBackup/sync_from_github.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>1800</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>${HOME_DIR}/ObsidianBackup/sync-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME_DIR}/ObsidianBackup/sync-stderr.log</string>
</dict>
</plist>
PLISTEOF
success "Created sync plist"

# 6b. Daily backup (21:30)
BACKUP_PLIST="${LAUNCH_DIR}/com.user.obsidian-backup.plist"
cat > "$BACKUP_PLIST" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.obsidian-backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>${HOME_DIR}/ObsidianBackup/backup_vault.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>21</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
</dict>
</plist>
PLISTEOF
success "Created backup plist"

# 6c. Nightly Synapse (21:30)
SYNAPSE_PLIST="${LAUNCH_DIR}/com.user.nightly-synapse.plist"
cat > "$SYNAPSE_PLIST" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.nightly-synapse</string>
    <key>ProgramArguments</key>
    <array>
        <string>${NODE_PATH}</string>
        <string>${VAULT_PATH}/scripts/nightly-synapse/run-now.js</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>21</integer>
        <key>Minute</key>
        <integer>30</integer>
    </dict>
    <key>WorkingDirectory</key>
    <string>${VAULT_PATH}/scripts/nightly-synapse</string>
</dict>
</plist>
PLISTEOF
success "Created synapse plist"

# ---------------------------------------------------------------------------
# Step 7: Load LaunchAgents
# ---------------------------------------------------------------------------
step "7" "Loading LaunchAgents"

load_agent() {
    local plist_path="$1"
    local label="$2"

    # Unload first if already loaded (ignore errors)
    launchctl bootout "gui/$(id -u)/${label}" 2>/dev/null || true

    if launchctl load "$plist_path" 2>/dev/null; then
        success "Loaded ${label}"
    else
        warn "Could not load ${label} — you may need to load it manually:"
        warn "  launchctl load ${plist_path}"
    fi
}

load_agent "$SYNC_PLIST"    "com.user.obsidian-github-sync"
load_agent "$BACKUP_PLIST"  "com.user.obsidian-backup"
load_agent "$SYNAPSE_PLIST" "com.user.nightly-synapse"

# ---------------------------------------------------------------------------
# Step 8: Run first indexing
# ---------------------------------------------------------------------------
step "8" "Running first indexing"

INDEXER="${MCP_DEST}/indexer.py"
if [ -f "$INDEXER" ]; then
    info "Running indexer.py (first run downloads the embedding model ~500MB)..."
    if "${MCP_DEST}/venv/bin/python" "$INDEXER" --full 2>&1; then
        success "First indexing complete"
    else
        warn "Indexing failed — you can run it manually later:"
        warn "  cd ~/obsidian-mcp-server && ./venv/bin/python indexer.py --full"
    fi
else
    warn "indexer.py not found in source. Skipping first indexing."
    warn "Make sure to create it and run: cd ~/obsidian-mcp-server && ./venv/bin/python indexer.py --full"
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${GREEN}${BOLD}  Installation Complete!${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""
echo -e "${BOLD}What was created:${NC}"
echo ""
echo -e "  ${GREEN}MCP Server${NC}"
echo "    ~/obsidian-mcp-server/           Python venv + indexer + search + server"
echo ""
echo -e "  ${GREEN}Nightly Synapse${NC}"
echo "    ${VAULT_PATH}/scripts/nightly-synapse/"
echo "                                     Auto-classification + audit"
echo ""
echo -e "  ${GREEN}Backup & Sync${NC}"
echo "    ~/ObsidianBackup/                sync_from_github.sh + backup_vault.sh"
echo ""
echo -e "  ${GREEN}Claude Config${NC}"
echo "    ~/.claude/.mcp.json              MCP server registration"
echo ""
echo -e "  ${GREEN}LaunchAgents${NC}"
echo "    com.user.obsidian-github-sync    Every 30 min"
echo "    com.user.obsidian-backup         Daily 21:30"
echo "    com.user.nightly-synapse         Daily 21:30"
echo ""
echo -e "${BOLD}Next steps:${NC}"
echo "  1. Restart Claude Code to pick up the MCP server"
echo "  2. Test: ask Claude 'search my notes about <topic>'"
echo "  3. Edit bridge_keywords.py with your own keywords"
echo "  4. (Optional) Set up CLAUDE.md in your vault root"
echo ""
echo -e "${BOLD}Vault path:${NC} ${VAULT_PATH}"
echo -e "${BOLD}Ground Truth:${NC} ${GROUND_TRUTH_REL:-<not set>}"
echo ""
