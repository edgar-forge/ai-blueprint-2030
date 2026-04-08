#!/bin/bash
# =============================================================================
# Obsidian Vault Daily Backup
# =============================================================================
# Creates a compressed tar.gz backup of the vault.
# Automatically deletes backups older than 7 days.
#
# Placeholders (replaced by setup.sh):
#   {VAULT_PATH}  — Absolute path to the Obsidian vault
#   {BACKUP_DIR}  — Absolute path to the backup directory
# =============================================================================

set -e

VAULT="{VAULT_PATH}"
BACKUP_DIR="{BACKUP_DIR}"
DATE=$(date +%Y-%m-%d)
FILENAME="ObsidianVault_${DATE}.tar.gz"

# ---------------------------------------------------------------------------
# Safety checks
# ---------------------------------------------------------------------------
if [ ! -d "$VAULT" ]; then
    echo "$(date): ERROR — Vault not found: ${VAULT}"
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
fi

# ---------------------------------------------------------------------------
# Create compressed backup
# ---------------------------------------------------------------------------
# Exclude .git and .obsidian/cache to reduce size
tar -czf "${BACKUP_DIR}/${FILENAME}" \
    --exclude='.git' \
    --exclude='.obsidian/cache' \
    --exclude='.smart-env' \
    -C "$(dirname "$VAULT")" "$(basename "$VAULT")"

# ---------------------------------------------------------------------------
# Retention: delete backups older than 7 days
# ---------------------------------------------------------------------------
find "$BACKUP_DIR" -name "ObsidianVault_*.tar.gz" -mtime +7 -delete

echo "$(date): Backup completed — ${FILENAME} ($(du -h "${BACKUP_DIR}/${FILENAME}" | cut -f1))"
