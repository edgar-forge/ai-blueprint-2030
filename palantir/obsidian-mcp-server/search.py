"""
옵시디언 노트 검색기 (Scenario B Phase 1 — 청킹 적용, 벡터 단독)
- LanceDB 벡터 검색 (본문 의미 기반) — 청크 단위
- source_path 기준 dedup (파일당 최고 점수 청크 1개)
- 파일명/제목 키워드 매칭 보너스
- 브릿지 키워드 겹침 보너스

최종 점수 = similarity + title_bonus + bridge_bonus
"""

import logging
import os

import lancedb
from sentence_transformers import SentenceTransformer
from bridge_keywords import BRIDGE_KEYWORDS

logger = logging.getLogger(__name__)

# ─── 설정 ───
DB_PATH = os.path.expanduser("~/obsidian-mcp-server/vault.lancedb")
TABLE_NAME = "notes"
EMBEDDING_MODEL = "nlpai-lab/KURE-v1"  # 1024D, 8192 토큰, MTEB-ko NDCG@5 0.6748 (1위)

# ─── 점수 가중치 ───
TITLE_MATCH_BONUS = 0.5
BRIDGE_KEYWORD_BONUS = 0.15
BRIDGE_KEYWORD_MAX_BONUS = 0.45
MIN_QUERY_WORD_LEN = 2

# ─── Fetch 설정 (청크 기반, 더 넓게 확보 후 dedup) ───
FETCH_MULTIPLIER = 30  # top_k의 몇 배를 DB에서 가져올지 (청킹으로 후보 증가 → 30배)
MIN_FETCH_COUNT = 500

# 폴더 가중치 제거 유지 (2026-04-21)
FOLDER_BONUS_SLIPBOX = 0.0
FOLDER_BONUS_PROJECT = 0.0

# ─── 모델 & DB 싱글턴 ───
_model = None
_table = None


def _get_model():
    global _model
    if _model is None:
        import torch
        torch.set_num_threads(1)
        torch.set_num_interop_threads(1)
        _model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
        _model.max_seq_length = 512
    return _model


def _get_table():
    global _table
    if _table is None:
        db = lancedb.connect(DB_PATH)
        _table = db.open_table(TABLE_NAME)
    return _table


def detect_query_bridge_keywords(query: str) -> set:
    """검색 쿼리에서 브릿지 키워드를 감지한다."""
    query_lower = query.lower()
    matched = set()
    for kw_name, signals in BRIDGE_KEYWORDS.items():
        for signal in signals:
            if signal.lower() in query_lower:
                matched.add(kw_name)
                break
    return matched


def calculate_score(row: dict, query_words: list[str],
                    query_bridge_kws: set) -> dict:
    """단일 청크의 최종 점수를 계산한다."""
    distance = row.get("_distance", 1.0)
    similarity = 1.0 / (1.0 + distance)

    filename_lower = row["filename"].lower()
    title_bonus = 0.0
    for word in query_words:
        if len(word) >= MIN_QUERY_WORD_LEN and word in filename_lower:
            title_bonus = TITLE_MATCH_BONUS
            break

    note_bridge_kws = set(row.get("bridge_keywords", "").split(",")) - {""}
    overlap_count = len(query_bridge_kws & note_bridge_kws)
    bridge_bonus = min(overlap_count * BRIDGE_KEYWORD_BONUS, BRIDGE_KEYWORD_MAX_BONUS)

    folder_weight = row.get("weight", 1.0)
    if folder_weight >= 3.0:
        folder_bonus = FOLDER_BONUS_SLIPBOX
    elif folder_weight >= 2.0:
        folder_bonus = FOLDER_BONUS_PROJECT
    else:
        folder_bonus = 0.0

    final_score = similarity + title_bonus + bridge_bonus + folder_bonus

    return {
        "filename": row["filename"],
        "path": row["path"],
        "chunk_id": row.get("chunk_id", row["path"]),
        "chunk_index": row.get("chunk_index", 0),
        "text": row["text"],
        "score": round(final_score, 4),
        "_detail": {
            "similarity": round(similarity, 4),
            "title_bonus": title_bonus,
            "bridge_bonus": bridge_bonus,
            "bridge_overlap": overlap_count,
            "folder_weight": folder_weight,
            "folder_bonus": folder_bonus,
        },
    }


def dedup_by_source(scored_chunks: list[dict], top_k: int) -> list[dict]:
    """source_path 기준으로 중복 제거. 파일당 최고 점수 청크 1개만 유지."""
    seen_paths = set()
    deduped = []
    for chunk in scored_chunks:
        if chunk["path"] in seen_paths:
            continue
        seen_paths.add(chunk["path"])
        deduped.append(chunk)
        if len(deduped) >= top_k:
            break
    return deduped


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    질문을 받아서 관련 노트를 찾아 반환한다.

    파이프라인:
    1. KURE-v1로 쿼리 임베딩
    2. LanceDB 벡터 검색 (top_k × 30 후보)
    3. 각 청크 점수 계산 (similarity + title_bonus + bridge_bonus)
    4. 점수 내림차순 정렬
    5. source_path로 dedup (파일당 최고 청크 1개)
    6. top_k 반환
    """
    try:
        model = _get_model()
        table = _get_table()
    except Exception as e:
        logger.error(f"DB/모델 로딩 실패: {e}")
        return []

    query_vector = model.encode(query).tolist()

    fetch_count = max(top_k * FETCH_MULTIPLIER, MIN_FETCH_COUNT)
    raw_results = (
        table.search(query_vector)
        .limit(fetch_count)
        .to_list()
    )

    query_bridge_kws = detect_query_bridge_keywords(query)
    query_words = query.lower().split()

    scored = [
        calculate_score(row, query_words, query_bridge_kws)
        for row in raw_results
    ]
    scored.sort(key=lambda x: x["score"], reverse=True)

    return dedup_by_source(scored, top_k)


if __name__ == "__main__":
    test_queries = [
        "내 업의 본질",
        "씬 전환 장소 단위 기억",
        "외모가 뛰어난 여자에게 외모 칭찬하지 않기",
    ]

    print("=" * 60)
    print("옵시디언 노트 검색 테스트 (Scenario B Phase 1)")
    print("=" * 60)

    for q in test_queries:
        print(f"\n🔍 질문: \"{q}\"")
        results = search(q, top_k=5)
        for i, r in enumerate(results, 1):
            d = r["_detail"]
            print(f"  {i}. [{r['score']:.4f}] {r['filename']} (chunk {r['chunk_index']})")
            print(f"     유사도={d['similarity']:.4f} 제목+{d['title_bonus']:.1f} 브릿지+{d['bridge_bonus']:.2f}")
            print(f"     경로: {r['path']}")
        print()
