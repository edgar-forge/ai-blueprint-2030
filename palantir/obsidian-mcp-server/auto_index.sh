#!/bin/bash
# obsidian-search 자동 증분 인덱싱 스크립트
# launchd가 30분마다 호출. 변경 없으면 0.1초에 끝남.

set -e

LOG="/Users/edger-choi/obsidian-mcp-server/indexer_auto.log"
cd /Users/edger-choi/obsidian-mcp-server

# 이미 인덱서가 돌고 있으면 스킵 (중복 실행 방지)
if pgrep -f "indexer.py" > /dev/null; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] 다른 indexer.py 실행 중. 스킵." >> "$LOG"
  exit 0
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 자동 증분 인덱싱 시작 ===" >> "$LOG"
./venv/bin/python indexer.py >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 완료 ===" >> "$LOG"

# 로그 파일 크기 관리 (10MB 초과 시 오래된 절반 삭제)
LOG_SIZE=$(stat -f%z "$LOG" 2>/dev/null || echo 0)
if [ "$LOG_SIZE" -gt 10485760 ]; then
  tail -c 5242880 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] === 로그 로테이션 ===" >> "$LOG"
fi
