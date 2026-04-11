#!/bin/bash
# GitHub ↔ Obsidian Vault 양방향 동기화 스크립트
# 1. 로컬 변경 → GitHub push (삭제/이동/수정 반영)
# 2. GitHub 변경 → 로컬 pull (텔레그램 메모 등 수신)

set -e

VAULT="${VAULT_PATH:-/path/to/your/obsidian-vault}"
LOG="${BACKUP_DIR:-$HOME/ObsidianBackup}/sync.log"

cd "$VAULT" || exit 1

# 1. 로컬 변경사항을 GitHub에 push
if [ -n "$(git status --porcelain)" ]; then
    # .env, 시크릿 파일이 추가되지 않도록 .gitignore 기반으로 추가
    git add -A
    # .env 등 민감 파일이 stage에 올라왔으면 제거
    git diff --cached --name-only | grep -iE '\.env$|credentials|secret|\.key$|\.pem$' | xargs -r git reset HEAD -- 2>/dev/null
    git commit -m "auto-sync: $(date '+%Y-%m-%d %H:%M') 볼트 변경사항 동기화" --quiet 2>/dev/null || true
    if ! git push origin main --quiet 2>/dev/null; then
        echo "$(date '+%Y-%m-%d %H:%M'): push 실패" >> "$LOG"
        exit 1
    fi
    echo "$(date '+%Y-%m-%d %H:%M'): push 완료" >> "$LOG"
fi

# 2. GitHub 변경사항을 로컬로 pull (텔레그램 메모 등)
if ! git pull --no-rebase origin main --quiet 2>/dev/null; then
    echo "$(date '+%Y-%m-%d %H:%M'): pull 실패 (충돌 가능성). 수동 확인 필요." >> "$LOG"
    # 충돌 시 merge 취소하고 원래 상태로 복원
    git merge --abort 2>/dev/null || true
    exit 1
fi
echo "$(date '+%Y-%m-%d %H:%M'): pull 완료" >> "$LOG"
