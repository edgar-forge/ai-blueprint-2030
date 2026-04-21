# Claude Code 도구 확장 정리

## 개요

[awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) 허브에서 실제 워크플로우에 맞는 도구를 선별 적용한 기록.

**선별 기준**: "설계는 적게, 사용은 많이" — 설치 후 바로 생산성에 기여하는 것만 도입.

> **2026-04-21 업데이트**: GBrain 제거. 2,400+ 파일 규모에서 PGLite 크래시 반복. LanceDB 기반 `obsidian-search` MCP가 같은 규모에서 안정 운영 — primary 검색 엔진으로 확정.

---

## 1. 설치된 CLI 도구

| 도구 | 설치 명령 | 용도 |
|------|----------|------|
| **Claude Squad** | `brew install claude-squad` | 여러 Claude 에이전트를 tmux 기반으로 병렬 관리 |
| **Usage Monitor** | `pipx install claude-monitor` | 토큰/비용 실시간 대시보드, 소진 예측 |
| **cchistory** | `npm install -g cchistory` | 과거 세션 명령어 히스토리 검색 |

---

## 2. MCP 서버

| 서버 | 등록 명령 | 용도 |
|------|----------|------|
| **Task Master** | `claude mcp add taskmaster-ai -- npx -y task-master-ai` | 태스크 분해, 의존성 추적 |
| **obsidian-search** | `obsidian-mcp-server/` 참조 | 볼트 벡터 검색 (LanceDB) |

---

## 3. RIPER Workflow

**출처**: [claude-code-riper-5](https://github.com/tony/claude-code-riper-5)

5단계 개발 워크플로우를 슬래시 명령어로 강제:

| 명령어 | 모드 | 제약 |
|--------|------|------|
| `/riper:strict` | 엄격 모드 | 모드 없이는 행동 불가 |
| `/riper:research` | RESEARCH | 읽기만 가능 |
| `/riper:innovate` | INNOVATE | 브레인스토밍만 |
| `/riper:plan` | PLAN | 명세 작성 |
| `/riper:execute` | EXECUTE | 승인된 계획만 실행 |
| `/riper:review` | REVIEW | 구현 검증 |
| `/riper:workflow` | 전체 | 5단계 순차 + 승인 게이트 |

`.claude/commands/riper/` 에 마크다운 파일로 생성. `$ARGUMENTS`로 작업 컨텍스트를 전달받는다.

---

## 4. 볼트 검색 엔진 — LanceDB (obsidian-search)

### 시스템 구성

```
~/obsidian-mcp-server/
├── indexer.py           # 노트 → 벡터 변환 → LanceDB 저장 (증분 기본)
├── search.py            # 4중 가중치 검색
├── bridge_keywords.py   # 35개 브릿지 키워드 사전
├── server.py            # FastMCP 서버
├── vault.lancedb/       # 벡터 DB 저장소 (~31MB)
└── venv/                # Python 가상환경
```

### 주요 특징

| 항목 | 값 |
|------|-----|
| 임베딩 모델 | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2, 384차원) |
| 벡터 DB | LanceDB (파일 기반, 로컬) |
| 검색 | 4중 가중치 (벡터유사도 + 제목보너스 + 브릿지보너스 × 폴더가중치) |
| 증분 속도 | 2,457 노트 기준 9.4초 |
| 비용 | 무료 (로컬 모델, 네트워크 불필요) |
| 한국어 | 특화 multilingual 모델 |

### 운영 명령어

```bash
# 증분 인덱싱 (기본)
cd ~/obsidian-mcp-server && ./venv/bin/python indexer.py

# 전체 재인덱싱 (모델 변경 등 예외)
cd ~/obsidian-mcp-server && ./venv/bin/python indexer.py --full

# DB 손상 시 복구
rm -rf ~/obsidian-mcp-server/vault.lancedb/
cd ~/obsidian-mcp-server && ./venv/bin/python indexer.py --full
```

---

## 5. GBrain 시도 회고 (2026-04-12 ~ 2026-04-21)

[GBrain](https://github.com/garrytan/gbrain) (PGLite + OpenAI 임베딩) 도입 후 중단한 기록.

**시도 배경**:
- Obsidian 볼트를 30분 내 AI 에이전트용 지식 베이스로 전환한다는 약속
- 하이브리드 검색 (벡터 + 키워드 + RRF)

**실제 결과**:
- 초기 790페이지 import + 임베딩 성공 ($0.16)
- 2,400+ 파일로 성장하면서 PGLite WASM Aborted 크래시 반복
- 공식 문서도 "1,000 파일 초과 시 Supabase 이관 권장"

**중단 결정 근거**:
- 로컬·개인용이라 Supabase($25/월)는 오버킬
- 이미 LanceDB 기반 시스템이 같은 규모에서 안정 운영 중
- 4중 가중치 검색이 개인 볼트 워크플로우에 더 적합

**교훈**:
- "30분 셋업" 마케팅을 개인 대규모 볼트에 그대로 적용하면 위험. 원작자 use case(VC 미팅 관리, 수백 페이지)와 스케일이 다르다.
- 새 도구 도입 전 **기존 도구가 같은 규모에서 검증됐는지** 먼저 확인.
- 도구 철학이 실제 워크플로우와 맞는지 점검.

---

## 6. 최종 구성

```
~/.claude/
├── commands/              ← 글로벌 슬래시 명령어
├── skills/                ← 자율 호출 스킬
├── rules/                 ← 글로벌 규칙
├── agents/                ← 서브에이전트
└── plugins/marketplaces/

Obsidian Vault/.claude/
├── commands/riper/        ← RIPER 워크플로우 (7개)
└── CLAUDE.md              ← 볼트 전용 규칙

~/obsidian-mcp-server/     ← 볼트 검색 엔진 (LanceDB, primary)
```
