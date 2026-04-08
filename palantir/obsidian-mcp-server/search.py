"""
4-가중치 검색 엔진
- 벡터 유사도 (코사인)
- 제목 매칭 보너스 (+0.3)
- 브릿지 키워드 보너스 (키워드당 +0.15, 최대 +0.45)
- 폴더 가중치 배수 (Slip-Box: x3, Project: x2, 기타: x1)
"""

import os
import lancedb
from sentence_transformers import SentenceTransformer
from bridge_keywords import BRIDGE_KEYWORDS

DB_PATH = os.path.expanduser("~/obsidian-mcp-server/vault.lancedb")
TABLE_NAME = "notes"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

TITLE_MATCH_BONUS = 0.3
BRIDGE_KEYWORD_BONUS = 0.15
MAX_BRIDGE_BONUS = 0.45

_model = None
_table = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _get_table():
    global _table
    if _table is None:
        db = lancedb.connect(DB_PATH)
        _table = db.open_table(TABLE_NAME)
    return _table


def detect_query_bridge_keywords(query: str) -> list[str]:
    query_lower = query.lower()
    matched = []
    for kw_name, signals in BRIDGE_KEYWORDS.items():
        for signal in signals:
            if signal.lower() in query_lower:
                matched.append(kw_name)
                break
    return matched


def search(query: str, top_k: int = 10) -> list[dict]:
    model = _get_model()
    table = _get_table()

    query_vector = model.encode(query).tolist()
    candidates = (
        table.search(query_vector)
        .limit(top_k * 3)
        .to_list()
    )

    query_lower = query.lower()
    query_bridge_kws = detect_query_bridge_keywords(query)

    results = []
    for row in candidates:
        base_score = 1.0 - row.get("_distance", 0.0)

        title_bonus = 0.0
        filename = row.get("filename", "")
        if query_lower in filename.lower():
            title_bonus = TITLE_MATCH_BONUS

        bridge_bonus = 0.0
        note_bridge_kws = row.get("bridge_keywords", "")
        if note_bridge_kws and query_bridge_kws:
            note_kw_set = set(note_bridge_kws.split(","))
            matched_count = len(set(query_bridge_kws) & note_kw_set)
            bridge_bonus = min(
                matched_count * BRIDGE_KEYWORD_BONUS,
                MAX_BRIDGE_BONUS,
            )

        folder_weight = row.get("weight", 1.0)

        final_score = (base_score + title_bonus + bridge_bonus) * folder_weight

        results.append({
            "filename": filename,
            "path": row.get("path", ""),
            "text": row.get("text", "")[:500],
            "score": round(final_score, 4),
            "bridge_keywords": note_bridge_kws,
            "weight": folder_weight,
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    import sys

    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "시스템 사고와 의사결정"
    print(f"검색어: {query}\n")

    results = search(query, top_k=5)
    for i, r in enumerate(results, 1):
        print(f"[{i}] {r['filename']}  (score: {r['score']})")
        print(f"    경로: {r['path']}")
        print(f"    브릿지: {r['bridge_keywords']}")
        print(f"    가중치: {r['weight']}")
        print(f"    내용: {r['text'][:100]}...")
        print()
