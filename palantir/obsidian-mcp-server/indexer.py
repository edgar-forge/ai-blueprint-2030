"""
옵시디언 노트 인덱서 (증분 인덱싱 + 헤더 기반 청킹)
- 대형 파일 tail 유실 방지: 마크다운 헤더 기반 청킹
- 변경/추가된 노트만 업데이트, 삭제된 노트는 DB에서 제거
- --full 플래그로 전체 재인덱싱 가능
- PARA 폴더 구조에 따라 가중치 부여 (Slip-Box/P1E → 3배, Project → 2배)
- 브릿지 키워드 자동 감지하여 저장 (청크 단위)
"""

import os

# ─── CPU 4 thread 강제 (Phase 1 인덱싱 전용) ───
# torch.set_num_threads만으론 macOS에서 무시됨. 환경변수로 먼저 강제해야 함.
# 반드시 import torch / sentence_transformers 이전에 설정해야 적용.
os.environ["OMP_NUM_THREADS"] = "4"
os.environ["MKL_NUM_THREADS"] = "4"
os.environ["OPENBLAS_NUM_THREADS"] = "4"
os.environ["VECLIB_MAXIMUM_THREADS"] = "4"
os.environ["NUMEXPR_NUM_THREADS"] = "4"
os.environ["TOKENIZERS_PARALLELISM"] = "true"

import re
import sys
import time
import json
import logging
import lancedb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from bridge_keywords import BRIDGE_KEYWORDS

# ─── 로깅 설정 ───
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ─── 설정 ───
VAULT_PATH = "/Users/edger-choi/Documents/Obsidian Vault"
DB_PATH = os.path.expanduser("~/obsidian-mcp-server/vault.lancedb")
TABLE_NAME = "notes"
EMBEDDING_MODEL = "nlpai-lab/KURE-v1"  # 2026-04-21 교체. 1024D, 8192 토큰, MTEB-ko NDCG@5 0.6748 (1위)
STATE_FILE = os.path.expanduser("~/obsidian-mcp-server/.index_state.json")

# ─── 청킹 설정 (2026-04-22 Scenario B) ───
CHUNK_SIZE = 800  # 청크 목표 크기 (자)
CHUNK_OVERLAP = 100  # 청크 간 겹침 (자)
LARGE_SECTION_THRESHOLD = 1200  # 헤더 섹션이 이 크기 초과 시 재분할
MIN_CHUNK_SIZE = 200  # 이 미만 청크는 이웃과 병합
SINGLE_CHUNK_THRESHOLD = 800  # 이 이하 파일은 단일 청크 유지

# ─── 상수 ───
MIN_CLEAN_CHARS = 10  # 이 미만이면 인덱싱 스킵
EMBEDDING_BATCH_SIZE = 32  # 4-thread + 16GB RAM 환경: 더 큰 배치로 throughput 확보
MAX_SEQ_LENGTH = 512  # KURE-v1 기본. 발열은 CPU 1 thread로 제어
SKIP_DIRS = {".obsidian", ".trash", ".smart-env", "Attachments", ".git"}

# ─── PARA 폴더 가중치 ───
SLIP_BOX_WEIGHT = 3.0
PROJECT_WEIGHT = 2.0
DEFAULT_WEIGHT = 1.0

# ─── 청킹 인스턴스 (싱글턴) ───
HEADERS_TO_SPLIT = [("#", "H1"), ("##", "H2"), ("###", "H3")]
_md_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=HEADERS_TO_SPLIT,
    strip_headers=False,
)
_char_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", "? ", "! ", " ", ""],
)


def get_folder_weight(rel_path: str, filename: str) -> float:
    """PARA 폴더 기준으로 노트 가중치를 반환한다."""
    if rel_path.startswith("0. Slip-Box/") or "P1E" in filename:
        return SLIP_BOX_WEIGHT
    if rel_path.startswith("1. Project/"):
        return PROJECT_WEIGHT
    return DEFAULT_WEIGHT


def detect_bridge_keywords(text: str) -> str:
    """본문에서 브릿지 키워드를 감지하여 쉼표 구분 문자열로 반환한다."""
    text_lower = text.lower()
    matched = []
    for kw_name, signals in BRIDGE_KEYWORDS.items():
        for signal in signals:
            if signal.lower() in text_lower:
                matched.append(kw_name)
                break
    return ",".join(matched)


