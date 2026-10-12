# Changelog

이 파일은 AI Blueprint 2030 가이드의 중요한 변경 사항을 기록합니다.

형식: [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 기반.

---

## [2026-10-12] — 링크 하나로 세팅 끝 (플러그인 자동 설치 · 한국어로 묻기 · 검색 엔진은 1주 뒤, LLM 위키는 한 달 뒤 · 폴더 설명 보강)

### Added (추가)

- `palantir/install_plugins.sh` — Calendar · Periodic Notes · Smart Typography 본체를 볼트 `.obsidian/plugins/`에 받아 넣는다(`--with-importer`로 Importer까지). 판은 옵시디언이 깔 때와 같다 — 각 저장소 기본 가지의 manifest.json에 적힌 판 번호의 배포 파일(가장 최근 배포가 베타인 Calendar도 1.5.10). styles.css는 있으면 받는다. 이미 있는 것은 건너뛰고 설정값(data.json)은 건드리지 않는다. 파이썬 없이 돈다. 임시 볼트 셋에서 시험했다.
- `vault-template/1. Project/세컨브레인 만들기/` — 처음 30일의 프로젝트 폴더. 카드 한 장(`_카드.md`, 끝 날짜는 세팅할 때 Claude가 적는다)과 나중에 붙이는 것 둘의 노트(`검색 엔진 — 1주 뒤에 붙인다.md` · `LLM 위키 — 한 달 뒤에 붙인다.md`). 노트마다 언제 · 왜 필요한가(컴퓨터가 노트를 잘 쓰려고) · 무엇인가 · 어떻게 쓰나 · 성원은 이렇게 쓴다 · 까는 법.

### Changed (변경)

- `START.md` — 링크만 붙여 넣어도 된다(Claude가 저장소를 `~/Downloads/`에 받고 시작). 사람에게 하는 말과 묻는 말은 전부 한국어로. 0단계 옵시디언 확인(맥 + Homebrew면 대신 설치), 2단계에 `성원에게_묻기/`와 `세팅/` 다섯 장을 볼트 `3. Resource/`로 복사(`.vscode/`는 검색 엔진을 붙일 때), 3단계 플러그인 자동 설치, 4단계 프로젝트 카드 끝 날짜, 7단계 VS Code가 있으면 확장 둘. 검색 엔진 설치 단계는 뺐다 — 1주 뒤.
- 옵시디언 첫 창을 한국어 화면 문구로 — 이 보관함의 작성자를 신뢰하시나요? → 작성자를 신뢰하고 플러그인 사용하기. `START.md` · `README.md` · `세팅/옵시디언.md` · 답 파일.
- `README.md` 첫 동작 — 링크 한 줄로. Claude에게 주는 한 단락(저장소 받기 → START).
- PARA · 슬립박스 폴더 설명(`vault-template/`의 `_여기는.md` 다섯 장) — 각 3줄에서 정의(성원 영상 · 블로그 말) · 무엇을 넣나 · 헷갈릴 때 · 언제 옮기나 · AI는 여기서로 늘렸다. 슬립박스 다섯 묶음 폴더와 상태 허브의 안내 줄은 `0. Slip-Box/_여기는.md`로 보낸다.
- `세팅/MCP 서버.md` — 10/12 성원 질문 둘과 답(실제로 쓰이나 · 읽기 전용은 안전장치가 아니다 · 늘 떠 있지 않다, 공식 문서 출처). 결론은 1주 뒤에 검색 엔진과 함께.
- `세팅/검색 엔진.md` · `세팅/LLM 위키.md` · `세팅/VS Code.md` 4절 · 답 파일(검색 엔진은 꼭 필요해요 · 윈도우에서도 돼요 · LLM 위키는 지금 필요해요 · 옵시디언 플러그인 뭐 깔아요 · PARA가 뭐예요)과 묶음 · `30일/README.md`(0일 · 2주 3번 · 4주 4번) · 볼트 틀 `CLAUDE.md`(한국어로 말한다 · 폴더 설명 자리 · 검색 서버는 1주 뒤) · 저장소 `CLAUDE.md`(말은 한국어로) — 같은 말로 맞췄다.
- `세팅/옵시디언.md` 6절 '뺀 것 둘' — Dataview, Mousewheel Image Zoom(옵시디언 1.13부터 이미지를 고른 뒤 + · − 키로 크기, 0으로 원래대로). `guides/01` 머리 한 줄에도 같은 이유.

### 같은 날 저녁 — 읽는 분 기준으로 말투 · 표시 · 라우터

- 읽는 분을 부르는 말을 성원 블로그 기준으로 맞췄다(README · START · guides 세 권 · 검색 · 답 파일 · 볼트 노트). 존댓말 글은 여러분, 반말 글은 우리 또는 주어 없이.
- 작업 표시를 걷었다 — 비공개 노트 출처 괄호, 답 파일의 💡, 출처 접기 상자, ☐ 자리표시, 실측 꼬리.
- 말투가 맞지 않거나 받아쓰기가 깨진 음성 인용은 영상 · 블로그의 같은 뜻 문장이나 평서문으로 바꿨다.
- 저장소 `CLAUDE.md`를 라우터로 줄였다. 세팅은 START, 질문은 `성원에게_묻기/README.md`의 Claude가 답하는 법으로 보낸다.
- 볼트 `CLAUDE.md` — 0~5절은 그 사람의 규칙, 성원 쪽을 가리키는 줄은 6절 '처음 30일 동안만'으로 모았다. 다 쓰면 통째로 지운다. 새 노트 `1. Project/세컨브레인 만들기/CLAUDE.md는 라우터다 — 쓰면서 고친다.md`.
- README — 업데이트 알림은 Star가 아니라 Watch로 받는다.
- 사람들에게 말하는 글은 존댓말로 맞췄다(성원 기준 — 내 생각은 반말, 사람들에게 말하는 글은 존댓말). 답 파일과 묶음 · 볼트 설명 노트 · 예시 안내 · guides 03 · 세팅 장과 안내의 소제목. 받는 사람이 자기 생각을 적는 볼트 CLAUDE.md · 프로젝트 카드 · 템플릿과 Claude에게 주는 지시는 반말 그대로.

---

## [2026-10-10] — 만든 사람이 실제로 쓰는 세팅만 넣는다 (세팅 다섯 장 · 옵시디언 설정)

### Added (추가)

- `세팅/` — 만든 사람이 실제로 쓰는 세팅 다섯 장. 받는 사람 눈높이로, 만든 사람의 말은 「」 원문만.
  - `옵시디언.md` — 설치 → 코어 플러그인 열여섯(Templates는 폴더 `Templates`) → 커뮤니티 플러그인 넷(Calendar · Periodic Notes · Smart Typography, Importer는 옮겨 올 때 한 번)의 설치 법과 설정값 → 기본 동작 설정 세 줄 → 단축키 여섯 → 「나는 이렇게 쓴다」.
  - `VS Code.md` — 설치 · 확장 둘(Claude Code · 한국어 팩) · 볼트 폴더를 열면 Claude Code가 보인다 · 검색 엔진을 깐 사람만: 볼트를 열 때 색인(`.vscode/tasks.json`)과 자동 작업 허용 설정(`task.allowAutomaticTasks`).
  - `검색 엔진.md` — 무엇인가(뜻으로 찾기 · KURE-v1 · LanceDB) · 언제 붙이나(노트 수백 장 뒤) · 설치는 `검색/README.md`로 · 무게(모델 약 2GB, 세션에서 처음 검색할 때 메모리에 올라감).
  - `LLM 위키.md` — 볼트 밖에 두는 구조 지도 · Claude Code 플러그인 llm-wiki 설치 두 줄 · 쌓인 뒤에 만든다(30일의 4주차 자리).
  - `MCP 서버.md` — 만든 사람의 질문(10/10) 그대로 → 답(이 서버는 읽기만 한다 · 서버 없이도 Claude Code는 볼트를 읽는다 · 더해 주는 것은 뜻으로 찾기) → 결론(선택).
- `vault-template/.obsidian/` — 볼트 틀의 옵시디언 설정. `core-plugins.json` · `community-plugins.json`(calendar · periodic-notes · obsidian-smart-typography) · `app.json`(첨부 Attachments · 새 노트 Reference · 링크 자동 갱신) · `templates.json`(폴더 Templates) · `hotkeys.json`(단축키 여섯) · `plugins/periodic-notes/data.json`(일간 `YYYY. MM. DD` · To_Process_Daily · 틀 `Templates/일간 노트`, 주간 · 월간) · `plugins/calendar/data.json`. 플러그인 본체는 넣지 않았다. 옵시디언에서 설치하면 폴더가 생기고 이 설정이 적용된다.

### Changed (변경)

- `성원에게_묻기/옵시디언 플러그인 뭐 깔아요.md` — 커뮤니티 플러그인 목록을 넷으로(Calendar · Periodic Notes · Smart Typography · Importer는 옮겨 올 때 한 번). 머리의 「갱신 예정」 줄을 지우고 `세팅/옵시디언.md`로 가는 줄을 더했다. 만든 사람의 「」 인용은 그대로. 묶음 `성원에게_묻기.md`의 같은 구간도 똑같이 바꿨다.
- `README.md` — 「여기 있는 것」에 `세팅/` 다섯 장, `vault-template/` 줄에 옵시디언 설정, `palantir/` 줄에 백업 스크립트(선택).
- `START.md` — 2단계 복사에 `vault-template/.obsidian/` 설정도 같이, 커뮤니티 플러그인 셋은 옵시디언에서 설치하도록 `세팅/옵시디언.md` 3절을 알려 준다.
- `palantir/README.md` — 폴더 목록에서 텔레그램 · 도구 메모 줄을 지우고, `backup/`에 「백업하고 싶은 사람만, 비공개 저장소로」 설명을 붙였다. `setup.sh` 설명을 새 사용법(인자 · 환경 변수 · 등록 명령)으로.
- `palantir/obsidian-mcp-server/indexer.py · search.py · server.py` — 2026-04 판을 만든 사람이 지금 쓰는 판으로 바꿨다(제목 글자 겹침 보너스 · 폴더 보너스 · 브릿지 보너스 0 · 도움말 덧셈 공식). 볼트 경로는 환경 변수 `VAULT_PATH`, 검색 기록은 `OBSIDIAN_SEARCH_LOG=1`일 때만 서버 옆 `logs/`에.
- `palantir/setup.sh` — 고장 셋을 고쳤다. 볼트 경로를 첫 인자 또는 `VAULT_PATH`로 받고 키보드가 없을 때는 묻지 않는다(전에는 Claude Code가 돌리면 0단계에서 조용히 멈췄다). Claude Code 등록을 `~/.claude/.mcp.json` 통째 쓰기 대신 `claude mcp add --scope user`로(이미 있으면 건드리지 않고, `claude`가 없으면 명령을 보여 주고 끝). `langchain-text-splitters`가 pip 목록에 빠져 첫 색인이 실패하던 것을 넣었다.
- `검색/README.md` · `START.md` 5단계 — 새 사용법과 등록 자리(`~/.claude.json`), 설치는 백그라운드로, 윈도우는 안 된다는 한 줄.

### Removed (제거)

- `palantir/telegram-pipeline/`(5파일) — 텔레그램 메모를 볼트 저장소에 넣던 장치. 만든 사람도 2026-04 뒤로 쓰지 않는다.
- `palantir/claude-code-tools.md` · `palantir/obsidian-mcp-server/RESUME_AT_HOME.md` — 2026-04의 개인 메모 둘.

---

## [2026-10-09] — 궁금한 것은 만든 사람의 말로 답한다 (답 파일 · 읽는 규칙 · 예시)

### Added (추가)

- `CLAUDE.md`(저장소 루트) — Claude Code가 이 폴더에서 먼저 읽는 규칙. 세팅 요청이면 `START.md`의 「Claude Code가 할 일」을 따른다(「세팅해 줘」만 쳐도 시작). 질문이면 `성원에게_묻기/`의 답 파일부터 읽고 그 문장으로 짧게, 실행 중심으로 답한다. 답 파일에 없으면 없다고 밝히고 오픈채팅을 알려 준다. 상주 작업을 만들지 않고, 사람이 쓴 문장을 고치지 않는다.
- `성원에게_묻기/` — 답 파일 열일곱. 질문 하나에 파일 하나, 파일 이름이 질문이다(물음표는 파일 이름에서 빼고 제목에만). 폴더 `README.md`에 목록과 쓰는 법.
  - PARA가 뭐예요 · 슬립박스는 왜 써요 · Attachments는 뭐예요 · 레퍼런스는 어떻게 써요 · 클로드 코드 어떻게 설치해요 · 옵시디언 플러그인 뭐 깔아요 · 메모는 어디에 먼저 적어요 · AI가 틀리면 어떡해요 · 프롬프트를 배워야 하나요 · 노션이랑 뭐가 달라요 · LLM 위키는 지금 필요해요 · 검색 엔진은 꼭 필요해요 · 프롬프트는 어디 있어요 · 돈이 얼마나 들어요 · 클로드 말고 다른 AI로도 돼요 · AI가 정리하면 내 공부는요 · 윈도우에서도 돼요
- `성원에게_묻기.md`(루트) — 위 폴더를 한 파일로 이어 붙인 묶음. ChatGPT · Gemini · NotebookLM에 올리는 용도. 원본은 폴더다.
- `예시/` — 만든 사람 볼트의 실제 노트 몇 장 + `README.md`. 이렇게 쓴다는 참고용.
- `.github/ISSUE_TEMPLATE/config.yml` — 빈 이슈를 막고, 이슈 화면에 버튼 둘(먼저 AI에게 묻기 · 오픈채팅). 오픈채팅 주소는 방을 연 뒤에 넣는다.

### Changed (변경)

- `README.md` — 「여기 있는 것」에 `CLAUDE.md` · `성원에게_묻기/` · `성원에게_묻기.md` · `예시/`. 「궁금한 것을 묻는 곳」의 순서를 자료를 AI에 넣고 묻기 → 오픈채팅 → Issues로. 업데이트 절은 질문의 답이 `성원에게_묻기/`로 돌아온다고 고침. 30일 줄에 「초안, 영상 뒤에 다시 씀」 표시.
- `START.md` — 2단계에 `성원에게_묻기/`를 볼트 `3. Resource/성원에게_묻기/`로 복사(없는 것만).
- `vault-template/CLAUDE.md` — §4 작업 표에 「궁금한 것」 줄(답 파일 먼저, 그 문장으로).
- `예시/` — 옮겨 온 노트에서 네 곳을 가렸다(주간 한 줄 · 9/15 일간 한 문장 · 프로젝트 카드의 내부 출처 줄과 폴더 이름 줄). `예시/README.md`의 「손댄 것」과 일간 · 카드의 안내 블록에 가림을 적었다.
- `vault-template/` 아래 `_여기는.md` 17개 — 제목 + 한두 문장으로 줄이고 설명은 해당 답 파일로 보냄. 설명을 두 군데에 쓰지 않는다. `Processed_Weekly/_여기는.md` 한 줄 채움. `0. Slip-Box/_여기는.md`에 영구 노트 번호(HU · CU · NA · GR · LR + 숫자 · 영문) 한 줄 설명.
- `30일/README.md` — 머리에 한 블록: 유튜브 영상을 먼저 만든 뒤 다시 쓴다(성원 10/9 생각), 초안이라 바뀐다. 본문은 검색 엔진 '선택' 표시 두 곳(2주 3번 · 졸업 조건 2) 말고 그대로.

### Fixed (수정)

- `START.md` · `검색/README.md` · `palantir/setup.sh` — 한국어 검색 모델(KURE-v1) 크기를 약 500MB에서 약 2GB로 바로잡음 (2026-10-08).
- 아래 [2026-10-07] 기록 — `palantir/nightly-synapse/` 파일 수를 11에서 10으로 바로잡음(`palantir/templates/CLAUDE.md`는 따로 적힌 한 줄이다).

---

## [2026-10-07] — 링크 하나로 세팅 + 30일 + 질문 창구 (세팅을 한번에, 궁금한 것은 묻는다)

### Added (추가)

- `START.md` — 첫 동작. Claude Code에게 이 파일을 읽게 하면 볼트 틀 복사 · CLAUDE.md 채우기 · 첫 일간 노트까지 대신한다. 검색 엔진은 선택 단계.
- `vault-template/` — 볼트 틀. PARA 다섯 폴더 + `0. Slip-Box/`(인간 · 문화 · 자연 · 잠재성 · 삶의 법칙 · 개념 · 상태 허브) + `My Think/1. 일간 · 2. 주간`, 한국어 `CLAUDE.md`(라우터 · 항상 참인 규칙 · 자동 승격 금지 · 내 언어 원칙), `Templates/`(일간 노트 · 주간 검토 다섯 칸 · 영구 노트), `개념/` 양식(단어 · 행동 두 칸), `.vscode/tasks.json`(볼트를 열 때 색인).
- `30일/README.md` — 30일 커리큘럼 초안 v0. 0일 세팅(AI) · 1주 축적 · 2주 사용 · 3주 창조 · 4주 내 단어 · 주말 갱신 다섯 칸 · 졸업 조건 다섯.
- `검색/README.md` — 검색 엔진 설치 한 장. 긴 설명은 guides/03에 그대로.
- `.github/ISSUE_TEMPLATE/질문.md` — 질문 창구. 어디서 막혔나 · 무엇을 해 봤나 · 원하는 결과.

### Changed (변경)

- `README.md` — 첫 줄이 첫 동작(START). 「궁금한 것을 묻는 곳」(Issues · 오픈채팅 · 30일 동행) 추가. 가이드 세 권은 「왜」, 새 폴더들은 「오늘 할 것」으로 자리 정리.
- `palantir/setup.sh` — 하는 일을 셋으로 줄임: 볼트 틀 복사(없는 것만) · 검색 서버 설치 · 첫 색인. Node.js · Ground Truth 입력 불필요.
- `palantir/README.md` — 위 변경대로 다시 씀. 백업 · 동기화 스크립트는 「수동 · 선택」으로.
- `palantir/obsidian-mcp-server/auto_index.sh` — 머리 주석이 launchd를 가리키던 것을 VSCode folderOpen으로.

### Removed (제거)

- `palantir/nightly-synapse/`(10파일)와 setup.sh의 Nightly Synapse · LaunchAgents 단계 — 상주 자동화는 2026-09에 만든 사람 본인 볼트에서도 걷어냈다. 받는 사람이 켜게 할 이유가 없다.
- `palantir/templates/CLAUDE.md`(영어 4월 판) — `vault-template/CLAUDE.md`(한국어)로 대체.
- README의 코칭 가격 비교 문장.

---

## [2026-04-22 수정] — 자동 인덱싱 방식 변경 (launchd → VSCode folderOpen) + 데이터 손실 방어 코드

### ⚠️ Incident

launchd 30분 주기 자동 인덱싱 운영 중 **데이터 손실 사고 발생**:
- 원인 불명의 `scan_vault` 0개 반환 → 인덱서가 "전체 삭제"로 해석 → DB 전부 비워짐
- LanceDB 버전 복원(`tbl.restore(38)`)으로 데이터 복구 성공
- 근본 원인은 인덱서 방어 코드 부재 (단일 스캔 신뢰 후 대량 삭제)

### Changed (변경)

- `palantir/obsidian-mcp-server/indexer.py`: **`validate_scan_sanity()` 방어 코드 추가**
  - 이전 state가 10개 이상인데 현재 스캔 0개 → abort
  - 90% 이상 감소 → abort
  - 실제 대량 삭제 필요하면 `--full` 플래그로 명시 실행

### Removed (제거)

- `palantir/obsidian-mcp-server/com.user.obsidian-indexer.plist` — launchd 30분 주기 자동 인덱싱 **폐기**
  - 대체: VSCode `.vscode/tasks.json` folderOpen 트리거 (볼트 작업 시작 시점에만 인덱싱)
  - 장점: 타이밍 충돌 없음, 환경변수 상속 OK, 작업 맥락에 맞춤

### Lesson Learned

- **방어 코드 기본값**: 단일 파일시스템 관찰로 대량 삭제 결정 금지
- **LanceDB 버전 히스토리는 생명줄**: 사고 복구 가능
- **성공 직후 수동 백업** 습관화 필요

---

## [2026-04-22] — 볼트 자동 인덱싱 (launchd, 폐기됨)

> ⚠️ 이 접근법은 위 사고로 폐기됨. 기록용으로만 남김.

### Added (신규, 폐기됨)

- ~~`palantir/obsidian-mcp-server/com.user.obsidian-indexer.plist`~~ — macOS launchd 에이전트 (30분 주기 자동 증분 인덱싱)
- `palantir/obsidian-mcp-server/auto_index.sh` — 자동 실행 스크립트 (중복 방지 + 로그 로테이션)

### 왜 구축했나

기존엔 `.md` 새로 만들거나 수정해도 수동으로 `indexer.py` 돌려야 검색에 반영됐음. GBrain(제거됨)의 파일 워처 기능 대체 필요. launchd 기반 30분 스케줄로 해결.

### 특징

- `LowPriorityIO=true` + `ProcessType=Background`로 작업 중에도 시스템 영향 최소
- `pgrep`으로 중복 실행 방지 (수동 `indexer.py`와 충돌 방지)
- 변경 없으면 0.1초에 종료 (저부하)
- 로그 10MB 초과 시 자동 축약
- `RunAtLoad=false`로 로그인 직후 실행 안 함 (부팅 부하 방지)

### 설치 방법

```bash
# plist 배치
cp com.user.obsidian-indexer.plist ~/Library/LaunchAgents/
chmod +x auto_index.sh

# 활성화
launchctl load ~/Library/LaunchAgents/com.user.obsidian-indexer.plist

# 확인
launchctl list | grep obsidian-indexer
```

---

## [2026-04-22] — Palantir Scenario B Phase 1 (마크다운 헤더 청킹)

### Changed (변경)

- `palantir/obsidian-mcp-server/indexer.py`: **1파일 = 1벡터 → 마크다운 헤더 청킹**
  - `langchain_text_splitters.MarkdownHeaderTextSplitter` (H1/H2/H3) + `RecursiveCharacterTextSplitter` (800/100 overlap)
  - 청크당 최대 ~1200자. 200자 미만은 이웃과 병합.
  - **기존 MAX_NOTE_CHARS=3000 제한 제거** — 대형 파일 tail 유실 문제 완전 해결.
  - 스키마 확장: `chunk_id`, `chunk_index` 추가. `path`는 소스 파일 경로로 유지 (safe_delete 호환).
  - 인덱싱 환경변수 `OMP_NUM_THREADS=4` 등 강제 (M1 PyTorch의 torch.set_num_threads 미효력 보완).
  - `EMBEDDING_BATCH_SIZE=8 → 32` (4-thread 환경 throughput 확보).

- `palantir/obsidian-mcp-server/search.py`: **청크 단위 검색 + dedup**
  - 벡터 검색 후 `source_path` 기준 중복 제거. 파일당 최고 점수 청크 1개만 반환.
  - `FETCH_MULTIPLIER=20 → 30` (청킹으로 후보 풀 확대).
  - 출력에 `chunk_id`, `chunk_index` 노출 (어느 섹션이 매칭됐는지 표시).

### Added (신규)

- `palantir/obsidian-mcp-server/RESUME_AT_HOME.md`: Phase 1 재개 가이드 (전체 재인덱싱 ~1h 45m, 4-thread 환경변수 + caffeinate 활용).

### 왜 이 변경이 필요했나

- **기존 문제**: `MAX_NOTE_CHARS=3000`으로 대형 파일의 뒷부분 99%가 유실됨. 예) 픽업 자료 1.2MB의 0.3%만 인덱싱됨. 긴 인용문이나 파일 중반 이후 내용 검색 불가.
- **해결**: 헤더 기준 청킹으로 파일 전체를 섹션 단위로 쪼개 각각 임베딩. 같은 파일의 여러 섹션이 독립 검색 단위가 됨.

