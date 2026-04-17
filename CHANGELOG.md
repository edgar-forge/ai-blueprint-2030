# Changelog

이 파일은 AI Blueprint 2030 가이드의 중요한 변경 사항을 기록합니다.

형식: [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/) 기반.

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
