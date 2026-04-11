"""
옵시디언 노트 검색기
- LanceDB 벡터 검색 (본문 의미 기반)
- 파일명/제목 키워드 매칭 보너스
- 브릿지 키워드 겹침 보너스
- PARA 폴더 가중치 (Slip-Box/P1E → 3배, Project → 2배)
"""

import logging
import os

import lancedb
from sentence_transformers import SentenceTransformer
from bridge_keywords import BRIDGE_KEYWORDS

logger = logging.getLogger(__name__)

# ─── 설정 ───
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "vault.lancedb"))
TABLE_NAME = "notes"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

# ─── 점수 가중치 ───
TITLE_MATCH_BONUS = 0.3
BRIDGE_KEYWORD_BONUS = 0.15
BRIDGE_KEYWORD_MAX_BONUS = 0.45
MIN_QUERY_WORD_LEN = 2  # 제목 매칭 시 최소 단어 길이
FETCH_MULTIPLIER = 10  # top_k의 몇 배를 DB에서 가져올지
MIN_FETCH_COUNT = 100  # 최소 fetch 수

# ─── 모델 & DB 싱글턴 (콜드스타트 최적화) ───
_model = None
_table = None


def _get_model():
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
    """단일 검색 결과의 최종 점수를 계산한다."""
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
    final_score = (similarity + title_bonus + bridge_bonus) * folder_weight

    return {
        "filename": row["filename"],
        "path": row["path"],
        "text": row["text"],
        "score": round(final_score, 4),
        "_detail": {
            "similarity": round(similarity, 4),
            "title_bonus": title_bonus,
            "bridge_bonus": bridge_bonus,
            "bridge_overlap": overlap_count,
            "folder_weight": folder_weight,
        },
    }


def search(query: str, top_k: int = 5) -> list[dict]:
    """
    질문을 받아서 관련 노트를 찾아 반환한다.

    최종 점수 = (벡터유사도 + 제목보너스 + 브릿지보너스) × 폴더가중치
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
    return scored[:top_k]


if __name__ == "__main__":
    test_queries = [
        "내 업의 본질",
        "자본주의와 비교우위",
        "습관을 만드는 방법",
    ]

    print("=" * 60)
    print("옵시디언 노트 검색 테스트")
    print(f"점수 = (유사도 + 제목보너스 + 브릿지보너스) × 폴더가중치")
    print("=" * 60)

    for q in test_queries:
        print(f"\n🔍 질문: \"{q}\"")
        q_kws = detect_query_bridge_keywords(q)
        if q_kws:
            print(f"   감지된 브릿지 키워드: {', '.join(q_kws)}")
        print("-" * 50)

        results = search(q, top_k=5)
        for i, r in enumerate(results, 1):
            d = r["_detail"]
            tags = []
            if d["folder_weight"] == 3.0:
                tags.append("⭐Slip-Box/P1E")
            elif d["folder_weight"] == 2.0:
                tags.append("📁Project")
            if d["title_bonus"] > 0:
                tags.append("📌제목매칭")
            if d["bridge_overlap"] > 0:
                tags.append(f"🔗브릿지×{d['bridge_overlap']}")
            tag_str = " ".join(tags)

            print(f"  {i}. [{r['score']:.4f}] {r['filename']}")
            print(f"     유사도={d['similarity']:.4f} "
                  f"제목+{d['title_bonus']:.1f} "
                  f"브릿지+{d['bridge_bonus']:.2f} "
                  f"×{d['folder_weight']:.0f}배  {tag_str}")
            print(f"     경로: {r['path']}")
        print()