### 결과 (12 쿼리 A/B/C/D 타입 벤치마크)

| 지표 | 기준선 (Scenario A) | Phase 1 | 델타 |
|------|:---:|:---:|:---:|
| P@1 | 5/12 (41.7%) | **7/12 (58.3%)** | +2 |
| P@5 | 6/12 (50%) | **9/12 (75%)** | +3 |
| MRR | 0.458 | **0.642** | +0.184 |

- **B타입 (긴 인용문)**: P@5 0/3 → **3/3** (핵심 성과)
- **D타입 (파일 tail)**: 라벨링 오류 발견 — Phase 1이 잘 작동해서 원자화된 개념/기법 노트를 소스 파일보다 더 정확히 매칭

### 주의사항

- 검색 시 CPU는 **1 thread 유지** (발열 방지). 인덱싱만 4-thread.
- M1 Apple Silicon에서 PyTorch CPU는 환경변수 설정해도 실질 ~1.5~2 thread만 활용됨 (Accelerate BLAS 한계).
- 전체 재인덱싱은 1회성 비용. 증분 인덱싱은 그대로 30초~2분 유지.

---

## [2026-04-17] — Ground Truth 12차 반영

### Added (신규)

- `guides/02-second-brain.md`에 **Zettelkasten 4규칙** 섹션 추가
  - 원자성 · 연결 필수 · 자기 언어 · **링크 컨텍스트**(신규 4번째 규칙)
  - 링크 컨텍스트: 단순 `[[ ]]` 링크가 아니라 "왜 연결했는지" 한 줄 표기. 1년 뒤 이유 망각 방지 + 설명 자체가 새 인사이트 생성