def clean_markdown(text: str) -> str:
    """마크다운에서 프론트매터, 이미지, 링크 구문 등을 제거한다."""
    text = re.sub(r"^---\n.*?\n---\n?", "", text, flags=re.DOTALL)
    text = re.sub(r"!\[\[.*?\]\]", "", text)
    text = re.sub(r"\[\[([^|\]]*\|)?([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str) -> list[str]:
    """마크다운 텍스트를 청크로 분할한다.

    전략:
    1. 800자 이하 파일 → 단일 청크 (대부분 노트)
    2. 헤더(H1/H2/H3)로 먼저 분할
    3. 헤더 섹션이 1200자 초과 → 재귀적 문자 분할 (800/100)
    4. 200자 미만 청크 → 이웃과 병합
    5. 헤더 없는 파일 → 바로 문자 분할
    """
    if len(text) <= SINGLE_CHUNK_THRESHOLD:
        return [text]

    try:
        header_docs = _md_splitter.split_text(text)
    except Exception as e:
        logger.warning(f"  헤더 분할 실패, 문자 분할로 fallback: {e}")
        header_docs = []

    if not header_docs:
        return _char_splitter.split_text(text)

    chunks = []
    for doc in header_docs:
        content = doc.page_content
        if len(content) <= LARGE_SECTION_THRESHOLD:
            chunks.append(content)
        else:
            sub_chunks = _char_splitter.split_text(content)
            chunks.extend(sub_chunks)

    # 작은 청크 병합
    merged = []
    buffer = ""
    for c in chunks:
        if not c.strip():
            continue
        if buffer and len(buffer) + len(c) < MIN_CHUNK_SIZE * 2:
            buffer = (buffer + "\n\n" + c).strip()
        else:
            if buffer:
                merged.append(buffer)
            buffer = c
    if buffer:
        merged.append(buffer)

    return merged if merged else [text]


def scan_vault(vault_path: str) -> dict[str, float]:
    """볼트의 모든 .md 파일과 수정시간(mtime)을 반환한다."""
    vault = Path(vault_path)
    files = {}
    for md_file in vault.rglob("*.md"):
        if any(part in SKIP_DIRS for part in md_file.parts):
            continue
        rel_path = str(md_file.relative_to(vault))
        files[rel_path] = md_file.stat().st_mtime
    return files


def load_state() -> dict[str, float]:
    """이전 인덱싱 시점의 mtime 상태를 불러온다."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state: dict[str, float]):
    """현재 파일 mtime 상태를 저장한다."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


def compute_changes(current: dict[str, float], previous: dict[str, float]):
    """현재와 이전 상태를 비교하여 추가/수정/삭제 목록을 반환한다."""
    added = [p for p in current if p not in previous]
    modified = [p for p in current if p in previous and current[p] > previous[p]]
    deleted = [p for p in previous if p not in current]
    return added, modified, deleted


def validate_scan_sanity(current_files: dict, previous_state: dict) -> None:
    """볼트 스캔 결과의 sanity check. 2026-04-22 장애로 추가된 방어 코드.

    시나리오: launchd 환경에서 rglob가 빈 iterator를 반환한 적 있음 (원인 불명).
    이때 인덱서가 '모든 파일이 삭제됐다'로 해석해 전체 DB를 비워버렸음.

    방어책:
    - 이전 state가 10개 이상인데 현재 스캔이 0개면 → 거의 100% 스캔 이상
    - 이전 state가 100개 이상인데 현재 스캔이 90% 이상 감소면 → 의심
    - 실제로 대량 삭제가 필요하면 `--full` 플래그로 명시적으로 실행
    """
    prev_count = len(previous_state)
    curr_count = len(current_files)

    if prev_count >= 10 and curr_count == 0:
        raise RuntimeError(
            f"⚠️ 스캔 결과 0개 파일 (이전 {prev_count}개 기록). "
            f"파일시스템 접근 이상 의심. 데이터 보호를 위해 인덱싱 중단. "
            f"실제 전체 삭제가 맞으면 indexer.py --full 로 재실행."
        )

    if prev_count >= 100 and curr_count < prev_count * 0.1:
        raise RuntimeError(
            f"⚠️ 스캔 파일 {prev_count} → {curr_count}로 90% 이상 감소. "
            f"비정상 감소로 판단. 데이터 보호를 위해 인덱싱 중단. "
            f"실제 대량 삭제가 맞으면 indexer.py --full 로 재실행."
        )


def process_note(vault_path: str, rel_path: str) -> list[dict]:
    """노트 하나를 읽어서 인덱싱용 청크 dict 리스트로 변환한다."""
    full_path = Path(vault_path) / rel_path
    try:
        text = full_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"  파일 읽기 실패 ({rel_path}): {e}")
        return []

    if not text:
        return []

    clean = clean_markdown(text)
    if len(clean) < MIN_CLEAN_CHARS:
        return []

    filename = full_path.stem
    weight = get_folder_weight(rel_path, filename)
    chunks = chunk_text(clean)

    result = []
    for i, chunk_content in enumerate(chunks):
        chunk_content = chunk_content.strip()
        if len(chunk_content) < MIN_CLEAN_CHARS:
            continue
        result.append({
            "chunk_id": f"{rel_path}::{i}",
            "chunk_index": i,
            "filename": filename,
            "path": rel_path,  # 소스 파일 경로 (기존 호환성 유지)
            "text": chunk_content,
            "weight": weight,
            "bridge_keywords": detect_bridge_keywords(chunk_content),
        })
    return result


