#!/bin/bash
# =============================================================================
# GitHub <-> Obsidian Vault Bidirectional Sync
# =============================================================================
# 1. Push local changes to GitHub
# 2. Pull remote changes (e.g. Telegram pipeline memos) to local
#
# Placeholders (replaced by setup.sh):
#   {VAULT_PATH} — Absolute path to the Obsidian vault
#   {LOG_PATH}   — Absolute path to the sync log file
# =============================================================================

set -e

VAULT="{VAULT_PATH}"
LOG="{LOG_PATH}"

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

# ---------------------------------------------------------------------------
# Safety: ensure vault exists and is a git repo
# ---------------------------------------------------------------------------
if [ ! -d "$VAULT" ]; then
    echo "${TIMESTAMP}: Vault not found: ${VAULT}" >> "$LOG"
    exit 1
fi

cd "$VAULT" || exit 1

if [ ! -d ".git" ]; then
    echo "${TIMESTAMP}: Not a git repository: ${VAULT}" >> "$LOG"
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Push local changes to GitHub
# ---------------------------------------------------------------------------
if [ -n "$(git status --porcelain)" ]; then
    git add -A

    # Safety check: remove sensitive files from staging
    # Prevents accidental commit of .env, credentials, API keys, etc.
    SENSITIVE_PATTERN='\.env$|\.env\.|credentials|secret|\.key$|\.pem$|\.p12$|token'
    STAGED_SENSITIVE=$(git diff --cached --name-only | grep -iE "$SENSITIVE_PATTERN" 2>/dev/null || true)

    if [ -n "$STAGED_SENSITIVE" ]; then
        echo "${TIMESTAMP}: [WARN] Removing sensitive files from staging:" >> "$LOG"
        echo "$STAGED_SENSITIVE" >> "$LOG"
        echo "$STAGED_SENSITIVE" | xargs -r git reset HEAD -- 2>/dev/null
    fi

    # Only commit if there are still staged changes after safety removal
    if [ -n "$(git diff --cached --name-only)" ]; then
        git commit -m "auto-sync: ${TIMESTAMP} 볼트 변경사항 동기화" --quiet 2>/dev/null || true

        if ! git push origin main --quiet 2>/dev/null; then
            echo "${TIMESTAMP}: push failed" >> "$LOG"
            exit 1
        fi
        echo "${TIMESTAMP}: push complete" >> "$LOG"
    else
        echo "${TIMESTAMP}: no changes to push (sensitive files excluded)" >> "$LOG"
    fi
else
    echo "${TIMESTAMP}: no local changes" >> "$LOG"
fi

# ---------------------------------------------------------------------------
# 2. Pull remote changes (Telegram memos, other devices, etc.)
# ---------------------------------------------------------------------------
if ! git pull --no-rebase origin main --quiet 2>/dev/null; then
    echo "${TIMESTAMP}: pull failed (possible merge conflict). Manual resolution required." >> "$LOG"
    # Safely abort merge on conflict
    git merge --abort 2>/dev/null || true
    exit 1
fi

echo "${TIMESTAMP}: sync complete" >> "$LOG"
