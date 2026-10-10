"""
옵시디언 노트 검색기 (Scenario B Phase 1 — 청킹 적용, 벡터 단독)
- LanceDB 벡터 검색 (본문 의미 기반) — 청크 단위
- source_path 기준 dedup (파일당 최고 점수 청크 1개)
- 파일명 글자겹침 저울 (2026-08-20: 옛 0.5 고정 보너스 스위치를 대체)
- 브릿지 키워드 겹침 보너스
- 4. Archives 경로 감점 / 0. Slip-Box/개념 가산

최종 점수 = similarity + title_bonus + bridge_bonus + folder_bonus

2026-08-20 재조정 — 정답세트 20줄 1위 5→10, 홀드아웃 20줄 1위 3→8.
상태 허브가 상태 문장 검색에서 상위5에 드는 비율 2/6 → 6/6 (전부 1위).
백업 = search.py.bak_20260820
"""

import logging
import os
import re
import unicodedata as ud

import lancedb
from sentence_transformers import SentenceTransformer
from bridge_keywords import BRIDGE_KEYWORDS

logger = logging.getLogger(__name__)

# ─── 설정 ───
DB_PATH = os.path.expanduser("~/obsidian-mcp-server/vault.lancedb")
TABLE_NAME = "notes"
EMBEDDING_MODEL = "nlpai-lab/KURE-v1"  # 1024D, 8192 토큰, MTEB-ko NDCG@5 0.6748 (1위)

# ─── 점수 가중치 (2026-08-20 재조정) ───
# 옛 TITLE_MATCH_BONUS=0.5 스위치 폐기 → 글자겹침 저울 LEX_TITLE_WEIGHT 로 교체.
# 닮은정도(1/(1+거리))가 후보 500개에서 폭 0.05~0.15 안에만 분포하는데
# 보너스가 0.5/0.45 라 저울이 아니라 스위치로 작동하고 있었다.
LEX_TITLE_WEIGHT = 0.15          # 제목 글자겹침 저울의 최대 몫 (평지 0.10~0.20)
# 브릿지 보너스 0 (2026-08-20 2차). 0.03 으로 낮춰 남겼더니 절단 실험에서
# 오히려 점수를 깎고 있었다 — 빼니까 정답세트 1위 10 → 12. 코드는 남겨둔다.
BRIDGE_KEYWORD_BONUS = 0.0
BRIDGE_KEYWORD_MAX_BONUS = 0.0
LEX_QUERY_MAX_CHARS = 300        # 계산량 상한 (긴 질의 방어)

# ─── Fetch 설정 (청크 기반, 더 넓게 확보 후 dedup) ───
FETCH_MULTIPLIER = 30  # top_k의 몇 배를 DB에서 가져올지 (청킹으로 후보 증가 → 30배)
MIN_FETCH_COUNT = 500

# 폴더 가중치 제거 유지 + Archives 감점 (2026-07-27 상태 정답세트 벤치마크로 확정)
FOLDER_BONUS_SLIPBOX = 0.0
FOLDER_BONUS_PROJECT = 0.0
ARCHIVE_PENALTY = 0.5
CONCEPT_BONUS = 0.05        # 0. Slip-Box/개념/ 가산점 (2026-08-18 신설, 8/20 유지)
# 0.12~0.15 로 올리면 정답세트 성적은 오르지만(10→15) 상태 허브가 개념 밑으로 밀리고
# (허브 1위 6/6 → 5/6·평균 2.4위) 개념이 답이 아닌 검색 15개 중 6개에서 개념이 1위를
# 뺏는다. 눈금 40줄이 전부 개념 정답이라 이 다이얼은 구조적으로 "더 올려라"만 말한다.
CONCEPT_DIR_MARK = "0. Slip-Box/개념/"

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


_LEX_CLEAN = re.compile(r"[^0-9a-z가-힣]")
# 개념 파일명의 「— 개념」 꼬리. 저울을 재기 전에 뗀다 (2026-08-20 2차).
# 안 떼면 질의에 "개념" 두 글자만 있어도 개념 파일 39개가 전부 저울을 받고,
# 이름이 짧은 파일일수록 꼬리가 분모를 키워 불리해진다. 떼니까 정답세트 1위 10 → 13.
_LEX_TAIL = re.compile(r"\s*—\s*개념$")
_lex_cache: dict = {}
_lex_cache_query = None
_lex_query_norm = ""


def _longest_common_substring(a: str, b: str) -> int:
    """두 문자열이 통으로 겹치는 가장 긴 토막의 길이."""
    prev = [0] * (len(b) + 1)
    best = 0
    for i in range(len(a)):
        cur = [0] * (len(b) + 1)
        ai = a[i]
        for j in range(len(b)):
            if ai == b[j]:
                v = prev[j] + 1
                cur[j + 1] = v
                if v > best:
                    best = v
        prev = cur
    return best


def lexical_title_score(filename: str, query: str) -> float:
    """파일명이 질의로 얼마나 설명되나. 0.0 ~ 1.0

    파일명 알맹이 글자수 대비, 질의와 통으로 겹치는 가장 긴 토막의 비율.
    형태소 분석기 없이 교착어(「도망치」↔「도망쳐서」)를 잡는 가장 싼 방법이다.
    캐시는 질의 하나 동안만 산다 (질의가 바뀌면 통째로 비운다).
    """
    global _lex_cache, _lex_cache_query, _lex_query_norm
    if _lex_cache_query != query:
        _lex_cache_query = query
        _lex_cache = {}
        _lex_query_norm = _LEX_CLEAN.sub(
            "", ud.normalize("NFC", query).lower())[:LEX_QUERY_MAX_CHARS]

    hit = _lex_cache.get(filename)
    if hit is not None:
        return hit

    name = _LEX_TAIL.sub("", ud.normalize("NFC", filename))
    name = _LEX_CLEAN.sub("", name.lower())
    if len(name) < 2 or len(_lex_query_norm) < 2:
        _lex_cache[filename] = 0.0
        return 0.0
    best = _longest_common_substring(name, _lex_query_norm)
    score = min(best / len(name), 1.0) if best >= 2 else 0.0
    _lex_cache[filename] = score
    return score


def calculate_score(row: dict, query: str,
                    query_bridge_kws: set) -> dict:
    """단일 청크의 최종 점수를 계산한다."""
    distance = row.get("_distance", 1.0)
    similarity = 1.0 / (1.0 + distance)

    title_bonus = LEX_TITLE_WEIGHT * lexical_title_score(row["filename"], query)

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
    path_nfc = ud.normalize("NFC", row.get("path", ""))
    if "4. Archives" in path_nfc:
        folder_bonus -= ARCHIVE_PENALTY
    # 「_」로 시작하는 색인 파일(_개념 지도)은 어떤 질의의 답도 아니므로 제외한다
    if CONCEPT_DIR_MARK in path_nfc and not row["filename"].startswith("_"):
        folder_bonus += CONCEPT_BONUS

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
            "title_bonus": round(title_bonus, 4),
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
    3. 각 청크 점수 계산 (similarity + title_bonus + bridge_bonus + folder_bonus)
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

    scored = [
        calculate_score(row, query, query_bridge_kws)
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
            print(f"     유사도={d['similarity']:.4f} 제목+{d['title_bonus']:.3f} 브릿지+{d['bridge_bonus']:.2f}")
            print(f"     경로: {r['path']}")
        print()
