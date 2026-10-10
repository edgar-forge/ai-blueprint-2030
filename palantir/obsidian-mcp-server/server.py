"""
옵시디언 노트 검색 MCP 서버
- Claude Code에서 도구(tool)로 사용 가능
- 질문을 받으면 관련 노트를 찾아서 반환
"""

import json
import os
from datetime import datetime

from mcp.server.fastmcp import FastMCP
from search import search, detect_query_bridge_keywords

VAULT_PATH = os.environ.get("VAULT_PATH", "/path/to/your/obsidian-vault")

# ─── 검색 로그 (기본 끔) ───
# 환경 변수 OBSIDIAN_SEARCH_LOG=1 일 때만 질의와 상위 5개를 이 파일 옆 logs/query_log.jsonl 에 남긴다.
LOG_ENABLED = os.environ.get("OBSIDIAN_SEARCH_LOG", "") == "1"
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
QUERY_LOG_PATH = os.path.join(LOG_DIR, "query_log.jsonl")
LOG_TOP_COUNT = 5

# MCP 서버 생성
mcp = FastMCP("obsidian-search")


def log_query(query: str, results: list) -> None:
    """검색 1회를 query_log.jsonl에 JSONL 한 줄로 append한다.

    OBSIDIAN_SEARCH_LOG=1 일 때만 남긴다(기본 끔).
    실패는 조용히 무시한다. 로깅은 검색 결과에 절대 영향을 주지 않는다.
    """
    if not LOG_ENABLED:
        return
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        record = {
            "ts": datetime.now().astimezone().isoformat(timespec="seconds"),
            "query": query,
            "top": [
                {"path": r.get("path"), "score": r.get("score")}
                for r in results[:LOG_TOP_COUNT]
            ],
            "n": len(results),
        }
        with open(QUERY_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


@mcp.tool()
def search_notes(query: str, top_k: int = 5) -> str:
    """
    옵시디언 볼트에서 질문과 관련된 노트를 검색합니다.

    점수 계산: 벡터유사도 + 제목보너스 + 브릿지키워드보너스 + 폴더보너스 (가산·감산 혼합)
    - 폴더 가중치는 점수에 반영하지 않는다 (Slip-Box, Project 보너스 0.0)
    - 4. Archives 경로는 0.5 감점
    - 파일명이 질문과 글자로 겹치는 만큼 최대 +0.15
    - 0. Slip-Box/개념/ 노트는 +0.05
    - 브릿지 키워드 보너스는 0 (꺼 둠)

    Args:
        query: 검색할 질문 (예: "내 업의 본질", "습관을 만드는 방법")
        top_k: 반환할 노트 수 (기본 5개, 최대 20개)
    """
    query = query.strip()
    if not query:
        return "검색어를 입력해주세요."

    top_k = min(max(top_k, 1), 20)
    results = search(query, top_k=top_k)
    log_query(query, results)

    if not results:
        return "관련 노트를 찾지 못했습니다."

    # 쿼리에서 감지된 브릿지 키워드
    query_kws = detect_query_bridge_keywords(query)

    lines = []
    lines.append(f"🔍 \"{query}\" 검색 결과 ({len(results)}개)")
    if query_kws:
        lines.append(f"감지된 브릿지 키워드: {', '.join(query_kws)}")
    lines.append("")

    for i, r in enumerate(results, 1):
        d = r["_detail"]
        tags = []
        if d["folder_weight"] == 3.0:
            tags.append("⭐Slip-Box")
        elif d["folder_weight"] == 2.0:
            tags.append("📁Project")
        if d["title_bonus"] > 0:
            tags.append("📌제목매칭")
        if d["bridge_overlap"] > 0:
            tags.append(f"🔗브릿지×{d['bridge_overlap']}")
        tag_str = " ".join(tags)

        lines.append(f"## {i}. [{r['score']:.4f}] {r['filename']}")
        lines.append(f"경로: {r['path']}")
        if tag_str:
            lines.append(tag_str)
        lines.append("")
        # 본문 미리보기 (앞 500자)
        preview = r["text"][:500].replace("\n", " ").strip()
        lines.append(f"> {preview}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
def get_note(path: str) -> str:
    """
    옵시디언 노트의 전체 내용을 읽어옵니다.
    search_notes로 찾은 노트의 경로(path)를 넣으면 전문을 반환합니다.

    Args:
        path: 노트 경로 (예: "0. Slip-Box/철학/P1_본질/P1A — 본질에 대한 생각.md")
    """
    path = path.strip()
    if not path:
        return "파일 경로를 입력해주세요."

    full_path = os.path.realpath(os.path.join(VAULT_PATH, path))

    if not full_path.startswith(os.path.realpath(VAULT_PATH)):
        return "볼트 외부 파일에는 접근할 수 없습니다."

    if not os.path.exists(full_path):
        return f"파일을 찾을 수 없습니다: {path}"

    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    return f"📄 {path}\n\n{content}"


if __name__ == "__main__":
    mcp.run()
