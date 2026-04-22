# Phase 1 재개 가이드 (집에서 실행)

## 현재 상태 (2026-04-22 외출 전)

- **활성 시스템**: Scenario A (어제 KURE-v1 1024D 상태)
- **DB**: vault.lancedb — 2,458행, 구 스키마 (chunk_id 없음)
- **백업**: vault.lancedb.backup_scenarioA_20260422_1038

## 오늘 중단된 작업

Scenario B Phase 1 (마크다운 헤더 청킹) 재인덱싱을 시도했으나 CPU 1 thread로 44분 지나도 완료 안 됨 → 외출을 위해 중단.

## 준비된 것

- `indexer_phase1.py` — 청킹 로직 + **CPU 4 thread 설정** (집 환경 전용)
- `search_phase1.py` — dedup 로직 (검색은 1 thread 유지)
- 의존성 이미 설치됨: langchain-text-splitters, kiwipiepy, rank_bm25
- 벤치마크: `benchmark.py` (12개 쿼리, A/B/C/D 타입 분리)

## 집에서 재개 — 명령어 복붙

```bash
cd ~/obsidian-mcp-server

# 1. Phase 1 코드 활성화
cp indexer.py indexer.py.backup_scenarioA_$(date +%Y%m%d_%H%M)
cp search.py search.py.backup_scenarioA_$(date +%Y%m%d_%H%M)
cp indexer_phase1.py indexer.py
cp search_phase1.py search.py

# 2. DB 백업 (혹시 모를 롤백 대비)
cp -r vault.lancedb vault.lancedb.backup_scenarioA_$(date +%Y%m%d_%H%M)

# 3. 전체 재인덱싱 (4-thread, 예상 10~15분)
caffeinate -i ./venv/bin/python indexer.py --full
```

**주의**
- 인덱싱 중 노트북 약간 뜨거워짐 (4 thread 풀가동)
- 끝날 때까지 무거운 작업 자제
- 전원 어댑터 연결 권장

## 완료 후 검증

```bash
# 벤치마크 실행
./venv/bin/python benchmark.py

# 기대 결과 (Phase 1 목표)
# P@1: 6~8/12 (이전 5/12)
# P@5: 10~11/12 (이전 6/12)
# D타입 (파일 tail) 개선 확인
```

결과 좋으면 다음 단계 (Phase 2: BM25 + RRF 하이브리드) 진행.
결과 나쁘면 롤백.

## 롤백 방법 (Phase 1 실패 시)

```bash
cd ~/obsidian-mcp-server
cp search.py.backup_scenarioA_20260422_1038 search.py
cp indexer.py.backup_scenarioA_20260422_1038 indexer.py
rm -rf vault.lancedb
cp -r vault.lancedb.backup_scenarioA_20260422_1038 vault.lancedb
```
