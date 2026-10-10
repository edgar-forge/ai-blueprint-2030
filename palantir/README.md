# palantir/ — 검색 엔진 소스와 설치 스크립트

`setup.sh` 하나가 셋을 합니다. 볼트 틀 복사(없는 것만) → 검색 서버 설치와 Claude Code 등록 → 첫 색인. 보통은 저장소 루트의 [START.md](../START.md)를 Claude Code에게 읽히면 이 스크립트까지 Claude가 돌립니다. 설치만 따로 하려면:

```bash
bash palantir/setup.sh                    # 볼트 경로를 묻는다
bash palantir/setup.sh "<볼트 경로>"       # 묻지 않고 바로 (환경 변수 VAULT_PATH 도 된다)
```

볼트 경로는 첫 인자 → `VAULT_PATH` → 질문 순서로 정하고, 키보드 입력이 없으면(Claude Code가 돌릴 때) 묻지 않고 기본값 `~/Documents/Obsidian Vault`를 씁니다. Claude Code 등록은 `claude mcp add --scope user`로 합니다 — `claude` 명령이 없으면 등록 한 줄을 화면에 보여 주고 끝냅니다. 맥(macOS) 전용이고 윈도우에서는 돌지 않습니다. 설명은 [검색/README.md](../검색/README.md).

## 필요한 것

| 것 | 확인 |
|---|---|
| Python 3.9+ | `python3 --version` |
| Claude Code | `claude --version` — 검색 서버를 쓰는 쪽 |
| Obsidian | 설치만. 볼트는 START가 만든다 |

Node.js · git · macOS LaunchAgents는 더 이상 필요 없습니다.

## 폴더

```
palantir/
  setup.sh                  설치 스크립트 — 하는 일 셋
  README.md                 이 파일
  obsidian-mcp-server/      검색 서버 소스 (indexer.py · search.py · server.py · auto_index.sh · bridge_keywords.py)
  backup/                   백업 · 동기화 스크립트 — 백업하고 싶은 사람만, 비공개 저장소로 (아래)
```

## 백업 · 동기화 — 백업하고 싶은 사람만, 비공개 저장소로

볼트를 GitHub에 올려 백업하고 싶은 사람만 씁니다. `sync_from_github.sh`는 볼트 전체를 자동으로 커밋해 올리니, 받는 저장소는 반드시 **비공개(Private)**로 만듭니다. 공개 저장소에 걸면 일기와 메모가 그대로 공개됩니다. `backup_vault.sh`는 볼트를 압축해 두고 7일 지난 압축본을 지웁니다.

`backup/`의 두 스크립트는 설치되지 않습니다. 쓰려면 `~/ObsidianBackup/`에 복사해 안의 경로를 고치고, VSCode `.vscode/tasks.json`의 folderOpen 작업으로 겁니다(`vault-template/.vscode/tasks.json`에 색인 작업이 같은 방식으로 들어 있으니 그 옆에 하나 더 두면 됩니다). 30분 주기 상주 작업은 두지 않습니다 — 2026년 4월 색인 사고와 2026년 9월 성능 문제로 만든 사람 본인도 걷어냈습니다([CHANGELOG](../CHANGELOG.md)).

## 막히면

[검색/README.md](../검색/README.md)의 「막히면」 표, 그래도 안 되면 [Issues](../../../issues/new?template=%EC%A7%88%EB%AC%B8.md).
