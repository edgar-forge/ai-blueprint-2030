# 검색 — 내 노트를 뜻으로 찾습니다

노트가 쌓이면 제목으로는 못 찾습니다. 이 검색 엔진은 노트를 **뜻**으로 찾습니다. 「결정을 미루는 이유」라고 물으면 그 말이 한 글자도 없는 노트도 나옵니다. 전부 내 컴퓨터 안에서 돌고, 노트가 인터넷으로 나가지 않습니다.

## 무엇이 설치되나

| 것 | 자리 | 하는 일 |
|---|---|---|
| 검색 서버 | `~/obsidian-mcp-server/` | 노트를 숫자(임베딩, KURE-v1)로 바꿔 LanceDB에 저장하고, Claude에게 `search_notes` 도구를 준다 |
| Python 환경 | `~/obsidian-mcp-server/venv/` | 시스템 파이썬과 분리된 설치 자리 |
| Claude 등록 | `~/.claude.json` (`claude mcp add --scope user`로 넣는다) | Claude Code가 어느 폴더에서 열려도 검색 서버를 알게 한다 |

## 설치 — 한 명령

맥(macOS) 전용입니다. 윈도우에서는 이 스크립트가 돌지 않습니다.

```bash
bash palantir/setup.sh                              # 볼트 경로를 묻는다
bash palantir/setup.sh "$HOME/Documents/내 볼트"      # 볼트 경로를 첫 인자로
VAULT_PATH="$HOME/Documents/내 볼트" bash palantir/setup.sh   # 환경 변수로
```

볼트 경로는 첫 인자 → 환경 변수 `VAULT_PATH` → 질문 순서로 정합니다. 터미널에서 직접 돌리면 묻고, Claude Code가 돌릴 때처럼 키보드 입력이 없으면 묻지 않고 기본값 `~/Documents/Obsidian Vault`를 씁니다. `~/obsidian-mcp-server/`에 서버 파일이 이미 있으면 덮어쓸지 묻고(기본은 아니오), 키보드가 없으면 그대로 둡니다. 묻지 않고 덮어쓰려면 `OVERWRITE_SERVER=1`을 붙입니다 — 기존 파일은 `.bak_날짜`로 남습니다.

등록은 `claude` 명령으로 합니다. 스크립트가 돌리는 한 줄은 이 꼴입니다.

```bash
claude mcp add -e VAULT_PATH="<볼트 경로>" --scope user --transport stdio obsidian-search -- ~/obsidian-mcp-server/venv/bin/python ~/obsidian-mcp-server/server.py
```

`obsidian-search`가 이미 등록돼 있으면 건드리지 않습니다. `claude` 명령이 없으면 등록하지 않고 이 한 줄을 화면에 보여 줍니다 — Claude Code를 설치한 뒤 터미널에 붙여 넣으면 됩니다. 등록됐는지는 `claude mcp list`로 봅니다.

첫 색인에서 한국어 검색 모델(KURE-v1) 약 2GB를 한 번 받으니 10~20분쯤 걸립니다. 끝나면 Claude Code를 껐다 켭니다. 그리고 이렇게 물어 보세요.

```
내 노트에서 결정을 미루는 이유를 찾아줘
```

Claude가 `search_notes`를 부르고 내 노트로 답합니다.

## 색인은 언제 갱신되나

VSCode로 볼트 폴더를 열 때 한 번 돕니다 — `vault-template/.vscode/tasks.json`이 `auto_index.sh`를 부릅니다. 바뀐 노트만 다시 읽으니 보통 몇 초입니다. 손으로 돌리려면:

```bash
~/obsidian-mcp-server/auto_index.sh
```

검색 기록은 기본으로 남기지 않습니다. 남기고 싶으면 등록할 때 `-e OBSIDIAN_SEARCH_LOG=1`을 더합니다. 그러면 질문과 상위 5개가 `~/obsidian-mcp-server/logs/query_log.jsonl`에 쌓입니다.

30분마다 도는 상주 작업(launchd)은 일부러 없습니다. 2026년 4월에 그 방식이 색인을 통째로 비운 사고가 있었고(CHANGELOG 참고), 「볼트를 열 때 한 번」이면 충분했습니다.

## 막히면

| 증상 | 보통 원인 | 할 것 |
|---|---|---|
| Claude에 검색 도구가 안 보인다 | 재시작 안 함 · 등록 안 됨 | Claude Code 재시작, `claude mcp list`에 `obsidian-search`가 없으면 위 등록 한 줄 |
| 결과가 0개 | 색인이 한 번도 안 돎 | `cd ~/obsidian-mcp-server && ./venv/bin/python indexer.py --full` |
| 결과가 옛날 것 | 색인이 안 갱신됨 | 위 `auto_index.sh` 한 번 |
| 설치 중 pip 오류 | Python 3.9 미만 | `python3 --version` 확인 뒤 재설치 |

원리와 코드 전체는 [guides/03-personal-palantir.md](../guides/03-personal-palantir.md)에 있습니다. 설치만 필요하면 이 한 장으로 끝입니다.