- `guides/02-second-brain.md`에 **루만 넘버링 4단계 깊이 제한** 섹션 추가
  - 최대 `HU1B-1a-1`까지. 5단계 필요 시 새 번호 줄기로 분기
  - 근거: 루만 원본도 3~4단계에 머무름. 깊어지면 번호가 검색·대조 도구로서 기능 상실
- `guides/02-second-brain.md`에 **과잉 수집 신호(Collector's Fallacy) 섹션** 신설
  - 점검 신호 3가지(하루 Resources 3개+ 쌓이는데 L2 볼드 0, 2주 연속 Slip-Box 승격 없음, 유사 노트 존재시 신규 생성)
  - 방어책 4가지("왜 남겼는가" 강제 기입, Output 중심 사고, 수집 필터 상향, 12 활성 질문법)
- `guides/02-second-brain.md`에 **Obsidian × AI 함정 7가지** 섹션 신설 (Part 2.8)
  - 1. 컨텍스트 윈도우 ≠ 볼트 전체
  - 2. CLAUDE.md 드리프트
  - 3. 볼트 오염
  - 4. Instruction Attenuation (명령 감쇠)
  - 5. 수집 강박 (Collector's Fallacy)
  - 6. Task Drift (자의적 확장)
  - 7. 시스템 구축이 목적화
  - 각 함정의 원인·증상·극복 전략 요약표 포함

### Changed (변경)

- `guides/02-second-brain.md` — **Intermediate Packets (IP)** 부가 팁에서 **중심 원칙**으로 승격
  - "세션당 IP 1개 완성" 규칙 명문화
  - "영상 1개 = IP 8개" 예시 추가
  - Slow Burns 방식과의 연결 설명 강화
- 카테고리 접두어 표기 예시를 HU(인간)/CU(문화)/NA(자연)/GR(잠재성)/LR(삶의 법칙)로 전환
  - 중립적이고 범용적인 분류 제시
- CODE ↔ ARC 파이프라인 매핑 섹션에 Relate 단계 구체 흐름 5단계 추가

### Fixed (수정)

- 기존 "제텔카스텐 3원칙"을 "4규칙"으로 확장 (Zettelkasten.de 정식 원칙 반영)
- 루만 넘버링 운용에 깊이 제한 명문화로 "무한히 깊어지는 번호" 문제 방지

### Notes

- 본 릴리즈는 실전 운영 1년의 시행착오와 Obsidian × AI 통합 운영에서 관찰된 7가지 구조적 함정을 반영한 대규모 개편입니다.
- 기존 독자는 추가된 Part 1의 7~9번 섹션과 Part 2의 8번 섹션을 우선 확인하시는 것을 권장합니다.

---

## [초기 릴리즈] — AI Blueprint 2030 3부작 공개

- `guides/01-ai-compass.md` — AI 시대 나침반
- `guides/02-second-brain.md` — 세컨드 브레인 구축 가이드
- `guides/03-personal-palantir.md` — 개인용 팔란티어 구축 가이드
- `palantir/` — 팔란티어 기술 구축 문서 (백업, MCP 서버, 나이틀리 시냅스, 텔레그램 파이프라인, 셋업 스크립트 등)

---

## 업데이트 정책

- **major**: 가이드 전체 구조 변경
- **minor**: 섹션 신규 추가·대규모 개편
- **patch**: 오탈자·작은 내용 수정

각 릴리즈는 `guides/` 또는 `palantir/` 문서에 반영되며, 독자는 문서 상단 "마지막 갱신" 날짜로 현재 버전을 확인할 수 있습니다.
