"""
옵시디언 노트 인덱서 (증분 인덱싱)
- 변경/추가된 노트만 업데이트, 삭제된 노트는 DB에서 제거
- --full 플래그로 전체 재인덱싱 가능
- PARA 폴더 구조에 따라 가중치 부여 (Slip-Box/P1E → 3배, Project → 2배)
- 브릿지 키워드 자동 감지하여 저장
"""

import os
import re
import sys
import time
import json
import logging
import lancedb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from bridge_keywords import BRIDGE_KEYWORDS

# ─── 로깅 설정 ───
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# ─── 설정 ───
VAULT_PATH = os.environ.get("VAULT_PATH", "/path/to/your/obsidian-vault")
DB_PATH = os.environ.get("DB_PATH", os.path.join(os.path.dirname(__file__), "vault.lancedb"))
TABLE_NAME = "notes"
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
STATE_FILE = os.environ.get("STATE_FILE", os.path.join(os.path.dirname(__file__), ".index_state.json"))

# ─── 상수 ───
MAX_NOTE_CHARS = 3000  # 노트 본문 최대 저장 길이
MIN_CLEAN_CHARS = 10  # 이 미만이면 인덱싱 스킵
EMBEDDING_BATCH_SIZE = 64
SKIP_DIRS = {".obsidian", ".trash", ".smart-env", "Attachments", ".git"}

# ─── PARA 폴더 가중치 ───
SLIP_BOX_WEIGHT = 3.0
PROJECT_WEIGHT = 2.0
DEFAULT_WEIGHT = 1.0


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


def process_note(vault_path: str, rel_path: str) -> dict | None:
    """노트 하나를 읽어서 인덱싱용 데이터 dict로 변환한다."""
    full_path = Path(vault_path) / rel_path
    try:
        text = full_path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as e:
        logger.warning(f"  파일 읽기 실패 ({rel_path}): {e}")
        return None

    if not text:
        return None

    clean = clean_markdown(text)
    if len(clean) < MIN_CLEAN_CHARS:
        return None

    filename = full_path.stem
    return {
        "filename": filename,
        "path": rel_path,
        "text": clean[:MAX_NOTE_CHARS],
        "weight": get_folder_weight(rel_path, filename),
        "bridge_keywords": detect_bridge_keywords(clean),
    }


def embed_notes(notes: list[dict]) -> list[dict]:
    """노트 리스트에 벡터를 추가하여 반환한다 (원본 변경 없음)."""
    logger.info(f"임베딩 모델 로딩 중: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    logger.info(f"{len(notes)}개 노트 임베딩 중...")
    texts = [n["text"] for n in notes]
    vectors = model.encode(texts, show_progress_bar=True, batch_size=EMBEDDING_BATCH_SIZE)

    return [{**note, "vector": vectors[i].tolist()} for i, note in enumerate(notes)]


def print_stats(notes: list[dict], label: str = "완료"):
    """인덱싱 결과 통계를 출력한다."""
    total = len(notes)
    w3 = sum(1 for n in notes if n["weight"] == SLIP_BOX_WEIGHT)
    w2 = sum(1 for n in notes if n["weight"] == PROJECT_WEIGHT)
    w1 = total - w3 - w2
    has_bridge = sum(1 for n in notes if n.get("bridge_keywords"))
    logger.info(f"{label}! {total}개 노트")
    logger.info(f"  → 폴더 가중치: Slip-Box/P1E(3배)={w3}개, Project(2배)={w2}개, 기타(1배)={w1}개")
    logger.info(f"  → 브릿지 키워드 감지: {has_bridge}개")


def safe_delete(table, path: str):
    """LanceDB 테이블에서 경로 기반으로 레코드를 삭제한다."""
    safe_path = path.replace(chr(34), "")
    table.delete(f'path = "{safe_path}"')


def full_reindex(vault_path: str, current_files: dict[str, float]):
    """전체 재인덱싱: 기존 테이블 삭제 후 새로 생성한다."""
    logger.info("[ 전체 재인덱싱 모드 ]")
    notes = []
    for rel_path in current_files:
        note = process_note(vault_path, rel_path)
        if note:
            notes.append(note)

    logger.info(f"  → {len(notes)}개 노트 발견")
    if not notes:
        logger.warning("노트를 찾지 못했습니다.")
        return

    data = embed_notes(notes)

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
        logger.info(f"  → {len(deleted)}개 노트 DB에서 제거 완료")

    if to_process:
        notes = [n for rel in to_process if (n := process_note(vault_path, rel))]
        if notes:
            for note in notes:
                safe_delete(table, note["path"])

            data = embed_notes(notes)
            table.add(data)
            logger.info(f"  → {len(data)}개 노트 임베딩 완료")

    all_data = table.to_pandas()
    print_stats(
        [{"weight": w, "bridge_keywords": bk} for w, bk in zip(all_data["weight"], all_data["bridge_keywords"])],
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
        added, modified, deleted = compute_changes(current_files, previous_state)
        incremental_index(VAULT_PATH, current_files, added, modified, deleted)

    elapsed = time.time() - start
    logger.info(f"\n총 소요 시간: {elapsed:.1f}초")
