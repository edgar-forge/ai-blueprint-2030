# Claude Code 도구 확장 및 GBrain 도입

## 개요

[awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) 허브에서 실제 워크플로우에 맞는 도구를 선별 적용하고, [GBrain](https://github.com/garrytan/gbrain)을 벡터 검색 코어로 도입한 기록.

**선별 기준**: "설계는 적게, 사용은 많이" — 설치 후 바로 생산성에 기여하는 것만 도입.

---

## 1. 설치된 CLI 도구

| 도구 | 설치 명령 | 용도 |
|------|----------|------|
| **Claude Squad** | `brew install claude-squad` | 여러 Claude 에이전트를 tmux 기반으로 병렬 관리 |
| **Usage Monitor** | `pipx install claude-monitor` | 토큰/비용 실시간 대시보드, 소진 예측 |
| **cchistory** | `npm install -g cchistory` | 과거 세션 명령어 히스토리 검색 |
| **GBrain** | `bun add -g github:garrytan/gbrain` | 벡터 검색 + AI 장기 기억 엔진 |

---

## 2. MCP 서버 추가

| 서버 | 등록 명령 | 용도 |
|------|----------|------|
| **Task Master** | `claude mcp add taskmaster-ai -- npx -y task-master-ai` | 태스크 분해, 의존성 추적 |
| **GBrain** | `claude mcp add gbrain -- gbrain serve` | 하이브리드 검색 (벡터+키워드+RRF) |

---

## 3. RIPER Workflow

**출처**: [claude-code-riper-5](https://github.com/tony/claude-code-riper-5)

5단계 개발 워크플로우를 슬래시 명령어로 강제:

| 명령어 | 모드 | 제약 |
|--------|------|------|
| `/riper:strict` | 엄격 모드 활성화 | 모드 없이는 행동 불가 |
| `/riper:research` | RESEARCH | 읽기만 가능 |
| `/riper:innovate` | INNOVATE | 브레인스토밍만 |
| `/riper:plan` | PLAN | 명세 작성, 실행 금지 |
| `/riper:execute` | EXECUTE | 승인된 계획만 실행 |
| `/riper:review` | REVIEW | 구현 검증 |
| `/riper:workflow` | 전체 | 5단계 순차 + 승인 게이트 |

`.claude/commands/riper/` 에 마크다운 파일로 생성. `$ARGUMENTS`로 작업 컨텍스트를 전달받는다.

---

## 4. GBrain — 벡터 검색 엔진

### GBrain이란

YC CEO Garry Tan이 만든 AI 에이전트용 개인 지식 베이스. 마크다운 노트를 Postgres + pgvector 기반 DB로 통합하고, LLM 에이전트가 장기 기억처럼 읽고 쓸 수 있게 하는 시스템.

### 셋업 과정

```bash
# 1. 설치
curl -fsSL https://bun.sh/install | bash
bun add -g github:garrytan/gbrain

# 2. 초기화 (PGLite = 로컬 임베디드 Postgres, 서버 불필요)
gbrain init --pglite

# 3. 마크다운 import
gbrain import /path/to/vault --no-embed

# 4. 벡터 임베딩 생성 (OpenAI API 키 필요)
export OPENAI_API_KEY="sk-..."
gbrain embed --stale

# 5. Claude Code에 MCP 서버로 연결
claude mcp add gbrain -- gbrain serve
```

### 결과

| 항목 | 값 |
|------|-----|
| 엔진 | PGLite (로컬) |
| 임베딩 모델 | OpenAI `text-embedding-3-large` (1536차원) |
| 규모 | 790페이지, 2,176 chunks |
| 임베딩 비용 | **$0.16** (전체 볼트, 1회성) |
| 검색 방식 | 하이브리드 (벡터 HNSW + 키워드 tsvector + RRF 융합) |

### 유지보수

```bash
# 새 노트 추가 후
gbrain import /path/to/vault --no-embed
gbrain embed --stale

# 통계
gbrain stats

# 검색
gbrain query "의미론적 질문"    # 하이브리드 검색
gbrain search "키워드"          # 키워드 검색

# 규모 확장
gbrain migrate --to supabase
```

### 기존 LanceDB 시스템과 비교

| 항목 | LanceDB (기존) | GBrain |
|------|---------------|--------|
| 임베딩 | sentence-transformers (384차원, 로컬) | OpenAI (1536차원, API) |
| 검색 | 4중 가중치 | 하이브리드 RRF + 멀티쿼리 확장 |
| 비용 | 무료 | ~$0.16/전체볼트 |
| 확장 | 로컬 전용 | PGLite → Supabase 마이그레이션 가능 |
| MCP 도구 | 2개 (search, get) | 30개 |

---

## 5. 활용 시나리오

### 콘텐츠 제작 병렬화

```bash
cs   # Claude Squad
# 세션 1~3: 각각 다른 대본의 소스 추출을 동시 진행
```

### 지식 검색 → 대본 작성

```bash
gbrain query "프레이밍과 설득의 관계"
# → 관련 노트가 유사도 순으로 나옴 → 대본에 바로 활용
```

### 기술 개발 가드레일

```
/riper:strict 새 기능 추가
# RESEARCH → INNOVATE → PLAN → [승인] → EXECUTE → REVIEW
```

---

## 6. 추후 작업

- [ ] Trail of Bits Security Skills 설치
- [ ] 기존 LanceDB 시스템과 GBrain 역할 정리
- [ ] GBrain 자동 동기화 설정
- [ ] Supabase 마이그레이션 시점 판단