def embed_notes(notes: list[dict]) -> list[dict]:
    """노트 리스트에 벡터를 추가하여 반환한다 (원본 변경 없음)."""
    logger.info(f"임베딩 모델 로딩 중: {EMBEDDING_MODEL}")
    import torch
    # Phase 1 인덱싱 전용: CPU 4 thread (집 환경, 다른 작업 안 할 때).
    # 검색(search_phase1.py)은 1 thread 유지 (발열 최소화). 인덱싱만 4 thread로 속도 확보.
    # 예상 시간: 24k청크 @ 4 thread ≈ 10~15분 (1 thread 40~60분 대비 3~4배 빠름)
    torch.set_num_threads(4)
    torch.set_num_interop_threads(2)
    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    model.max_seq_length = MAX_SEQ_LENGTH

    logger.info(f"{len(notes)}개 청크 임베딩 중...")
    texts = [n["text"] for n in notes]
    vectors = model.encode(texts, show_progress_bar=True, batch_size=EMBEDDING_BATCH_SIZE)

    return [{**note, "vector": vectors[i].tolist()} for i, note in enumerate(notes)]


def print_stats(chunks: list[dict], label: str = "완료"):
    """인덱싱 결과 통계를 출력한다."""
    total_chunks = len(chunks)
    unique_files = len(set(c["path"] for c in chunks))
    w3 = sum(1 for c in chunks if c["weight"] == SLIP_BOX_WEIGHT)
    w2 = sum(1 for c in chunks if c["weight"] == PROJECT_WEIGHT)
    w1 = total_chunks - w3 - w2
    has_bridge = sum(1 for c in chunks if c.get("bridge_keywords"))
    logger.info(f"{label}!")
    logger.info(f"  → 총 청크 {total_chunks}개 (원본 파일 {unique_files}개)")
    logger.info(f"  → 폴더 가중치: Slip-Box/P1E(3배)={w3} / Project(2배)={w2} / 기타(1배)={w1}")
    logger.info(f"  → 브릿지 키워드 감지: {has_bridge}개 청크")


def safe_delete(table, path: str):
    """LanceDB 테이블에서 소스 경로 기반으로 레코드를 삭제한다 (모든 청크)."""
    safe_path = path.replace(chr(34), "")
    table.delete(f'path = "{safe_path}"')


