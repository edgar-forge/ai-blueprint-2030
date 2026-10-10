#!/bin/bash
# =============================================================================
# AI Blueprint 2030 — 설치 스크립트 (세팅을 한 번에)
# =============================================================================
# 하는 일 셋:
#   1. vault-template/ 을 볼트로 복사한다 — 이미 있는 파일은 건드리지 않는다
#   2. 검색 서버(Python)를 ~/obsidian-mcp-server/ 에 설치하고 Claude Code에 등록한다
#   3. 첫 색인을 돌린다 (한국어 검색 모델 KURE-v1 약 2GB를 한 번 받는다)
#
# 쓰는 법 (저장소 루트에서):
#   bash palantir/setup.sh                          # 볼트 경로를 묻는다 (터미널에서 직접 돌릴 때)
#   bash palantir/setup.sh "$HOME/Documents/내 볼트"  # 볼트 경로를 첫 인자로
#   VAULT_PATH="$HOME/Documents/내 볼트" bash palantir/setup.sh   # 환경 변수로
#   키보드 입력이 없으면(Claude Code가 돌릴 때) 묻지 않는다. 인자도 환경 변수도 없으면
#   기본값 ~/Documents/Obsidian Vault 를 쓴다.
#   OVERWRITE_SERVER=1 이면 이미 있는 검색 서버 파일을 묻지 않고 덮어쓴다(.bak_날짜 를 남김).
#
# Claude Code 등록은 claude mcp add --scope user 로 한다(설정은 ~/.claude.json 에 들어간다).
# claude 명령이 없으면 등록 명령만 보여 주고 끝낸다.
#
# 만들지 않는 것: 상주 작업(launchd · cron). 색인은 VSCode로 볼트를 열 때 한 번 돈다.
# =============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "${BLUE}[정보]${NC}  $1"; }
success() { echo -e "${GREEN}[완료]${NC}  $1"; }
warn()    { echo -e "${YELLOW}[주의]${NC}  $1"; }
error()   { echo -e "${RED}[오류]${NC}  $1"; }
step()    { echo -e "\n${BOLD}==> $1${NC}"; }
die()     { error "$1"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_MCP_DIR="${SCRIPT_DIR}/obsidian-mcp-server"
REPO_TEMPLATE_DIR="${REPO_DIR}/vault-template"
HOME_DIR="$HOME"

# ---------------------------------------------------------------------------
# 0. 볼트 경로
# ---------------------------------------------------------------------------
step "0. 볼트 경로"
DEFAULT_VAULT="${HOME_DIR}/Documents/Obsidian Vault"
INPUT_VAULT="${1:-${VAULT_PATH:-}}"
if [ -z "$INPUT_VAULT" ]; then
    if [ -t 0 ]; then
        read -r -p "Obsidian 볼트 경로 [${DEFAULT_VAULT}]: " INPUT_VAULT || INPUT_VAULT=""
    else
        info "키보드 입력이 없어서 묻지 않는다. 볼트 경로를 바꾸려면 첫 인자나 VAULT_PATH 로 준다."
    fi
fi
VAULT_PATH="${INPUT_VAULT:-$DEFAULT_VAULT}"
VAULT_PATH="${VAULT_PATH/#\~/$HOME_DIR}"
if [ ! -d "$VAULT_PATH" ]; then
    mkdir -p "$VAULT_PATH"
    success "볼트 폴더를 만들었다: ${VAULT_PATH}"
else
    success "볼트 폴더: ${VAULT_PATH}"
fi

# ---------------------------------------------------------------------------
# 1. 볼트 틀 복사 — 없는 것만
# ---------------------------------------------------------------------------
step "1. 볼트 틀 복사 (이미 있는 파일은 건너뜀)"
[ -d "$REPO_TEMPLATE_DIR" ] || die "vault-template/ 이 없다: ${REPO_TEMPLATE_DIR}"
COPIED=0; SKIPPED=0
while IFS= read -r -d '' src; do
    rel="${src#"$REPO_TEMPLATE_DIR"/}"
    dst="${VAULT_PATH}/${rel}"
    if [ -e "$dst" ]; then
        SKIPPED=$((SKIPPED + 1))
    else
        mkdir -p "$(dirname "$dst")"
        cp "$src" "$dst"
        COPIED=$((COPIED + 1))
    fi
done < <(find "$REPO_TEMPLATE_DIR" -type f -print0)
success "복사 ${COPIED}개 · 이미 있어서 건너뜀 ${SKIPPED}개"

# ---------------------------------------------------------------------------
# 2. 필요한 것 확인
# ---------------------------------------------------------------------------
step "2. 필요한 것 확인"
command -v python3 &>/dev/null || die "python3가 없다. https://www.python.org/downloads/ 에서 3.9 이상을 설치한다."
PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=${PY_VERSION%%.*}; PY_MINOR=${PY_VERSION##*.}
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 9 ]; }; then
    die "Python 3.9 이상이 필요하다. 지금: ${PY_VERSION}"
fi
success "python3 ${PY_VERSION}"
if command -v claude &>/dev/null; then
    success "claude CLI: $(command -v claude)"
else
    warn "claude CLI가 없다. 검색 서버는 설치되지만 Claude Code가 있어야 쓸 수 있다: https://docs.anthropic.com/en/docs/claude-code"
fi

