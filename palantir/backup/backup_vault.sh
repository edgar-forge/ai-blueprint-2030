#!/bin/bash
# Obsidian Vault 일일 백업 스크립트
# 압축 파일명: ObsidianVault_YYYY-MM-DD.tar.gz

VAULT="${VAULT_PATH:-/path/to/your/obsidian-vault}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/ObsidianBackup}"
DATE=$(date +%Y-%m-%d)
FILENAME="ObsidianVault_${DATE}.tar.gz"

# 압축 백업
tar -czf "${BACKUP_DIR}/${FILENAME}" -C "$(dirname "$VAULT")" "$(basename "$VAULT")"

# 7일 이상 된 백업 자동 삭제 (디스크 관리)
find "$BACKUP_DIR" -name "ObsidianVault_*.tar.gz" -mtime +7 -delete

echo "$(date): Backup completed - ${FILENAME}"
