#!/usr/bin/env bash
# install_plugins.sh — 옵시디언 커뮤니티 플러그인을 공식 배포 주소에서 받아 볼트에 넣는다.
#
# 쓰는 법:  bash palantir/install_plugins.sh "<볼트 경로>" [--with-importer]
#   - 받는 것: Calendar · Periodic Notes · Smart Typography (그리고 --with-importer 를 주면 Importer까지)
#   - 자리:   <볼트>/.obsidian/plugins/<플러그인 id>/  (manifest.json · main.js, 있으면 styles.css)
#   - 받는 판: 옵시디언이 플러그인을 깔 때와 같다. 각 저장소 기본 가지의 manifest.json에 적힌 판 번호를 읽고,
#             그 번호의 GitHub 배포 파일을 받는다. (가장 최근 배포가 베타일 때 베타를 받지 않으려고)
#   - 이미 main.js 가 있는 플러그인은 건드리지 않는다. data.json(설정값)은 절대 덮어쓰지 않는다.
#   - 받은 뒤 옵시디언에서 볼트를 처음 열면 "이 보관함의 작성자를 신뢰하시나요?" 창이 뜬다.
#     "작성자를 신뢰하고 플러그인 사용하기"를 누르면 켜진다.
#
# 맥 · 리눅스 · WSL 의 bash 에서 돈다. curl 이 있어야 한다.

set -euo pipefail

VAULT="${1:-${VAULT_PATH:-}}"
WITH_IMPORTER=0
for a in "$@"; do [ "$a" = "--with-importer" ] && WITH_IMPORTER=1; done

if [ -z "$VAULT" ] || [ "$VAULT" = "--with-importer" ]; then
  echo "볼트 경로를 첫 인자로 주세요.  예) bash palantir/install_plugins.sh \"\$HOME/Documents/Obsidian Vault\"" >&2
  exit 2
fi
if [ ! -d "$VAULT" ]; then
  echo "볼트 폴더가 없습니다: $VAULT" >&2
  exit 2
fi
command -v curl >/dev/null 2>&1 || { echo "curl 이 없습니다. 설치한 뒤 다시 실행하세요." >&2; exit 2; }

PLUG="$VAULT/.obsidian/plugins"
mkdir -p "$PLUG"

# manifest.json 에서 키 하나의 값을 꺼낸다(파이썬 없이).
jget() { sed -n "s/.*\"$1\"[[:space:]]*:[[:space:]]*\"\([^\"]*\)\".*/\1/p" | head -1; }

# id | GitHub 저장소 — 옵시디언 공식 플러그인 목록(community-plugins.json)과 같은 짝
PLUGINS=(
  "calendar|liamcain/obsidian-calendar-plugin"
  "periodic-notes|liamcain/obsidian-periodic-notes"
  "obsidian-smart-typography|mgmeyers/obsidian-smart-typography"
)
if [ "$WITH_IMPORTER" = "1" ]; then
  PLUGINS+=("obsidian-importer|obsidianmd/obsidian-importer")
fi

ok=0; skipped=0; failed=0
for entry in "${PLUGINS[@]}"; do
  id="${entry%%|*}"; repo="${entry#*|}"
  dir="$PLUG/$id"
  if [ -f "$dir/main.js" ]; then
    echo "건너뜀  $id — 이미 설치돼 있음"
    skipped=$((skipped+1)); continue
  fi
  # 옵시디언과 같은 판: 기본 가지의 manifest.json
  if ! head_manifest=$(curl -fsSL --retry 2 "https://raw.githubusercontent.com/$repo/HEAD/manifest.json"); then
    echo "실패    $id — 판 번호를 읽지 못했습니다 ($repo)" >&2
    failed=$((failed+1)); continue
  fi
  mid=$(printf '%s\n' "$head_manifest" | jget id)
  ver=$(printf '%s\n' "$head_manifest" | jget version)
  if [ -z "$ver" ]; then
    echo "실패    $id — 판 번호를 읽지 못했습니다. 옵시디언에서 직접 설치하세요." >&2
    failed=$((failed+1)); continue
  fi
  if [ "$mid" != "$id" ]; then
    echo "실패    $id — 저장소의 플러그인 이름이 다릅니다(${mid:-없음}). 옵시디언에서 직접 설치하세요." >&2
    failed=$((failed+1)); continue
  fi
  mkdir -p "$dir"
  good=1
  base="https://github.com/$repo/releases/download/$ver"
  for f in manifest.json main.js; do
    if ! curl -fsSL --retry 2 -o "$dir/$f" "$base/$f"; then
      echo "실패    $id — $f 를 받지 못했습니다 ($base/$f)" >&2
      good=0; break
    fi
  done
  # styles.css 는 없는 플러그인도 있다(옵시디언도 없으면 넘어간다).
  if [ "$good" = "1" ] && ! curl -fsSL --retry 2 -o "$dir/styles.css" "$base/styles.css" 2>/dev/null; then
    rm -f "$dir/styles.css"
  fi
  if [ "$good" = "1" ]; then
    got=$(jget id < "$dir/manifest.json")
    if [ "$got" != "$id" ]; then
      echo "실패    $id — 받은 파일의 플러그인 이름이 다릅니다($got)" >&2
      good=0
    fi
  fi
  if [ "$good" = "1" ]; then
    echo "설치    $id (v$ver)"
    ok=$((ok+1))
  else
    rm -f "$dir/main.js" "$dir/manifest.json" "$dir/styles.css"
    failed=$((failed+1))
  fi
done

# 켜 둘 목록(community-plugins.json)이 없으면 만든다 — 있는 목록은 그대로 둔다.
CP="$VAULT/.obsidian/community-plugins.json"
if [ ! -f "$CP" ]; then
  printf '[\n  "calendar",\n  "periodic-notes",\n  "obsidian-smart-typography"\n]\n' > "$CP"
fi
if [ "$WITH_IMPORTER" = "1" ] && ! grep -q '"obsidian-importer"' "$CP"; then
  # 목록을 통째로 다시 쓴다(파이썬 없이). 있는 이름은 그대로, 끝에 하나를 더한다.
  ids=$( { grep -o '"[^"]*"' "$CP" || true; echo '"obsidian-importer"'; } | sed '/^$/d')
  { echo "["; printf '%s\n' "$ids" | sed 's/^/  /' | sed '$!s/$/,/'; echo "]"; } > "$CP.tmp" && mv "$CP.tmp" "$CP"
fi

echo "---"
echo "플러그인: 설치 $ok · 이미 있음 $skipped · 실패 $failed"
if [ "$failed" != "0" ]; then
  echo "실패한 것은 옵시디언에서 직접 설치하면 됩니다 — 설정 → 커뮤니티 플러그인 → 탐색 → 이름 검색 → 설치 → 활성화." >&2
  exit 1
fi
echo "옵시디언에서 볼트를 처음 열면 \"이 보관함의 작성자를 신뢰하시나요?\" 창이 뜹니다. \"작성자를 신뢰하고 플러그인 사용하기\"를 누르면 플러그인이 켜집니다."