# ---------------------------------------------------------------------------
# 3. 검색 서버 설치
# ---------------------------------------------------------------------------
step "3. 검색 서버 설치 → ~/obsidian-mcp-server/"
[ -d "$REPO_MCP_DIR" ] || die "소스 폴더가 없다: ${REPO_MCP_DIR}"
MCP_DEST="${HOME_DIR}/obsidian-mcp-server"
mkdir -p "$MCP_DEST"
# 이미 검색 서버가 있으면(= 전에 설치했거나 직접 고쳐 쓰는 중) 덮어쓰기 전에 묻고, 덮어쓸 때는 백업을 남긴다
if [ -f "${MCP_DEST}/server.py" ]; then
    warn "~/obsidian-mcp-server/ 에 이미 서버 파일이 있다. 직접 고쳐 쓰는 중이면 덮어쓰지 않는 게 맞다."
    OVERWRITE="${OVERWRITE_SERVER:-}"
    [ "$OVERWRITE" = "1" ] && OVERWRITE="y"
    if [ -z "$OVERWRITE" ] && [ -t 0 ]; then
        read -r -p "저장소 판으로 덮어쓸까? 덮어쓰면 기존 파일은 .bak_날짜 로 남긴다 (y/N): " OVERWRITE || OVERWRITE=""
    fi
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        info "서버 파일은 그대로 둔다. 4단계(등록)와 5단계(색인)만 진행한다."
        SKIP_COPY=1
    fi
fi
STAMP=$(date +%Y%m%d_%H%M%S)
VAULT_SED=$(printf '%s' "$VAULT_PATH" | sed -e 's/[\\|&]/\\&/g')
for f in "$REPO_MCP_DIR"/*.py "$REPO_MCP_DIR"/*.sh; do
    [ -f "$f" ] || continue
    [ "${SKIP_COPY:-0}" = "1" ] && break
    base=$(basename "$f")
    [ -f "${MCP_DEST}/${base}" ] && cp "${MCP_DEST}/${base}" "${MCP_DEST}/${base}.bak_${STAMP}"
    sed -e "s|/path/to/your/obsidian-vault|${VAULT_SED}|g" "$f" > "${MCP_DEST}/${base}"
    [ "${base##*.}" = "sh" ] && chmod +x "${MCP_DEST}/${base}"
    success "복사 ${base}"
done
if [ ! -d "${MCP_DEST}/venv" ]; then
    info "Python 가상환경을 만든다..."
    python3 -m venv "${MCP_DEST}/venv"
    success "가상환경 생성"
else
    warn "가상환경이 이미 있다 — 그대로 쓴다"
fi
info "Python 패키지를 설치한다 (몇 분 걸린다)..."
"${MCP_DEST}/venv/bin/pip" install --upgrade pip --quiet
"${MCP_DEST}/venv/bin/pip" install sentence-transformers lancedb langchain-text-splitters "mcp[cli]" --quiet
success "패키지 설치"

# ---------------------------------------------------------------------------
# 4. Claude Code에 등록
# ---------------------------------------------------------------------------
step "4. Claude Code에 검색 서버 등록 (claude mcp add, 사용자 범위)"
MCP_PY="${MCP_DEST}/venv/bin/python"
MCP_SERVER="${MCP_DEST}/server.py"
REGISTER_CMD="claude mcp add -e VAULT_PATH=\"${VAULT_PATH}\" --scope user --transport stdio obsidian-search -- \"${MCP_PY}\" \"${MCP_SERVER}\""
REGISTERED="안 함"
if command -v claude &>/dev/null; then
    if claude mcp get obsidian-search &>/dev/null; then
        warn "obsidian-search 가 이미 등록돼 있다 — 건드리지 않는다. 다시 등록하려면:"
        echo "    claude mcp remove obsidian-search --scope user"
        echo "    ${REGISTER_CMD}"
        REGISTERED="이미 있음"
    elif claude mcp add -e VAULT_PATH="${VAULT_PATH}" --scope user --transport stdio obsidian-search -- "${MCP_PY}" "${MCP_SERVER}"; then
        success "등록: obsidian-search (사용자 범위, ~/.claude.json)"
        REGISTERED="함"
    else
        warn "등록이 실패했다. 터미널에 이 한 줄을 붙여 넣는다:"
        echo "    ${REGISTER_CMD}"
    fi
else
    warn "claude 명령이 없어서 등록하지 않았다. Claude Code를 설치한 뒤 터미널에 이 한 줄을 붙여 넣는다:"
    echo "    ${REGISTER_CMD}"
fi

# ---------------------------------------------------------------------------
# 5. 첫 색인
# ---------------------------------------------------------------------------
step "5. 첫 색인 (한국어 검색 모델 KURE-v1 약 2GB를 한 번 받는다)"
if VAULT_PATH="$VAULT_PATH" "${MCP_DEST}/venv/bin/python" "${MCP_DEST}/indexer.py" --full; then
    success "첫 색인 완료"
else
    warn "색인이 실패했다. 나중에 손으로: cd ~/obsidian-mcp-server && VAULT_PATH=\"${VAULT_PATH}\" ./venv/bin/python indexer.py --full"
fi

# ---------------------------------------------------------------------------
# 끝
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}============================================${NC}"
echo -e "${GREEN}${BOLD}  설치 끝${NC}"
echo -e "${BOLD}============================================${NC}"
echo ""
echo "  볼트            ${VAULT_PATH}"
echo "  검색 서버       ~/obsidian-mcp-server/"
echo "  Claude 등록     ${REGISTERED} — 확인: claude mcp list"
echo ""
echo -e "${BOLD}다음:${NC}"
echo "  1. Claude Code를 껐다 켠다"
echo "  2. 물어 본다: 「내 노트에서 ○○ 찾아줘」"
echo "  3. 색인은 VSCode로 볼트를 열 때 한 번 돈다 (손으로: ~/obsidian-mcp-server/auto_index.sh)"
echo ""
