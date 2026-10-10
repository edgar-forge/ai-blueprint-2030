# VS Code 세팅

VS Code는 글자 파일을 여는 작업대 프로그램입니다. 여기에 Claude Code 확장을 끼우면 볼트 폴더를 연 채로 옆 창에서 Claude와 이야기하며 노트를 읽고 쓰게 할 수 있습니다. 옵시디언은 노트를 쓰고 읽는 곳, VS Code는 Claude와 같이 일하는 곳입니다.

윈도우에서는 아래의 Cmd를 Ctrl로 읽으면 됩니다.

---

## 1. 설치

https://code.visualstudio.com 에서 내려받아 설치합니다.

---

## 2. 확장 둘

왼쪽 막대의 확장(Extensions) 아이콘을 누르고, 이름으로 찾아 설치(Install)를 누릅니다.

- **Claude Code** (만든 곳 Anthropic, ID `anthropic.claude-code`): VS Code 안에서 Claude를 불러 볼트 파일을 읽고 쓰게 합니다. 처음 쓸 때 Claude 계정 로그인을 묻습니다.
- **Korean Language Pack for Visual Studio Code** (만든 곳 Microsoft, ID `MS-CEINTL.vscode-language-pack-ko`): 메뉴를 한국어로 바꿉니다. 설치 뒤 다시 시작하라는 안내가 뜨면 따릅니다.

터미널이 익숙하면 두 줄로도 됩니다.

```bash
code --install-extension anthropic.claude-code
code --install-extension MS-CEINTL.vscode-language-pack-ko
```

`code` 명령이 없다고 나오면 VS Code에서 명령 팔레트(Cmd+Shift+P)를 열고 Shell Command: Install 'code' command in PATH를 한 번 실행합니다.

---

## 3. 볼트 폴더를 열면 Claude Code가 보인다

1. 파일 → 폴더 열기(Open Folder)로 볼트 폴더를 엽니다.
2. 이 폴더를 만든 사람을 신뢰하는지 물으면 신뢰한다를 고릅니다. 직접 만든 볼트라서 그렇게 해도 됩니다.
3. 화면에 생긴 Claude 아이콘을 누르거나, 명령 팔레트(Cmd+Shift+P)에 Claude Code를 쳐서 창을 엽니다.

Claude는 볼트에서 일을 시작할 때 볼트의 `CLAUDE.md`를 먼저 읽습니다. 그래서 볼트 폴더를 열고 Claude를 부르는 것이 기본 자세입니다.

---

## 4. 검색 엔진을 깐 사람만: 볼트를 열 때 색인

검색 엔진([검색 엔진.md](검색%20엔진.md))을 깔았다면 이 절을 봅니다. 깔지 않았다면 넘어가도 됩니다.

볼트 틀의 `.vscode/tasks.json`에는 작업이 하나 들어 있습니다. VS Code가 볼트 폴더를 열 때 한 번, 바뀐 노트만 골라 검색 엔진의 찾아보기 목록(색인)을 새로 만듭니다. 컴퓨터에 늘 떠 있는 자동 작업은 만들지 않습니다. 볼트를 열 때 한 번이면 충분합니다.

이 작업이 저절로 돌려면 VS Code에서 자동 작업이 허용돼 있어야 합니다. 설정(Cmd+,)에서 `task.allowAutomaticTasks`를 찾아 `on`으로 둡니다. 사용자 설정 파일(settings.json)에 직접 적는다면 아래 한 줄입니다.

```json
"task.allowAutomaticTasks": "on"
```

검색 엔진을 깔지 않은 채 이 값이 `on`이면, 작업이 실행할 스크립트를 찾지 못해 오류로 끝날 수 있습니다. 그럴 땐 `off`로 두면 됩니다.
