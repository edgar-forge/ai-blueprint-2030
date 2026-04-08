"""
Obsidian MCP 서버
- search_notes: 4-가중치 시맨틱 검색
- get_note: 노트 원문 반환 (볼트 경계 보안 체크 포함)
"""

import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from search import search

VAULT_PATH = "{VAULT_PATH}"

mcp = FastMCP(
    "obsidian-vault",
    instructions=(
        "옵시디언 볼트를 검색하고 노트를 읽는 MCP 서버입니다. "
        "search_notes로 시맨틱 검색, get_note로 노트 원문을 가져옵니다."
    ),
)


def _is_safe_path(note_path: str) -> bool:
    vault = Path(VAULT_PATH).resolve()
    target = (vault / note_path).resolve()
    return str(target).startswith(str(vault))


@mcp.tool()
def search_notes(query: str, top_k: int = 5) -> list[dict]:
    """
    옵시디언 볼트에서 시맨틱 검색을 수행합니다.

    Args:
        query: 검색어 (자연어)
        top_k: 반환할 최대 결과 수 (기본 5)

    Returns:
        검색 결과 리스트 (filename, path, text, score, bridge_keywords, weight)
    """
    if not query or not query.strip():
        return [{"error": "검색어를 입력해주세요."}]

    clamped_top_k = max(1, min(top_k, 20))
    results = search(query, top_k=clamped_top_k)
    return results


@mcp.tool()
def get_note(path: str) -> dict:
    """
    노트의 전체 원문을 반환합니다.

    Args:
        path: 볼트 루트 기준 상대 경로 (예: "0. Slip-Box/시스템_사고.md")

    Returns:
        노트 내용 또는 에러 메시지
    """
    if not path or not path.strip():
        return {"error": "경로를 입력해주세요."}

    if not _is_safe_path(path):
        return {"error": "접근이 허용되지 않는 경로입니다."}

    full_path = Path(VAULT_PATH) / path
    if not full_path.exists():
        return {"error": f"노트를 찾을 수 없습니다: {path}"}

    if not full_path.is_file():
        return {"error": f"파일이 아닙니다: {path}"}

    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"노트 읽기 실패: {str(e)}"}

    return {
        "path": path,
        "filename": full_path.stem,
        "content": content,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