def full_reindex(vault_path: str, current_files: dict[str, float]):
    """전체 재인덱싱: 기존 테이블 삭제 후 새로 생성한다."""
    logger.info("[ 전체 재인덱싱 모드 — 청킹 활성화 ]")
    all_chunks = []
    for rel_path in current_files:
        chunks = process_note(vault_path, rel_path)
        all_chunks.extend(chunks)

    unique_files = len(set(c["path"] for c in all_chunks))
    logger.info(f"  → {unique_files}개 파일 → {len(all_chunks)}개 청크")
    if not all_chunks:
        logger.warning("청크를 생성하지 못했습니다.")
        return

    data = embed_notes(all_chunks)

    db = lancedb.connect(DB_PATH)
    existing = db.list_tables()
    table_names = existing.tables if hasattr(existing, "tables") else list(existing)
    if TABLE_NAME in table_names:
        db.drop_table(TABLE_NAME)

    db.create_table(TABLE_NAME, data=data)
    logger.info(f"  → DB 위치: {DB_PATH}")
    print_stats(data)
    save_state(current_files)


def incremental_index(vault_path: str, current_files: dict[str, float],
                      added: list, modified: list, deleted: list):
    """증분 인덱싱: 변경된 노트만 업데이트한다."""
    logger.info("[ 증분 인덱싱 모드 ]")
    logger.info(f"  → 추가: {len(added)}개 / 수정: {len(modified)}개 / 삭제: {len(deleted)}개")

    to_process = added + modified
    if not to_process and not deleted:
        logger.info("  → 변경 사항 없음. 스킵.")
        return

    db = lancedb.connect(DB_PATH)
    table = db.open_table(TABLE_NAME)

    if deleted:
        for path in deleted:
            safe_delete(table, path)
        logger.info(f"  → {len(deleted)}개 파일의 모든 청크 제거 완료")

    if to_process:
        all_chunks = []
        for rel in to_process:
            chunks = process_note(vault_path, rel)
            all_chunks.extend(chunks)

        if all_chunks:
            processed_paths = set(c["path"] for c in all_chunks)
            for p in processed_paths:
                safe_delete(table, p)

            data = embed_notes(all_chunks)
            table.add(data)
            logger.info(f"  → {len(data)}개 청크 임베딩 완료 (원본 {len(processed_paths)}개 파일)")

    all_data = table.to_pandas()
    print_stats(
        [{"weight": w, "bridge_keywords": bk, "path": p}
         for w, bk, p in zip(all_data["weight"], all_data["bridge_keywords"], all_data["path"])],
        label="현재 DB 상태",
    )
    save_state(current_files)


def determine_index_mode(force_full: bool, previous_state: dict) -> bool:
    """전체 재인덱싱이 필요한지 판단한다."""
    if force_full:
        logger.info("  → --full 플래그 감지. 전체 재인덱싱 실행.")
        return True

    if not previous_state:
        logger.info("  → 첫 실행. 전체 재인덱싱 실행.")
        return True

    db = lancedb.connect(DB_PATH)
    existing = db.list_tables()
    table_names = existing.tables if hasattr(existing, "tables") else list(existing)
    if TABLE_NAME not in table_names:
        logger.info("  → DB 테이블 없음. 전체 재인덱싱 실행.")
        return True

    # 스키마 확인 (chunk_id 컬럼 있는지)
    try:
        tbl = db.open_table(TABLE_NAME)
        schema_names = [f.name for f in tbl.schema]
        if "chunk_id" not in schema_names:
            logger.info("  → 구 스키마 감지 (chunk_id 없음). 전체 재인덱싱 필요.")
            return True
    except Exception as e:
        logger.info(f"  → 스키마 확인 실패 ({e}). 전체 재인덱싱 실행.")
        return True

    return False


if __name__ == "__main__":
    start = time.time()
    is_force_full = "--full" in sys.argv

    logger.info(f"볼트 경로: {VAULT_PATH}")
    logger.info("볼트 스캔 중...")
    current_files = scan_vault(VAULT_PATH)
    logger.info(f"  → {len(current_files)}개 .md 파일 발견")

    previous_state = load_state()

    if determine_index_mode(is_force_full, previous_state):
        full_reindex(VAULT_PATH, current_files)
    else:
        # 증분 인덱싱 전 sanity check (2026-04-22 장애 재발 방지)
        validate_scan_sanity(current_files, previous_state)
        added, modified, deleted = compute_changes(current_files, previous_state)
        incremental_index(VAULT_PATH, current_files, added, modified, deleted)

    elapsed = time.time() - start
    logger.info(f"\n총 소요 시간: {elapsed:.1f}초")
